"""
Thermodynamic calculator module.

Provides the core calculation engine using CoolProp, independent of UI.
"""

from typing import Optional, Tuple, List
import logging
import math

from natural_gas_main.config.settings import config
from natural_gas_main.core.exceptions import (
    BackendNotAvailableError,
    StateUpdateError,
    HeatingValueError,
    CalculationConvergenceError,
    ThermoCalculationError,
)
from natural_gas_main.models.gas_data import GasMixture
from natural_gas_main.models.calculation_result import (
    CalculationResult,
    ActualConditionResults,
    StandardConditionResults,
    HeatingValues,
    VolumeConversion,
    PhaseEnvelopeData,
    ZFactorComparison,
    HydrateResults
)
from natural_gas_main.models.heating_value_db import get_reference_heating_values
from natural_gas_main.models.z_factor import StandingKatzZFactor
from natural_gas_main.models.aga8_calculator import calculate_aga8, PYAGA8_AVAILABLE, AGA8_MAPPING
from natural_gas_main.models.iso6976 import calculate_iso6976_heating_values, is_iso6976_compatible
from natural_gas_main.models.neqsim_calculator import (
    calculate_neqsim,
    NEQSIM_AVAILABLE,
    NEQSIM_AVAILABLE_BACKENDS,
    NEQSIM_EOS_REGISTRY,
    get_neqsim_iso6976,
    get_neqsim_hydrate_temperature,
)

CP = None
COOLPROP_AVAILABLE = False

try:
    import CoolProp.CoolProp as CP
    COOLPROP_AVAILABLE = True
    CP.set_debug_level(0)
    logging.info("CoolProp başarıyla yüklendi")
except ImportError as e:
    logging.error(f"CoolProp içe aktarılamadı: {e}")
    CP = None


class ThermoCalculator:
    """
    Thermodynamic properties calculator.
    
    Handles all thermodynamic calculations using CoolProp library.
    Provides fallback mechanisms for different backends.
    """
    
    def __init__(self):
        """
        Initialize calculator.
        
        Raises:
            BackendNotAvailableError: If neither CoolProp nor NeqSim is installed
        """
        if not COOLPROP_AVAILABLE and not NEQSIM_AVAILABLE:
            raise BackendNotAvailableError("CoolProp veya NeqSim")
        
        self.logger = logging.getLogger(__name__)
        self.z_factor_estimator = StandingKatzZFactor(CP if COOLPROP_AVAILABLE else None)

    @staticmethod
    def _air_density(pressure_pa: float, temperature_k: float) -> float:
        """Calculate air density using CoolProp with ideal gas law fallback."""
        try:
            return CP.PropsSI('D', 'T', temperature_k, 'P', pressure_pa, 'Air')
        except Exception:
            return pressure_pa / (287.058 * temperature_k)
        
    def calculate_properties(
        self,
        mixture: GasMixture,
        temperature_k: float,
        pressure_pa: float,
        backend: str = "HEOS",
        volume_m3: Optional[float] = None,
        standard_T: float = config.T_STANDARD,
        standard_P: float = config.P_STANDARD,
        standard_name: Optional[str] = None
    ) -> CalculationResult:
        """
        Calculate thermodynamic properties for gas mixture.
        
        Args:
            mixture: Gas mixture definition
            temperature_k: Temperature in Kelvin
            pressure_pa: Pressure in Pascals
            backend: CoolProp backend (HEOS, SRK, PR)
            volume_m3: Optional volume in cubic meters for conversion
            standard_T: Reference standard temperature (K)
            standard_P: Reference standard pressure (Pa)
            standard_name: Optional name of the standard used
            
        Returns:
            Complete calculation results
            
        Raises:
            StateUpdateError: If state update fails
            Various exceptions from validation
        """
        # Validate mixture total
        mixture.validate_total()
        
        # Get backend to use
        backend = self._select_backend(mixture, backend)
        
        try:
            # Calculate properties
            result = self._calculate_with_backend(
                mixture,
                temperature_k,
                pressure_pa,
                volume_m3,
                backend,
                standard_T,
                standard_P,
                standard_name
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Calculation failed with {backend}: {e}")
            raise
    
    def calculate_with_fallback(
        self,
        mixture: GasMixture,
        temperature_k: float,
        pressure_pa: float,
        preferred_backend: str = "HEOS",
        volume_m3: Optional[float] = None,
        standard_T: float = config.T_STANDARD,
        standard_P: float = config.P_STANDARD,
        standard_name: Optional[str] = None
    ) -> Tuple[CalculationResult, str]:
        """
        Calculate with automatic backend fallback.

        Tries backends in order: [preferred, SRK, PR]
        HEOS is skipped if mixture is incompatible.

        Args:
            mixture: Gas mixture
            temperature_k: Temperature (K)
            pressure_pa: Pressure (Pa)
            preferred_backend: Preferred backend to try first
            volume_m3: Optional volume (m³)
            standard_T: Reference standard temperature (K)
            standard_P: Reference standard pressure (Pa)
            
        Returns:
            Tuple of (result, backend_used) or (None, "")
        """
        # Validate total fractions
        mixture.validate_total()
        # Determine backend order
        backends = self._get_backend_order(mixture, preferred_backend)
        
        result = None
        used_backend = ""
        
        for backend in backends:
            try:
                self.logger.info(f"Trying backend: {backend}")
                result = self._calculate_with_backend(
                    mixture,
                    temperature_k,
                    pressure_pa,
                    volume_m3,
                    backend,
                    standard_T,
                    standard_P,
                    standard_name
                )
                used_backend = backend
                result.z_factor_comparison = self._calculate_z_factor_comparison(
                    mixture,
                    temperature_k,
                    pressure_pa,
                    main_actual=result.actual,
                    main_backend=backend,
                )
                self.logger.info(f"Successfully calculated with {backend}")
                break
                
            except (StateUpdateError, ThermoCalculationError, ValueError, RuntimeError) as e:
                self.logger.warning(f"Backend {backend} failed: {e}")
                continue
        if result is None:
            result = self._calculate_z_only_fallback(
                mixture,
                temperature_k,
                pressure_pa,
                volume_m3,
                standard_T,
                standard_P,
                standard_name
            )
            if result is not None:
                used_backend = "Standing-Katz ANN10"
            else:
                raise ThermoCalculationError(
                    "Hesaplama tüm yöntemlerle (HEOS, SRK, PR, AGA8, ANN10) tamamlanamadı."
                )

        return result, used_backend
    
    def _select_backend(self, mixture: GasMixture, requested_backend: str) -> str:
        """
        Select appropriate backend based on mixture compatibility.
        
        Args:
            mixture: Gas mixture to check
            requested_backend: Backend requested
            
        Returns:
            Backend name to use
        """
        if requested_backend == "HEOS":
            incompatible = mixture.check_heos_compatibility()
            if incompatible:
                self.logger.warning(
                    f"HEOS incompatible gases: {incompatible}. "
                    "Consider using SRK or PR."
                )

        if self._is_neqsim_backend(requested_backend):
            if not NEQSIM_AVAILABLE:
                self.logger.warning(
                    f"NeqSim backend '{requested_backend}' is not available "
                    "(neqsim package not installed). Falling back."
                )

        return requested_backend
    
    @staticmethod
    def _is_neqsim_backend(backend: str) -> bool:
        """Check if a backend name is a NeqSim EOS."""
        return backend.startswith("neqsim-")

    @staticmethod
    def _has_non_aga8_components(mixture: GasMixture) -> bool:
        """Check if mixture contains components not supported by AGA8 standard."""
        for gas in mixture.components:
            coolprop_name = GasMixture._format_gas_name_for_coolprop(gas.name).lower()
            if coolprop_name not in AGA8_MAPPING:
                return True
        return False

    def _get_backend_order(self, mixture: GasMixture, preferred: str) -> List[str]:
        """
        Get prioritized list of backends to try.
        
        Args:
            mixture: Gas mixture
            preferred: Preferred backend
            
        Returns:
            Ordered list of backend names
        """
        backends = []
        
        # Add preferred backend if available
        if self._is_neqsim_backend(preferred):
            if NEQSIM_AVAILABLE:
                backends.append(preferred)
        elif preferred in ("GERG-2008", "AGA8-Detail"):
            if PYAGA8_AVAILABLE:
                backends.append(preferred)
        else: # CoolProp backend (HEOS, SRK, PR)
            if COOLPROP_AVAILABLE:
                backends.append(preferred)
                
        # Define fallbacks in priority order
        # We start with NeqSim backends if NeqSim is available
        fallbacks = []
        if NEQSIM_AVAILABLE:
            # Add NeqSim default fallback first
            fallbacks.append("neqsim-gerg2008")
            # Add other NeqSim backends for fallback
            for b in NEQSIM_AVAILABLE_BACKENDS:
                if b not in fallbacks:
                    fallbacks.append(b)
                    
        # Add legacy/native backends if available
        if PYAGA8_AVAILABLE and not self._has_non_aga8_components(mixture):
            fallbacks.extend(["GERG-2008", "AGA8-Detail"])
            
        if COOLPROP_AVAILABLE:
            if not mixture.check_heos_compatibility():
                fallbacks.append("HEOS")
            fallbacks.extend(["SRK", "PR"])
            
        # Merge backends while keeping priority order
        for fb in fallbacks:
            if fb not in backends:
                backends.append(fb)
                
        return backends

    def _calculate_z_factor_comparison(
        self,
        mixture: GasMixture,
        temperature_k: float,
        pressure_pa: float,
        main_actual: Optional[ActualConditionResults] = None,
        main_backend: Optional[str] = None,
    ) -> List[ZFactorComparison]:
        """Return comprehensive Z-factor comparisons across all backends.

        Args:
            mixture: Gas mixture to evaluate.
            temperature_k: Temperature in Kelvin.
            pressure_pa: Pressure in Pascals.
            main_actual: ActualConditionResults from the primary calculation.
                          When provided the corresponding backend is not
                          recomputed.
            main_backend: Backend name that produced *main_actual*.

        Returns:
            List of ZFactorComparison entries for display.
        """
        comparisons = []

        # 1. Standing-Katz and DAK
        try:
            estimates = self.z_factor_estimator.estimates(mixture, temperature_k, pressure_pa)
            for est in estimates:
                comparisons.append(ZFactorComparison(
                    method=est.method,
                    z_factor=est.z_factor,
                    ppr=est.ppr,
                    tpr=est.tpr,
                    valid=est.valid,
                    warning=est.warning
                ))
        except Exception as e:
            self.logger.info(f"Standing-Katz/DAK Z comparison unavailable: {e}")

        # Helper to get pseudo criticals for valid flag
        try:
            pseudo = self.z_factor_estimator.pseudo_critical(mixture)
            ppr = pressure_pa / pseudo.pc_pa
            tpr = temperature_k / pseudo.tc_k
        except (ValueError, ZeroDivisionError, AttributeError):
            ppr, tpr = float('nan'), float('nan')
            self.logger.debug("Pseudo-critical properties could not be calculated")

        # 2. Add GERG-2008 & AGA8-Detail
        for method in ["GERG-2008", "AGA8-Detail"]:
            try:
                res = calculate_aga8(mixture, temperature_k, pressure_pa, method)
                comparisons.append(ZFactorComparison(
                    method=method,
                    z_factor=res.compressibility_factor,
                    density=res.density,
                    molar_mass=res.molar_mass,
                    enthalpy=res.enthalpy,
                    entropy=res.entropy,
                    cp=res.cp,
                    cv=res.cv,
                    ppr=ppr, tpr=tpr, valid=True, warning=None
                ))
            except Exception as e:
                self.logger.debug(f"AGA8 {method} comparison unavailable: {e}")

        # 2.5 Add NeqSim backends for comparison
        for method in ["neqsim-gerg2008", "neqsim-srk", "neqsim-pr", "neqsim-srk-cpa"]:
            if self._is_neqsim_backend(main_backend or "") and method == main_backend:
                continue
            try:
                res, _ = calculate_neqsim(mixture, temperature_k, pressure_pa, method)
                comparisons.append(ZFactorComparison(
                    method=method,
                    z_factor=res.compressibility_factor,
                    density=res.density,
                    molar_mass=res.molar_mass,
                    enthalpy=res.enthalpy,
                    entropy=res.entropy,
                    cp=res.cp,
                    cv=res.cv,
                    ppr=ppr, tpr=tpr, valid=True, warning=None
                ))
            except Exception as e:
                self.logger.debug(f"NeqSim {method} comparison unavailable: {e}")

        # 3. Add HEOS, SRK, PR — reuse main result when available
        for method in ["HEOS", "SRK", "PR"]:
            try:
                if method == "HEOS" and mixture.check_heos_compatibility():
                    continue
                if method == main_backend and main_actual is not None:
                    # Reuse already-computed values instead of a second state
                    a = main_actual
                    comparisons.append(ZFactorComparison(
                        method=method,
                        z_factor=a.compressibility_factor,
                        density=a.density,
                        molar_mass=a.molar_mass,
                        enthalpy=a.enthalpy,
                        entropy=a.entropy,
                        cp=a.cp,
                        cv=a.cv,
                        ppr=ppr, tpr=tpr, valid=True, warning=None
                    ))
                else:
                    state = self._create_state(mixture, temperature_k, pressure_pa, method)
                    res = self._calculate_actual_conditions(state)
                    comparisons.append(ZFactorComparison(
                        method=method,
                        z_factor=res.compressibility_factor,
                        density=res.density,
                        molar_mass=res.molar_mass,
                        enthalpy=res.enthalpy,
                        entropy=res.entropy,
                        cp=res.cp,
                        cv=res.cv,
                        ppr=ppr, tpr=tpr, valid=True, warning=None
                    ))
            except Exception as e:
                self.logger.debug(f"{method} comparison skipped: {e}")

        return comparisons

    def _calculate_z_only_fallback(
        self,
        mixture: GasMixture,
        temperature_k: float,
        pressure_pa: float,
        volume_m3: Optional[float],
        standard_T: float,
        standard_P: float,
        standard_name: Optional[str]
    ) -> Optional[CalculationResult]:
        """
        Return a limited result when all CoolProp backends fail.

        Only Z, density, molar mass, SG and volume conversion are estimated.
        Enthalpy/entropy/Cp/Cv/phase information are intentionally left as NaN.
        """
        try:
            comparisons = self._calculate_z_factor_comparison(mixture, temperature_k, pressure_pa)
            ann10 = next(
                (
                    item for item in comparisons
                    if item.method == "Standing-Katz ANN10"
                    and item.valid
                    and item.z_factor is not None
                    and item.z_factor > 0
                ),
                None
            )
            if ann10 is None:
                self.logger.warning("Standing-Katz ANN10 fallback unavailable or outside validity range")
                return None

            pseudo = self.z_factor_estimator.pseudo_critical(mixture)
            z_actual = ann10.z_factor
            density = self._density_from_z(pressure_pa, temperature_k, pseudo.molar_mass_kg_mol, z_actual)

            # Standard conditions – only need ANN10 Z; skip full comparison
            std_estimates = self.z_factor_estimator.estimates(mixture, standard_T, standard_P)
            std_ann10 = next(
                (
                    item for item in std_estimates
                    if item.method == "Standing-Katz ANN10"
                    and item.valid
                    and item.z_factor is not None
                    and item.z_factor > 0
                ),
                None
            )
            z_std = std_ann10.z_factor if std_ann10 is not None else 1.0
            rho_std = self._density_from_z(standard_P, standard_T, pseudo.molar_mass_kg_mol, z_std)

            rho_air = self._air_density(standard_P, standard_T)
            sg = rho_std / rho_air

            actual_results = ActualConditionResults(
                temperature=temperature_k,
                pressure=pressure_pa,
                density=density,
                molar_mass=pseudo.molar_mass_kg_mol,
                compressibility_factor=z_actual,
                internal_energy=math.nan,
                enthalpy=math.nan,
                entropy=math.nan,
                cp=math.nan,
                cv=math.nan,
                isentropic_exponent=None,
                speed_of_sound=None
            )
            standard_results = StandardConditionResults(
                density_std=rho_std,
                specific_gravity=sg,
                reference_temperature=standard_T,
                reference_pressure=standard_P,
                standard_name=standard_name
            )

            heating_results = None
            try:
                hhv_mass, lhv_mass = self._calculate_heating_values_reference(mixture)
                heating_results = self._package_heating_values(
                    hhv_mass,
                    lhv_mass,
                    rho_std,
                    sg,
                    "Referans veri tabanı"
                )
            except Exception as e:
                self.logger.info(f"Heating values unavailable in Z-only fallback: {e}")

            volume_results = None
            if volume_m3 is not None:
                mass = density * volume_m3
                volume_results = VolumeConversion(
                    actual_volume=volume_m3,
                    mass=mass,
                    standard_volume=mass / rho_std,
                    normal_volume=None,
                    normal_volume_error="Z-only fallback normal hacim hesaplamaz"
                )

            hydrate_results = self._calculate_hydrate_formation(
                temperature_k,
                pressure_pa,
                sg
            )

            return CalculationResult(
                backend_used="Standing-Katz ANN10 (Z-only fallback)",
                actual=actual_results,
                standard=standard_results,
                heating=heating_results,
                volume_conversion=volume_results,
                phase_envelope=None,
                z_factor_comparison=comparisons,
                z_fallback_warning=(
                    "CoolProp HEOS/SRK/PR başarısız oldu; yalnızca Standing-Katz ANN10 "
                    "ile Z ve yoğunluk tahmini yapıldı. Entalpi, entropi, Cp/Cv ve faz "
                    "bilgileri bu fallbackte hesaplanmaz."
                ),
                hydrate=hydrate_results
            )
        except Exception as e:
            self.logger.warning(f"Standing-Katz ANN10 fallback failed: {e}")
            return None

    @staticmethod
    def _density_from_z(pressure_pa: float, temperature_k: float, molar_mass: float, z_factor: float) -> float:
        return pressure_pa * molar_mass / (z_factor * 8.314462618 * temperature_k)
    
    def _calculate_with_backend(
        self,
        mixture: GasMixture,
        temperature_k: float,
        pressure_pa: float,
        volume_m3: Optional[float],
        backend: str,
        standard_T: float = config.T_STANDARD,
        standard_P: float = config.P_STANDARD,
        standard_name: Optional[str] = None
    ) -> CalculationResult:
        """Perform calculation with specific backend and package results."""

        if self._is_neqsim_backend(backend):
            return self._compute_neqsim(
                mixture, temperature_k, pressure_pa, volume_m3, backend,
                standard_T, standard_P, standard_name
            )
        elif backend in ["GERG-2008", "AGA8-Detail"]:
            actual_results, standard_results, phase_envelope = self._compute_aga8(
                mixture, temperature_k, pressure_pa, backend,
                standard_T, standard_P, standard_name
            )
        else:
            actual_results, standard_results, phase_envelope = self._compute_coolprop(
                mixture, temperature_k, pressure_pa, backend,
                standard_T, standard_P, standard_name
            )

        return self._finalize_result(
            mixture, actual_results, standard_results, phase_envelope,
            temperature_k, pressure_pa, volume_m3, backend,
            standard_T, standard_P
        )

    def _compute_aga8(
        self, mixture, temperature_k, pressure_pa, backend,
        standard_T, standard_P, standard_name
    ):
        """Actual + standard results using GERG-2008 / AGA8-Detail."""
        actual_results = calculate_aga8(mixture, temperature_k, pressure_pa, backend)
        standard_results = StandardConditionResults(
            density_std=None,
            specific_gravity=None,
            reference_temperature=standard_T, reference_pressure=standard_P,
            standard_name=standard_name
        )
        try:
            std_res = calculate_aga8(mixture, standard_T, standard_P, backend)
            standard_results.density_std = std_res.density
            rho_air = self._air_density(standard_P, standard_T)
            standard_results.specific_gravity = std_res.density / rho_air
        except Exception as e:
            self.logger.warning(f"Standard condition calculation failed with {backend}: {e}")

        phase_envelope = None
        try:
            if not mixture.check_heos_compatibility():
                pe_backend = "HEOS"
            else:
                pe_backend = "SRK"
            state = self._create_state(mixture, temperature_k, pressure_pa, pe_backend)
            phase_envelope = self._calculate_phase_envelope(state, pe_backend)
        except Exception as e:
            self.logger.debug(f"Phase envelope skipped: {e}")

        return actual_results, standard_results, phase_envelope

    def _compute_coolprop(
        self, mixture, temperature_k, pressure_pa, backend,
        standard_T, standard_P, standard_name
    ):
        """Actual + standard + phase results using CoolProp HEOS/SRK/PR."""
        state = self._create_state(mixture, temperature_k, pressure_pa, backend)
        actual_results = self._calculate_actual_conditions(state)
        standard_results = self._calculate_standard_conditions(
            mixture, backend, standard_T, standard_P, standard_name
        )
        phase_envelope = self._calculate_phase_envelope(state, backend)
        return actual_results, standard_results, phase_envelope

    def _compute_neqsim(
        self, mixture, temperature_k, pressure_pa, volume_m3,
        backend, standard_T, standard_P, standard_name
    ):
        """Full calculation using NeqSim backend (actual + standard + transport)."""
        if not NEQSIM_AVAILABLE:
            raise BackendNotAvailableError(backend)

        actual_results, transport = calculate_neqsim(
            mixture, temperature_k, pressure_pa, backend
        )

        standard_results = StandardConditionResults(
            density_std=None,
            specific_gravity=None,
            reference_temperature=standard_T,
            reference_pressure=standard_P,
            standard_name=standard_name
        )

        try:
            std_actual, _ = calculate_neqsim(mixture, standard_T, standard_P, backend)
            standard_results.density_std = std_actual.density
            rho_air = self._air_density(standard_P, standard_T)
            standard_results.specific_gravity = std_actual.density / rho_air
        except Exception as e:
            self.logger.warning(f"NeqSim standard condition failed with {backend}: {e}")

        result = self._finalize_result(
            mixture, actual_results, standard_results, None,
            temperature_k, pressure_pa, volume_m3, backend,
            standard_T, standard_P
        )

        result.transport = transport

        return result

    def _finalize_result(
        self, mixture, actual_results, standard_results, phase_envelope,
        temperature_k, pressure_pa, volume_m3, backend,
        standard_T, standard_P
    ):
        """Common post-processing: heating, volume, Z-comparison, packaging."""
        rho_std = standard_results.density_std
        sg = standard_results.specific_gravity

        if rho_std is None or sg is None:
            self.logger.warning(
                "Standard condition calculation failed; heating values and "
                "volume conversion will be limited."
            )

        heating_results = self._calculate_heating_values(
            mixture, rho_std, sg, backend, standard_T, standard_P
        )
        volume_results = None
        if volume_m3 is not None and rho_std is not None:
            cp_backend = backend
            if cp_backend in ["GERG-2008", "AGA8-Detail"]:
                cp_backend = "SRK" if mixture.check_heos_compatibility() else "HEOS"
            volume_results = self._calculate_volume_conversion(
                volume_m3, actual_results.density, rho_std, mixture, cp_backend
            )
        hydrate_results = self._calculate_hydrate_formation(
            temperature_k, pressure_pa, sg, mixture, backend
        )
        result = CalculationResult(
            backend_used=backend,
            actual=actual_results,
            standard=standard_results,
            heating=heating_results,
            volume_conversion=volume_results,
            phase_envelope=phase_envelope,
            hydrate=hydrate_results
        )
        result.z_factor_comparison = self._calculate_z_factor_comparison(
            mixture, temperature_k, pressure_pa,
            main_actual=actual_results, main_backend=backend,
        )
        return result

    def _calculate_hydrate_formation(
        self,
        temperature_k: float,
        pressure_pa: float,
        specific_gravity: Optional[float],
        mixture: Optional[GasMixture] = None,
        backend: Optional[str] = None,
    ) -> Optional[HydrateResults]:
        """Calculate gas hydrate formation temperature.

        Args:
            temperature_k: Operating temperature in Kelvin
            pressure_pa: Operating pressure in Pascals
            specific_gravity: Gas specific gravity (dimensionless)
            mixture: Gas mixture (for NeqSim CPA-based calculation)
            backend: Backend used (to check if NeqSim available)

        Returns:
            HydrateResults object or None if calculation fails
        """
        try:
            if specific_gravity is None or pressure_pa <= 0 or specific_gravity <= 0:
                self.logger.warning(
                    f"Hydrate calculation skipped due to invalid inputs: "
                    f"pressure={pressure_pa} Pa, specific_gravity={specific_gravity}"
                )
                return None

            # Convert pressure from Pa to psia
            # 1 psi = 6894.757 Pa
            p_psia = pressure_pa / 6894.757
            if p_psia <= 0:
                return None

            # Calculate temperatures in Fahrenheit
            # 1. Hammerschmidt (1934) — SG-duyarsız; SG≠0.6 için ±3-5°F hata payı vardır
            t_f_hammerschmidt = 8.9 * (p_psia ** 0.285) - 38.2

            # 2. Motiee (1991)
            log_p = math.log10(p_psia)
            t_f_motiee = (
                -238.24469
                + 78.99667 * log_p
                - 5.352544 * (log_p ** 2)
                + 349.473877 * specific_gravity
                - 150.854675 * (specific_gravity ** 2)
                - 27.604065 * log_p * specific_gravity
            )

            # 3. Towler & Mokhatab (2005)
            ln_p = math.log(p_psia)
            ln_gamma = math.log(specific_gravity)
            t_f_towler_mokhatab = (
                13.47 * ln_p
                + 34.27 * ln_gamma
                - 1.675 * ln_gamma * ln_p
                - 20.35
            )

            # Convert predicted temperatures to Kelvin
            t_k_hammerschmidt = (t_f_hammerschmidt - 32) * 5 / 9 + 273.15
            t_k_motiee = (t_f_motiee - 32) * 5 / 9 + 273.15
            t_k_towler_mokhatab = (t_f_towler_mokhatab - 32) * 5 / 9 + 273.15

            # 4. NeqSim CPA-based hydrate (if available)
            t_k_neqsim = None
            if NEQSIM_AVAILABLE and mixture is not None:
                try:
                    t_k_neqsim = get_neqsim_hydrate_temperature(mixture, temperature_k, pressure_pa)
                except Exception as e:
                    self.logger.debug(f"NeqSim hydrate calculation failed: {e}")

            # Average of the three empirical models only
            temps = [t_k_hammerschmidt, t_k_motiee, t_k_towler_mokhatab]
            t_k_average = sum(temps) / len(temps)

            # NeqSim CPA result shown separately (recommended)
            neqsim_result: Optional[float] = None
            neqsim_risk: Optional[bool] = None
            if t_k_neqsim is not None and not math.isnan(t_k_neqsim):
                neqsim_result = t_k_neqsim
                neqsim_risk = temperature_k <= t_k_neqsim

            # Hydrate formation risk assessment
            risk_hammerschmidt = temperature_k <= t_k_hammerschmidt
            risk_motiee = temperature_k <= t_k_motiee
            risk_towler_mokhatab = temperature_k <= t_k_towler_mokhatab
            risk_average = temperature_k <= t_k_average

            return HydrateResults(
                specific_gravity=specific_gravity,
                operating_temperature=temperature_k,
                operating_pressure=pressure_pa,
                t_hydrate_hammerschmidt=t_k_hammerschmidt,
                t_hydrate_motiee=t_k_motiee,
                t_hydrate_towler_mokhatab=t_k_towler_mokhatab,
                t_hydrate_average=t_k_average,
                t_hydrate_neqsim=neqsim_result,
                risk_neqsim=neqsim_risk,
                risk_hammerschmidt=risk_hammerschmidt,
                risk_motiee=risk_motiee,
                risk_towler_mokhatab=risk_towler_mokhatab,
                risk_average=risk_average
            )
        except Exception as e:
            self.logger.error(f"Error calculating hydrate formation: {e}")
            return None
    def _create_state(
        self,
        mixture: GasMixture,
        temperature_k: float,
        pressure_pa: float,
        backend: str
    ) -> 'CP.AbstractState':
        """
        Create and update CoolProp state.
        
        Args:
            mixture: Gas mixture
            temperature_k: Temperature (K)
            pressure_pa: Pressure (Pa)
            backend: Backend name
            
        Returns:
            Updated CoolProp AbstractState
            
        Raises:
            StateUpdateError: If state creation/update fails
        """
        try:
            # Create state
            mixture_string = mixture.to_coolprop_string()
            self.logger.debug(f"Creating state: {backend}, {mixture_string}")
            
            state = CP.AbstractState(backend, mixture_string)
            
            # Set fractions
            fractions = mixture.get_decimal_fractions()
            if mixture.fraction_type == 'molar':
                state.set_mole_fractions(fractions)
            else:
                state.set_mass_fractions(fractions)
            
            # Update state
            state.update(CP.PT_INPUTS, pressure_pa, temperature_k)
            
            return state
            
        except Exception as e:
            raise StateUpdateError(backend, temperature_k, pressure_pa, e)
            
    def _calculate_phase_envelope(
        self,
        state: 'CP.AbstractState',
        backend: str
    ) -> Optional[PhaseEnvelopeData]:
        """
        Calculate phase envelope for the gas mixture.
        """
        try:
            self.logger.debug(f"Attempting phase envelope calculation with {backend}")
            
            # Try to build the phase envelope. Sometimes this fails for heavy mixtures.
            state.build_phase_envelope("")
            
            # Extract the actual data arrays
            pe_data = state.get_phase_envelope_data()
            T_array = list(pe_data.T)
            P_array = list(pe_data.p)

            if not T_array or not P_array:
                return None

            # Detect multi-lobed envelopes by temperature discontinuity
            lobes = []
            current_lobe = [(T_array[0], P_array[0])]
            for i in range(1, len(T_array)):
                if abs(T_array[i] - T_array[i - 1]) > 10.0:
                    lobes.append(current_lobe)
                    current_lobe = []
                current_lobe.append((T_array[i], P_array[i]))
            if current_lobe:
                lobes.append(current_lobe)

            primary_lobe = max(lobes, key=lambda l: max(p[0] for p in l) - min(p[0] for p in l))
            T_primary, P_primary = zip(*primary_lobe)

            cricondentherm_t = max(T_primary)

            cricondenbar_p: Optional[float] = None
            max_p_idx = P_primary.index(max(P_primary))
            cricondenbar_t = T_primary[max_p_idx]
            cricondenbar_p = P_primary[max_p_idx]

            # Try to extract critical point from CoolProp state
            critical_t: Optional[float] = None
            critical_p: Optional[float] = None
            try:
                critical_t = state.keyed_output(CP.iT_critical)
                critical_p = state.keyed_output(CP.iP_critical)
            except Exception as e:
                self.logger.debug(f"Critical point extraction failed: {e}")

            return PhaseEnvelopeData(
                temperature_k=T_array,
                pressure_pa=P_array,
                cricondentherm_t=cricondentherm_t,
                cricondenbar_p=cricondenbar_p,
                cricondenbar_t=cricondenbar_t,
                critical_t=critical_t,
                critical_p=critical_p,
            )
        except Exception as e:
            self.logger.info(
                f"Phase envelope unavailable with {backend}; main thermodynamic results are still valid. "
                f"Reason: {e}"
            )
            return None
    
    def _calculate_actual_conditions(
        self,
        state: 'CP.AbstractState'
    ) -> ActualConditionResults:
        """
        Calculate properties at actual operating conditions.
        
        Args:
            state: CoolProp state at operating conditions
            
        Returns:
            Actual condition results
        """
        # Basic properties
        density = state.rhomass()
        molar_mass = state.molar_mass()
        z_factor = state.compressibility_factor()
        
        # Thermodynamic properties (convert J to kJ)
        u = state.umass() / 1000.0  # kJ/kg
        h = state.hmass() / 1000.0  # kJ/kg
        s = state.smass() / 1000.0  # kJ/(kg·K)
        cp = state.cpmass() / 1000.0  # kJ/(kg·K)
        cv = state.cvmass() / 1000.0  # kJ/(kg·K)
        
        # Isentropic exponent (real gas via CoolProp's built-in method)
        k = None
        try:
            k = state.isentropic_exponent()
        except Exception:
            try:
                k = cp / cv if cv > 1e-10 else None
            except (ZeroDivisionError, ArithmeticError):
                pass
        
        speed_sound = None
        try:
            speed_sound = state.speed_sound()
        except Exception as e:
            self.logger.warning(f"Speed of sound calculation failed: {e}")

        # Transport properties (CoolProp supports these for many pure fluids & mixtures)
        viscosity = None
        try:
            viscosity = state.viscosity() / 0.001  # Pa·s → cP
        except Exception:
            pass

        thermal_conductivity = None
        try:
            thermal_conductivity = state.conductivity()  # W/m·K
        except Exception:
            pass

        joule_thomson = None
        try:
            joule_thomson = state.joule_thomson_coefficient()  # K/Pa
        except Exception:
            pass

        surface_tension_val = None
        try:
            surface_tension_val = state.surface_tension()  # N/m
        except Exception:
            pass
        
        return ActualConditionResults(
            temperature=state.T(),
            pressure=state.p(),
            density=density,
            molar_mass=molar_mass,
            compressibility_factor=z_factor,
            internal_energy=u,
            enthalpy=h,
            entropy=s,
            cp=cp,
            cv=cv,
            isentropic_exponent=k,
            speed_of_sound=speed_sound,
            viscosity=viscosity,
            thermal_conductivity=thermal_conductivity,
            joule_thomson_coefficient=joule_thomson,
            surface_tension=surface_tension_val,
        )
    
    def _calculate_standard_conditions(
        self,
        mixture: GasMixture,
        backend: str,
        T_std: float,
        P_std: float,
        standard_name: Optional[str] = None
    ) -> StandardConditionResults:
        """
        Calculate properties at standard conditions.
        
        Args:
            mixture: Gas mixture
            backend: Backend to use
            T_std: Standard temperature (K)
            P_std: Standard pressure (Pa)
            standard_name: Name of standard used
            
        Returns:
            Standard condition results
        """
        # Create state at standard conditions
        state_std = self._create_state(mixture, T_std, P_std, backend)
        rho_std = state_std.rhomass()
        
        # Calculate specific gravity (relative to air at same conditions)
        rho_air = self._air_density(P_std, T_std)
        if rho_air != P_std / (287.058 * T_std):
            self.logger.debug(f"Air density at standard conditions: {rho_air:.3f} kg/m³")
        else:
            self.logger.warning(
                f"Could not get air density from CoolProp, using Ideal Gas Law "
                f"(rho={rho_air:.3f} kg/m3 for T={T_std}K, P={P_std}Pa)"
            )
        
        sg = rho_std / rho_air
        
        return StandardConditionResults(
            density_std=rho_std,
            specific_gravity=sg,
            reference_temperature=T_std,
            reference_pressure=P_std,
            standard_name=standard_name
        )
    
    def _calculate_heating_values(
        self,
        mixture: GasMixture,
        rho_std: Optional[float],
        sg: Optional[float],
        backend: str,
        T_ref: float,
        P_ref: float
    ) -> Optional[HeatingValues]:
        """Calculate heating values with multi-stage fallback.

        Args:
            mixture: Gas mixture
            rho_std: Standard density (kg/Sm³), may be None
            sg: Specific gravity, may be None
            backend: Backend being used
            T_ref: Reference temperature for combustion (K)
            P_ref: Reference pressure (Pa)

        Returns:
            Heating values or None if calculation fails
        """
        if rho_std is None or rho_std <= 0:
            self.logger.warning(
                "Standard density unavailable; skipping heating value calculation."
            )
            return None

        # Stage 0: NeqSim ISO 6976 (for NeqSim backends or generally)
        if NEQSIM_AVAILABLE:
            try:
                iso_data = get_neqsim_iso6976(mixture, T_ref)
                if iso_data is not None and iso_data.get("gcv_kj_m3", 0) > 0:
                    hhv_vol = iso_data["gcv_kj_m3"] / 1000.0
                    lhv_vol = iso_data["lcv_kj_m3"] / 1000.0
                    wobbe = iso_data.get("wobbe_kj_m3", 0) / 1000.0
                    hhv_mass = hhv_vol / rho_std if rho_std > 0 else 0.0
                    lhv_mass = lhv_vol / rho_std if rho_std > 0 else 0.0
                    if hhv_mass > 0 and lhv_mass > 0:
                        self.logger.info("Using NeqSim ISO 6976 heating values")
                        return self._package_heating_values(
                            hhv_mass, lhv_mass, rho_std, sg, "NeqSim ISO 6976"
                        )
            except Exception as e:
                self.logger.info(f"NeqSim ISO 6976 unavailable: {e}")

        # CoolProp API requires CoolProp backends
        if backend in ["GERG-2008", "AGA8-Detail"]:
            backend = "SRK" if mixture.check_heos_compatibility() else "HEOS"
        if self._is_neqsim_backend(backend):
            backend = "SRK" if mixture.check_heos_compatibility() else "HEOS"

        # Try Stage 1: Built-in method (HEOS only)
        if backend == "HEOS":
            try:
                hhv_mass, lhv_mass = self._calculate_heating_values_builtin(
                    mixture,
                    backend,
                    T_ref,
                    P_ref
                )
                if hhv_mass > 0 and lhv_mass > 0:
                    return self._package_heating_values(
                        hhv_mass,
                        lhv_mass,
                        rho_std,
                        sg,
                        "CoolProp yerleşik"
                    )
            except Exception as e:
                self.logger.info(f"CoolProp built-in HHV/LHV unavailable: {e}")
        
        # Try Stage 2: Component-based CoolProp
        try:
            hhv_mass, lhv_mass = self._calculate_heating_values_component_based(
                mixture,
                backend,
                T_ref,
                P_ref
            )
            if hhv_mass > 0 and lhv_mass > 0:
                return self._package_heating_values(
                    hhv_mass,
                    lhv_mass,
                    rho_std,
                    sg,
                    "Bileşen bazlı (CoolProp)"
                )
        except Exception as e:
            self.logger.info(f"CoolProp component HHV/LHV unavailable: {e}")

        # Try Stage 2.5: ISO 6976:2016 stoichiometric method
        try:
            if is_iso6976_compatible(mixture, GasMixture._format_gas_name_for_coolprop):
                hhv_mass, lhv_mass = calculate_iso6976_heating_values(
                    mixture,
                    GasMixture._format_gas_name_for_coolprop,
                    T_ref
                )
                if hhv_mass is not None and lhv_mass is not None and hhv_mass > 0:
                    self.logger.info("Using ISO 6976:2016 standard heating values")
                    return self._package_heating_values(
                        hhv_mass,
                        lhv_mass,
                        rho_std,
                        sg,
                        "ISO 6976:2016"
                    )
        except Exception as e:
            self.logger.info(f"ISO 6976 HHV/LHV unavailable: {e}")

        # Try Stage 3: Reference database
        try:
            # Note: Database values are typically at 15°C or 25°C.
            # If user selected a very different standard (e.g. 0°C),
            # this might introduce a small error.
            if abs(T_ref - 288.15) > 5.0 and abs(T_ref - 298.15) > 5.0:
                 self.logger.warning(
                     f"Using reference DB values (15°C/25°C base) for T={T_ref:.2f}K. "
                     "Result may have slight deviation."
                 )
            
            hhv_mass, lhv_mass = self._calculate_heating_values_reference(
                mixture
            )
            if hhv_mass > 0 and lhv_mass > 0:
                self.logger.info("Using reference database heating values")
                return self._package_heating_values(
                    hhv_mass,
                    lhv_mass,
                    rho_std,
                    sg,
                    "Referans veri tabanı"
                )
        except Exception as e:
            self.logger.warning(f"Reference database HHV/LHV failed: {e}")
        
        # All methods failed
        self.logger.error("All heating value calculation methods failed")
        return None
    
    def _calculate_heating_values_builtin(
        self,
        mixture: GasMixture,
        backend: str,
        T_ref: float,
        P_ref: float
    ) -> Tuple[float, float]:
        """
        Calculate heating values using CoolProp built-in method.
        """
        state_std = self._create_state(mixture, T_ref, P_ref, backend)
        if not hasattr(state_std, "HHVmass") or not hasattr(state_std, "LHVmass"):
            raise HeatingValueError(message="CoolProp AbstractState has no HHVmass/LHVmass API")
        
        hhv = state_std.HHVmass() / 1e6  # Convert J/kg to MJ/kg
        lhv = state_std.LHVmass() / 1e6
        
        if hhv < 1e-6 or lhv < 1e-6:
            raise HeatingValueError(message="Built-in method returned zero values")
        
        return hhv, lhv
    
    def _calculate_heating_values_component_based(
        self,
        mixture: GasMixture,
        backend: str,
        T_ref: float,
        P_ref: float
    ) -> Tuple[float, float]:
        """Calculate heating values by summing component contributions.

        HHVmass()/LHVmass() returns J/kg, converted to MJ/kg.
        Weights are mass fractions; molar fractions are converted via
        _get_heating_value_mass_weights to match the mass-basis API.
        """
        weights = self._get_heating_value_mass_weights(mixture)
        total_hhv = 0.0
        total_lhv = 0.0
        missing_api_logged = False
        
        for component in mixture.components:
            try:
                component_name = GasMixture._format_gas_name_for_coolprop(component.name)
                state = CP.AbstractState(backend, component_name)
                state.update(CP.PT_INPUTS, P_ref, T_ref)

                if not hasattr(state, "HHVmass") or not hasattr(state, "LHVmass"):
                    if not missing_api_logged:
                        self.logger.info("CoolProp AbstractState has no per-component HHVmass/LHVmass API")
                        missing_api_logged = True
                    continue
                
                hhv = state.HHVmass() / 1e6
                lhv = state.LHVmass() / 1e6
                
                if hhv < 1e-6:
                    hhv = 0.0
                if lhv < 1e-6:
                    lhv = 0.0
                
                weight = weights.get(component.name, component.to_decimal())
                if weight <= 0:
                    continue
                total_hhv += weight * hhv
                total_lhv += weight * lhv
                
            except Exception as e:
                self.logger.warning(
                    f"Could not get heating values for {component.name}: {e}. "
                    "Using 0 contribution."
                )
                continue
        
        if total_hhv < 1e-6:
            raise HeatingValueError(
                message="No combustible components with heating value data"
            )
            
        return total_hhv, total_lhv
    
    def _calculate_heating_values_reference(
        self,
        mixture: GasMixture
    ) -> Tuple[float, float]:
        """
        Calculate heating values using reference database.
        
        Args:
            mixture: Gas mixture
            
        Returns:
            Tuple of (HHV, LHV) in MJ/kg
        """
        weights = self._get_heating_value_mass_weights(mixture)
        total_hhv = 0.0
        total_lhv = 0.0
        components_found = 0
        
        for component in mixture.components:
            component_name = GasMixture._format_gas_name_for_coolprop(component.name)
            ref_values = get_reference_heating_values(component_name)
            
            if ref_values is not None:
                hhv, lhv = ref_values
                weight = weights.get(component.name, component.to_decimal())
                total_hhv += weight * hhv
                total_lhv += weight * lhv
                components_found += 1
                
                self.logger.debug(
                    f"Reference values for {component.name}: "
                    f"HHV={hhv:.2f}, LHV={lhv:.2f} MJ/kg, weight={weight:.6f}"
                )
            else:
                self.logger.warning(
                    f"No reference heating values for {component.name}"
                )
        
        if components_found == 0:
            raise HeatingValueError(
                message="No reference data available for any component"
            )
        
        if total_hhv < 1e-6:
            raise HeatingValueError(
                message="No combustible components in reference database"
            )
        
        self.logger.info(
            f"Reference database calculation: HHV={total_hhv:.4f}, "
            f"LHV={total_lhv:.4f} MJ/kg ({components_found}/{len(mixture.components)} components found)"
        )
        
        return total_hhv, total_lhv

    def _get_heating_value_mass_weights(self, mixture: GasMixture) -> dict:
        """
        Return component weights for mass-basis heating value averaging.

        Reference heating values are stored as MJ/kg. Mass fractions can be used
        directly; molar fractions must be converted to mass fractions first.
        """
        if mixture.fraction_type == "mass":
            return {component.name: component.to_decimal() for component in mixture.components}

        weighted_masses = {}
        total = 0.0

        for component in mixture.components:
            component_name = GasMixture._format_gas_name_for_coolprop(component.name)
            try:
                molar_mass = CP.PropsSI("M", component_name)
            except Exception:
                state = CP.AbstractState("HEOS", component_name)
                molar_mass = state.molar_mass()

            weighted_mass = component.to_decimal() * molar_mass
            weighted_masses[component.name] = weighted_mass
            total += weighted_mass

        if total <= 0:
            raise HeatingValueError(message="Could not convert molar fractions to mass fractions")

        return {
            component_name: weighted_mass / total
            for component_name, weighted_mass in weighted_masses.items()
        }
    
    def _package_heating_values(
        self,
        hhv_mass: float,
        lhv_mass: float,
        rho_std: float,
        sg: Optional[float],
        method: str
    ) -> HeatingValues:
        """Package heating values into result model.

        Args:
            hhv_mass: HHV in MJ/kg
            lhv_mass: LHV in MJ/kg
            rho_std: Standard density (kg/Sm³)
            sg: Specific gravity (may be None)
            method: Calculation method description
        """
        hhv_vol = hhv_mass * rho_std
        lhv_vol = lhv_mass * rho_std

        if sg is not None and sg > 0:
            wobbe = hhv_vol / (sg ** 0.5)
        else:
            wobbe = 0.0

        hhv_btu_scf = hhv_vol * config.MMBTU_PER_MJ / config.M3_TO_SCF * 1e6
        
        return HeatingValues(
            hhv_mass=hhv_mass,
            lhv_mass=lhv_mass,
            hhv_volume=hhv_vol,
            lhv_volume=lhv_vol,
            wobbe_index=wobbe,
            hhv_btu_scf=hhv_btu_scf,
            calculation_method=method
        )
    
    def _calculate_volume_conversion(
        self,
        volume_actual: float,
        rho_actual: float,
        rho_std: float,
        mixture: GasMixture,
        backend: str
    ) -> VolumeConversion:
        """
        Calculate volume conversion from actual to standard and normal conditions.
        
        Args:
            volume_actual: Actual volume (m³)
            rho_actual: Actual density (kg/m³)
            rho_std: Standard density (kg/Sm³)
            mixture: Gas mixture definition
            backend: Backend to use for normal density calculation
            
        Returns:
            Volume conversion results
        """
        mass = rho_actual * volume_actual  # kg
        volume_std = mass / rho_std  # Sm³
        
        # Calculate Normal Volume (NCM) @ 0°C, 1 atm
        volume_norm = None
        error_msg = None
        try:
            # Create state at Normal conditions
            state_norm = self._create_state(
                mixture, 
                config.T_NORMAL, 
                config.P_NORMAL, 
                backend
            )
            rho_norm = state_norm.rhomass()
            volume_norm = mass / rho_norm
        except Exception as e:
            self.logger.warning(f"Failed to calculate NCM volume: {e}")
            error_msg = "0°C'de olası yoğuşma (faz değişimi) veya hesaplama hatası"
        
        return VolumeConversion(
            actual_volume=volume_actual,
            mass=mass,
            standard_volume=volume_std,
            normal_volume=volume_norm,
            normal_volume_error=error_msg
        )
