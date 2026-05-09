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
    CalculationConvergenceError
)
from natural_gas_main.models.gas_data import GasMixture
from natural_gas_main.models.calculation_result import (
    CalculationResult,
    ActualConditionResults,
    StandardConditionResults,
    HeatingValues,
    VolumeConversion,
    PhaseEnvelopeData,
    ZFactorComparison
)
from natural_gas_main.models.heating_value_db import get_reference_heating_values
from natural_gas_main.models.z_factor import StandingKatzZFactor

# Try to import CoolProp
CP = None
COOLPROP_AVAILABLE = False


try:
    import pyaga8
    PYAGA8_AVAILABLE = True
    logging.info("pyaga8 başarıyla yüklendi")
except ImportError as e:
    logging.error(f"pyaga8 içe aktarılamadı: {e}")
    PYAGA8_AVAILABLE = False

try:
    import CoolProp.CoolProp as CP
    COOLPROP_AVAILABLE = True
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
            BackendNotAvailableError: If CoolProp is not installed
        """
        if not COOLPROP_AVAILABLE:
            raise BackendNotAvailableError("CoolProp")
        
        self.logger = logging.getLogger(__name__)
        self.z_factor_estimator = StandingKatzZFactor(CP)
        
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
    ) -> Tuple[Optional[CalculationResult], str]:
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
                    pressure_pa
                )
                self.logger.info(f"Successfully calculated with {backend}")
                break
                
            except Exception as e:
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
        
        return requested_backend
    
    def _get_backend_order(self, mixture: GasMixture, preferred: str) -> List[str]:
        """
        Get prioritized list of backends to try.
        
        Args:
            mixture: Gas mixture
            preferred: Preferred backend
            
        Returns:
            Ordered list of backend names
        """
        backends = [preferred]
        
        # Check compatibility
        heos_incompatible = mixture.check_heos_compatibility()
        if heos_incompatible and preferred == "HEOS":
            backends = []
            
        # Add fallbacks in order of preference
        all_fallbacks = ["GERG-2008", "AGA8-Detail", "HEOS", "SRK", "PR"]
        for fallback in all_fallbacks:
            if fallback == "HEOS" and heos_incompatible:
                continue
            if fallback not in backends:
                backends.append(fallback)
        
        return backends

    def _calculate_z_factor_comparison(
        self,
        mixture: GasMixture,
        temperature_k: float,
        pressure_pa: float
    ) -> List[ZFactorComparison]:
        """Return comprehensive Z-factor comparisons across all backends."""
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
        except:
            ppr, tpr = 1.0, 1.0
            
        # 2. Add GERG-2008 & AGA8-Detail
        for method in ["GERG-2008", "AGA8-Detail"]:
            try:
                res = self._calculate_aga8(mixture, temperature_k, pressure_pa, method)
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
                pass
            
        # 3. Add HEOS, SRK, PR
        for method in ["HEOS", "SRK", "PR"]:
            try:
                if method == "HEOS" and mixture.check_heos_compatibility(): continue
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
                pass
            
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

            standard_comparisons = self._calculate_z_factor_comparison(mixture, standard_T, standard_P)
            std_ann10 = next(
                (
                    item for item in standard_comparisons
                    if item.method == "Standing-Katz ANN10"
                    and item.valid
                    and item.z_factor is not None
                    and item.z_factor > 0
                ),
                None
            )
            z_std = std_ann10.z_factor if std_ann10 is not None else 1.0
            rho_std = self._density_from_z(standard_P, standard_T, pseudo.molar_mass_kg_mol, z_std)

            try:
                rho_air = CP.PropsSI('D', 'T', standard_T, 'P', standard_P, 'Air')
            except Exception:
                rho_air = standard_P / (287.058 * standard_T)
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
                )
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
        """
        Perform calculation with specific backend.
        
        Args:
            mixture: Gas mixture
            temperature_k: Temperature (K)
            pressure_pa: Pressure (Pa)
            volume_m3: Optional volume (m³)
            backend: Backend to use
            standard_T: Reference standard temperature (K)
            standard_P: Reference standard pressure (Pa)
            
        Returns:
            Calculation results
        """
        if backend in ["GERG-2008", "AGA8-Detail"]:
            actual_results = self._calculate_aga8(mixture, temperature_k, pressure_pa, backend)
            # Standart conditions
            standard_results = StandardConditionResults(
                density_std=1.0, specific_gravity=1.0, reference_temperature=standard_T, reference_pressure=standard_P, standard_name=standard_name
            )
            try:
                std_res = self._calculate_aga8(mixture, standard_T, standard_P, backend)
                standard_results.density_std = std_res.density
                
                # Air density calculation using ideal gas
                rho_air = standard_P / (287.058 * standard_T)
                try:
                    rho_air = CP.PropsSI('D', 'T', standard_T, 'P', standard_P, 'Air')
                except: pass
                
                standard_results.specific_gravity = std_res.density / rho_air
            except Exception as e:
                self.logger.warning(f"Standard condition calculation failed with {backend}: {e}")
                
            state = None
            phase_envelope = None
            # Fallback to HEOS/SRK for phase envelope
            try:
                state = self._create_state(mixture, temperature_k, pressure_pa, "HEOS" if not mixture.check_heos_compatibility() else "SRK")
                phase_envelope = self._calculate_phase_envelope(state, "HEOS" if not mixture.check_heos_compatibility() else "SRK")
            except:
                pass
                
        else:
            # Create CoolProp state
            state = self._create_state(mixture, temperature_k, pressure_pa, backend)
            
            # Calculate actual condition properties
            actual_results = self._calculate_actual_conditions(state)
            
            # Calculate standard condition properties
            standard_results = self._calculate_standard_conditions(
                mixture, backend, standard_T, standard_P, standard_name
            )
            
            # Calculate Phase Envelope
            phase_envelope = self._calculate_phase_envelope(state, backend)
        
        # Calculate heating values
        # Note: We use the selected Standard T for combustion reference as well
        # This is generally acceptable for common standards
        heating_results = self._calculate_heating_values(
            mixture,
            standard_results.density_std,
            standard_results.specific_gravity,
            backend,
            standard_T,
            standard_P
        )
        
        # Calculate volume conversion if provided
        volume_results = None
        if volume_m3 is not None:
            cp_backend = backend
            if cp_backend in ["GERG-2008", "AGA8-Detail"]:
                cp_backend = "HEOS" if not mixture.check_heos_compatibility() else "SRK"
                
            volume_results = self._calculate_volume_conversion(
                volume_m3,
                actual_results.density,
                standard_results.density_std,
                mixture,
                cp_backend
            )
            
        # Package results
        result = CalculationResult(
            backend_used=backend,
            actual=actual_results,
            standard=standard_results,
            heating=heating_results,
            volume_conversion=volume_results,
            phase_envelope=phase_envelope
        )
        result.z_factor_comparison = self._calculate_z_factor_comparison(
            mixture,
            temperature_k,
            pressure_pa
        )
        return result
    
    def _calculate_aga8(self, mixture, temperature_k, pressure_pa, method="GERG-2008") -> ActualConditionResults:
        if not PYAGA8_AVAILABLE:
            raise BackendNotAvailableError(method)
            
        comp = pyaga8.Composition()
        
        aga8_mapping = {
            'methane': 'methane', 'ethane': 'ethane', 'n-propane': 'propane', 'propane': 'propane',
            'n-butane': 'n_butane', 'isobutane': 'isobutane', 'n-pentane': 'n_pentane',
            'isopentane': 'isopentane', 'n-hexane': 'hexane', 'n-heptane': 'heptane',
            'n-octane': 'octane', 'n-nonane': 'nonane', 'n-decane': 'decane',
            'hydrogen': 'hydrogen', 'oxygen': 'oxygen', 'carbonmonoxide': 'carbon_monoxide',
            'water': 'water', 'hydrogensulfide': 'hydrogen_sulfide', 'helium': 'helium',
            'argon': 'argon', 'carbondioxide': 'carbon_dioxide', 'nitrogen': 'nitrogen'
        }
        
        sum_fractions = 0.0
        for gas in mixture.components:
            coolprop_name = mixture._format_gas_name_for_coolprop(gas.name).lower()
            aga8_name = aga8_mapping.get(coolprop_name)
            if aga8_name:
                val = gas.fraction / 100.0
                setattr(comp, aga8_name, val)
                sum_fractions += val
            else:
                self.logger.warning(f"Bileşen {gas.name} AGA8 standardında desteklenmiyor. Yoksayılıyor.")
                
        if sum_fractions < 0.99:
            raise ValueError(f"AGA8 için geçerli gazların toplamı {sum_fractions} (< 0.99). AGA8 desteklenmiyor.")
            
        # Normalize just in case of float precision issues
        if abs(sum_fractions - 1.0) > 1e-5:
            # We must normalize to exactly 1.0 for pyaga8 to avoid BadSum panic
            for gas in mixture.components:
                coolprop_name = mixture._format_gas_name_for_coolprop(gas.name).lower()
                aga8_name = aga8_mapping.get(coolprop_name)
                if aga8_name:
                    current = getattr(comp, aga8_name)
                    setattr(comp, aga8_name, current / sum_fractions)
                    
        engine = pyaga8.Gerg2008() if method == "GERG-2008" else pyaga8.Detail()
        try:
            engine.set_composition(comp)
        except Exception as e:
            raise ValueError(f"AGA8 set_composition hatası: {e}")
        engine.temperature = temperature_k
        engine.pressure = pressure_pa / 1000.0
        
        engine.calc_density(0)
        engine.calc_properties()
        
        density_kg_m3 = engine.d * engine.mm               
        enthalpy_kj_kg = engine.h / engine.mm              
        entropy_kj_kg_k = engine.s / engine.mm             
        internal_energy_kj_kg = engine.u / engine.mm       
        cp_kj_kg_k = engine.cp / engine.mm                 
        cv_kj_kg_k = engine.cv / engine.mm                 
        
        return ActualConditionResults(
            temperature=temperature_k,
            pressure=pressure_pa,
            density=density_kg_m3,
            molar_mass=engine.mm / 1000.0,
            compressibility_factor=engine.z,
            internal_energy=internal_energy_kj_kg,
            enthalpy=enthalpy_kj_kg,
            entropy=entropy_kj_kg_k,
            cp=cp_kj_kg_k,
            cv=cv_kj_kg_k,
            isentropic_exponent=engine.kappa,
            speed_of_sound=engine.w
        )

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
                
            return PhaseEnvelopeData(
                temperature_k=T_array,
                pressure_pa=P_array,
                cricondentherm_t=max(T_array),
                cricondenbar_p=max(P_array)
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
        
        # Derived properties
        k = None
        try:
            k = cp / cv if cv > 1e-10 else None
        except:
            pass
        
        speed_sound = None
        try:
            speed_sound = state.speed_sound()
        except Exception as e:
            self.logger.warning(f"Speed of sound calculation failed: {e}")
        
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
            speed_of_sound=speed_sound
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
        try:
            # We must calculate air density at the SAME standard conditions
            # to be scientifically correct for SG
            rho_air = CP.PropsSI('D', 'T', T_std, 'P', P_std, 'Air')
        except:
            # Ideal Gas Law for Air: R_air = 287.058 J/(kg.K)
            rho_air = P_std / (287.058 * T_std)
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
        rho_std: float,
        sg: float,
        backend: str,
        T_ref: float,
        P_ref: float
    ) -> Optional[HeatingValues]:
        # CoolProp API requires CoolProp backends
        if backend in ["GERG-2008", "AGA8-Detail"]:
            backend = "HEOS" if not mixture.check_heos_compatibility() else "SRK"

        """
        Calculate heating values with 3-stage fallback.
        
        Args:
            mixture: Gas mixture
            rho_std: Standard density (kg/Sm³)
            sg: Specific gravity
            backend: Backend being used
            T_ref: Reference temperature for combustion (K)
            P_ref: Reference pressure (Pa)
            
        Returns:
            Heating values or None if calculation fails
        """
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
        """
        Calculate heating values by summing component contributions.
        """
        total_hhv = 0.0
        total_lhv = 0.0
        missing_api_logged = False
        
        for component in mixture.components:
            try:
                # Create state for single component
                component_name = GasMixture._format_gas_name_for_coolprop(component.name)
                state = CP.AbstractState(backend, component_name)
                state.update(CP.PT_INPUTS, P_ref, T_ref)

                if not hasattr(state, "HHVmass") or not hasattr(state, "LHVmass"):
                    if not missing_api_logged:
                        self.logger.info("CoolProp AbstractState has no per-component HHVmass/LHVmass API")
                        missing_api_logged = True
                    continue
                
                hhv = state.HHVmass() / 1e6  # MJ/kg
                lhv = state.LHVmass() / 1e6
                
                # Zero values mean no data available
                if hhv < 1e-6: hhv = 0.0
                if lhv < 1e-6: lhv = 0.0
                
                # Add weighted contribution
                fraction_decimal = component.to_decimal()
                total_hhv += fraction_decimal * hhv
                total_lhv += fraction_decimal * lhv
                
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
        sg: float,
        method: str
    ) -> HeatingValues:
        """
        Package heating values into result model.
        
        Args:
            hhv_mass: HHV in MJ/kg
            lhv_mass: LHV in MJ/kg
            rho_std: Standard density (kg/Sm³)
            sg: Specific gravity
            method: Calculation method description
            
        Returns:
            Heating values model
        """
        # Volumetric basis
        hhv_vol = hhv_mass * rho_std  # MJ/Sm³
        lhv_vol = lhv_mass * rho_std  # MJ/Sm³
        
        # Wobbe index
        wobbe = hhv_vol / (sg ** 0.5)
        
        # Industrial units (Btu/SCF)
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
