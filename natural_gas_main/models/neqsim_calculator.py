"""
NeqSim thermodynamic backend wrapper.

Provides a multi-EOS interface to Equinor's NeqSim library for natural gas
thermodynamic calculations. Supports 15+ EOS models covering cubic, CPA,
reference, and sour-gas formulations.

Requires: Java 11+ and `pip install neqsim`
"""

from __future__ import annotations

import logging
import math
from typing import Dict, Optional, Tuple

from natural_gas_main.models.calculation_result import ActualConditionResults, TransportProperties
from natural_gas_main.core.exceptions import BackendNotAvailableError

NEQSIM_AVAILABLE = False
_jneqsim = None

try:
    from neqsim import jneqsim as _jneqsim
    NEQSIM_AVAILABLE = True
    logging.getLogger(__name__).info("NeqSim başarıyla yüklendi")

    import sys as _sys
    if getattr(_sys, 'frozen', False):
        import os as _os
        _mei = _sys._MEIPASS
        for _root, _dirs, _files in _os.walk(_mei):
            for _f in _files:
                if _f.endswith('.jar'):
                    try:
                        import jpype as _jp
                        _jp.addClassPath(_os.path.join(_root, _f))
                    except Exception:
                        pass
except ImportError as e:
    logging.getLogger(__name__).error(f"NeqSim içe aktarılamadı: {e}")
except Exception as e:
    logging.getLogger(__name__).error(f"NeqSim JVM başlatılamadı: {e}")

NEQSIM_GAS_MAPPING: Dict[str, str] = {
    "methane": "methane",
    "ethane": "ethane",
    "n-propane": "propane",
    "propane": "propane",
    "n-butane": "n-butane",
    "isobutane": "isobutane",
    "n-pentane": "n-pentane",
    "isopentane": "isopentane",
    "neopentane": "neopentane",
    "n-hexane": "n-hexane",
    "isohexane": "2-methylpentane",
    "n-heptane": "n-heptane",
    "n-octane": "n-octane",
    "n-nonane": "n-nonane",
    "n-decane": "n-decane",
    "n-undecane": "n-undecane",
    "n-dodecane": "n-dodecane",
    "nitrogen": "nitrogen",
    "carbondioxide": "CO2",
    "carbon_dioxide": "CO2",
    "hydrogensulfide": "H2S",
    "hydrogen_sulfide": "H2S",
    "carbonylsulfide": "COS",
    "carbonyl_sulfide": "COS",
    "sulfurdioxide": "SO2",
    "sulfur_dioxide": "SO2",
    "water": "water",
    "hydrogen": "hydrogen",
    "oxygen": "oxygen",
    "helium": "helium",
    "argon": "argon",
    "carbonmonoxide": "CO",
    "carbon_monoxide": "CO",
    "methanol": "methanol",
    "meg": "MEG",
    "teg": "TEG",
    "mdea": "MDEA",
    "dea": "DEA",
    "mea": "MEA",
    "ethylene": "ethylene",
    "propylene": "propylene",
    "1-butene": "1-butene",
    "isobutene": "isobutene",
    "cis-2-butene": "cis-2-butene",
    "trans-2-butene": "trans-2-butene",
    "cyclopropane": "cyclopropane",
    "cyclopentane": "cyclopentane",
    "cyclohexane": "cyclohexane",
    "ammonia": "ammonia",
    "neon": "neon",
    "krypton": "krypton",
    "xenon": "xenon",
}

NEQSIM_EOS_REGISTRY: Dict[str, Dict] = {
    "neqsim-srk": {
        "class": "SystemSrkEos",
        "mixing": "no",
        "group": "SRK Ailesi",
        "desc": "Soave-Redlich-Kwong (standart)",
        "multiphase": False,
        "supports_aga8": False,
    },
    "neqsim-srk-peneloux": {
        "class": "SystemSrkPenelouxEos",
        "mixing": "no",
        "group": "SRK Ailesi",
        "desc": "SRK + Peneloux hacim düzeltmesi (iyi sıvı yoğunluğu)",
        "multiphase": False,
        "supports_aga8": False,
    },
    "neqsim-srk-mc": {
        "class": "SystemSrkMathiasCopeman",
        "mixing": "no",
        "group": "SRK Ailesi",
        "desc": "SRK + Mathias-Copeman alpha (polar bileşenler)",
        "multiphase": False,
        "supports_aga8": False,
    },
    "neqsim-srk-twucoon": {
        "class": "SystemSrkTwuCoon",
        "mixing": "no",
        "group": "SRK Ailesi",
        "desc": "SRK + Twu-Coon alpha (süperkritik)",
        "multiphase": False,
        "supports_aga8": False,
    },
    "neqsim-pr": {
        "class": "SystemPrEos",
        "mixing": "no",
        "group": "PR Ailesi",
        "desc": "Peng-Robinson (standart)",
        "multiphase": False,
        "supports_aga8": False,
    },
    "neqsim-pr-mc": {
        "class": "SystemPrMathiasCopeman",
        "mixing": "no",
        "group": "PR Ailesi",
        "desc": "PR + Mathias-Copeman alpha",
        "multiphase": False,
        "supports_aga8": False,
    },
    "neqsim-pr-twucoon": {
        "class": "SystemPrTwuCoon",
        "mixing": "no",
        "group": "PR Ailesi",
        "desc": "PR + Twu-Coon alpha (süperkritik)",
        "multiphase": False,
        "supports_aga8": False,
    },
    "neqsim-pr-danesh": {
        "class": "SystemPrDanesh",
        "mixing": "no",
        "group": "PR Ailesi",
        "desc": "PR + Danesh düzeltmesi (rezervuar)",
        "multiphase": False,
        "supports_aga8": False,
    },
    "neqsim-srk-cpa": {
        "class": "SystemSrkCPAstatoil",
        "mixing": 10,
        "group": "CPA",
        "desc": "SRK-CPA (Equinor) - su/hidrokarbon/hidrat/glikol",
        "multiphase": True,
        "supports_aga8": False,
    },
    "neqsim-soreide": {
        "class": "SystemSoreideWhitson",
        "mixing": 11,
        "group": "Ekşi Gaz",
        "desc": "Søreide-Whitson - ekşi gaz + tuzlu su",
        "multiphase": True,
        "supports_aga8": False,
    },
    "neqsim-gerg2008": {
        "class": "SystemGERG2008Eos",
        "mixing": None,
        "group": "Referans EOS",
        "desc": "GERG-2008 (ISO 20765-2) - 21 bileşen, yüksek hassasiyet",
        "multiphase": False,
        "supports_aga8": True,
    },
    "neqsim-gerg2008-h2": {
        "class": "SystemGERG2008Eos",
        "mixing": None,
        "group": "Referans EOS",
        "desc": "GERG-2008-H2 - hidrojen katkılı doğal gaz",
        "multiphase": False,
        "supports_aga8": True,
        "h2_enhanced": True,
    },
    "neqsim-eoscg": {
        "class": "SystemEOSCGEos",
        "mixing": None,
        "group": "Referans EOS",
        "desc": "EOS-CG - CCS (CO2 + SO2/NO/HCl/Cl2)",
        "multiphase": False,
        "supports_aga8": True,
    },
    "neqsim-spanwagner": {
        "class": "SystemSpanWagnerEos",
        "mixing": None,
        "group": "Referans EOS",
        "desc": "Span-Wagner - saf CO2",
        "multiphase": False,
        "supports_aga8": False,
    },
    "neqsim-umrpru": {
        "class": "SystemUMRPRUMCEos",
        "mixing": "no",
        "group": "Tahminsel",
        "desc": "UMR-PRU - tahminsel, etkileşim parametresi gerekmez",
        "multiphase": False,
        "supports_aga8": False,
    },
}

NEQSIM_AVAILABLE_BACKENDS = list(NEQSIM_EOS_REGISTRY.keys())


def _get_neqsim_gas_name(coolprop_name: str) -> str:
    import re
    clean = re.sub(r'\s+', '', coolprop_name.strip()).lower()
    return NEQSIM_GAS_MAPPING.get(clean, clean)


def calculate_neqsim(
    mixture,
    temperature_k: float,
    pressure_pa: float,
    method: str = "neqsim-gerg2008",
) -> Tuple[ActualConditionResults, Optional[TransportProperties]]:
    """
    Calculate thermodynamic properties using NeqSim with the specified EOS.

    Args:
        mixture: GasMixture instance with component fractions.
        temperature_k: Temperature in Kelvin.
        pressure_pa: Pressure in Pascals.
        method: NeqSim backend name (e.g., "neqsim-gerg2008", "neqsim-srk", etc.)

    Returns:
        Tuple of (ActualConditionResults, TransportProperties or None).

    Raises:
        BackendNotAvailableError: If NeqSim is not installed/JVM not available.
        ValueError: If method is unknown or property extraction fails.
    """
    if not NEQSIM_AVAILABLE:
        raise BackendNotAvailableError(f"NeqSim ({method})")

    logger = logging.getLogger(__name__)

    if method not in NEQSIM_EOS_REGISTRY:
        raise ValueError(
            f"Bilinmeyen NeqSim metodu '{method}'. "
            f"Kullanılabilir: {', '.join(NEQSIM_AVAILABLE_BACKENDS)}"
        )

    eos_info = NEQSIM_EOS_REGISTRY[method]
    class_name = eos_info["class"]
    mixing_rule = eos_info["mixing"]
    is_multiphase = eos_info["multiphase"]
    is_h2_enhanced = eos_info.get("h2_enhanced", False)
    is_reference = eos_info["group"] == "Referans EOS"

    try:
        eos_cls = getattr(_jneqsim.thermo.system, class_name)
    except AttributeError:
        raise BackendNotAvailableError(
            f"NeqSim sınıfı '{class_name}' bulunamadı. "
            "NeqSim sürümünüz bu EOS'u desteklemiyor olabilir."
        )

    try:
        fluid = eos_cls(temperature_k, pressure_pa / 1e5)

        for comp in mixture.components:
            coolprop_name = mixture._format_gas_name_for_coolprop(comp.name).lower()
            neqsim_name = _get_neqsim_gas_name(coolprop_name)
            fraction_decimal = comp.fraction / 100.0
            try:
                fluid.addComponent(neqsim_name, fraction_decimal)
            except Exception as exc:
                logger.warning(
                    f"NeqSim {neqsim_name} bileşeni eklenemedi: {exc}"
                )
                if is_reference:
                    raise ValueError(
                        f"Referans EOS '{method}' '{neqsim_name}' desteklemiyor."
                    )

        if mixing_rule is not None and mixing_rule != "no":
            try:
                fluid.setMixingRule(mixing_rule)
            except Exception as exc:
                logger.warning(f"Mixing rule {mixing_rule} ayarlanamadı: {exc}")

        if is_multiphase:
            try:
                fluid.setMultiPhaseCheck(True)
            except Exception as exc:
                logger.debug(f"setMultiPhaseCheck(True) failed: {exc}")

        if is_h2_enhanced:
            try:
                fluid.useHydrogenEnhancedModel()
            except Exception as exc:
                logger.debug(f"useHydrogenEnhancedModel() failed: {exc}")

        try:
            fluid.createDatabase(True)
        except Exception as exc:
            logger.debug(f"createDatabase(True) failed: {exc}")

        ops = _jneqsim.thermodynamicoperations.ThermodynamicOperations(fluid)
        ops.TPflash()

        try:
            fluid.initProperties()
        except Exception as exc:
            logger.debug(f"initProperties() failed: {exc}")

        try:
            fluid.initPhysicalProperties()
        except Exception as exc:
            logger.debug(f"initPhysicalProperties() failed: {exc}")

        phase = fluid.getPhase(0)

        density = float(phase.getDensity("kg/m3"))
        molar_mass = float(phase.getMolarMass())
        if molar_mass < 0.001:
            molar_mass = 0.016

        try:
            z_factor = float(fluid.getZ())
            if math.isnan(z_factor) or z_factor <= 0:
                z_factor = float(phase.getZ())
        except Exception as exc:
            logger.debug(f"fluid.getZ() failed: {exc}")
            z_factor = float(phase.getZ())

        h = float(phase.getEnthalpy("kJ/kg")) if hasattr(phase, 'getEnthalpy') else float(fluid.getEnthalpy("kJ/kg"))
        s = float(phase.getEntropy("kJ/kgK")) if hasattr(phase, 'getEntropy') else float(fluid.getEntropy("kJ/kgK"))
        u = float(phase.getInternalEnergy("kJ/kg")) if hasattr(phase, 'getInternalEnergy') else math.nan

        cp = float(phase.getCp("kJ/kgK")) if hasattr(phase, 'getCp') else float(fluid.getCp("kJ/kgK"))
        cv = float(phase.getCv("kJ/kgK")) if hasattr(phase, 'getCv') else float(fluid.getCv("kJ/kgK"))

        kappa = None
        try:
            if hasattr(phase, 'getGamma'):
                kappa = float(phase.getGamma())
            elif cp > 0 and cv > 0:
                kappa = cp / cv
        except Exception as exc:
            logger.debug(f"isentropic exponent extraction failed: {exc}")

        speed = None
        try:
            speed = float(phase.getSoundSpeed())
        except Exception as exc:
            logger.debug(f"sound speed extraction failed: {exc}")

        # --- Transport properties ---
        transport = TransportProperties()

        try:
            vis = float(phase.getViscosity("cP"))
            transport.viscosity_cp = vis if vis > 0 else None
        except Exception as exc:
            logger.debug(f"viscosity extraction failed: {exc}")

        try:
            tc = float(phase.getThermalConductivity("W/mK"))
            transport.thermal_conductivity = tc if tc > 0 else None
        except Exception as exc:
            logger.debug(f"thermal conductivity extraction failed: {exc}")

        try:
            jt = float(phase.getJouleThomsonCoefficient())
            transport.joule_thomson_coefficient = jt
        except Exception as exc:
            logger.debug(f"Joule-Thomson extraction failed: {exc}")

        try:
            st = float(fluid.getInterphaseProperties().getSurfaceTension(0, 1))
            transport.surface_tension = st if st > 0 else None
        except Exception as exc:
            logger.debug(f"surface tension extraction failed: {exc}")

        # --- Phase info for multiphase (CPA) ---
        transport.has_aqueous_phase = False
        transport.has_liquid_hc_phase = False
        try:
            transport.has_aqueous_phase = fluid.hasPhaseType("aqueous")
            transport.has_liquid_hc_phase = fluid.hasPhaseType("oil")
        except Exception as exc:
            logger.debug(f"phase type detection failed: {exc}")

        actual = ActualConditionResults(
            temperature=temperature_k,
            pressure=pressure_pa,
            density=density,
            molar_mass=molar_mass,
            compressibility_factor=z_factor,
            internal_energy=u,
            enthalpy=h,
            entropy=s,
            cp=cp,
            cv=cv,
            isentropic_exponent=kappa,
            speed_of_sound=speed,
        )

        return actual, transport

    except BackendNotAvailableError:
        raise
    except ValueError as e:
        if "desteklemiyor" in str(e):
            raise
        raise ValueError(f"NeqSim {method} hesaplama hatası: {e}")
    except Exception as e:
        raise RuntimeError(f"NeqSim {method} başarısız: {e}")


def get_neqsim_iso6976(mixture, temperature_ref_k: float = 288.15) -> Optional[Dict[str, float]]:
    """
    Calculate ISO 6976 gas quality parameters using NeqSim.

    Args:
        mixture: GasMixture instance.
        temperature_ref_k: Reference temperature in Kelvin (default 288.15 = 15C).

    Returns:
        Dict with keys: gcv_kj_m3, lcv_kj_m3, wobbe_kj_m3, relative_density,
        compressibility_factor, molar_mass_g_mol, density_real, density_ideal
        or None if calculation fails.
    """
    if not NEQSIM_AVAILABLE:
        return None

    logger = logging.getLogger(__name__)
    try:
        from neqsim.thermo import fluid as nqfluid, TPflash as nqTPflash

        nqf = nqfluid("gerg-2008")
        nqf.setTemperature(temperature_ref_k - 273.15, "C")
        nqf.setPressure(1.01325, "bara")

        for comp in mixture.components:
            coolprop_name = mixture._format_gas_name_for_coolprop(comp.name).lower()
            neqsim_name = _get_neqsim_gas_name(coolprop_name)
            nqf.addComponent(neqsim_name, comp.fraction, "mol/sec")

        nqTPflash(nqf)

        gas_system = nqf.getSystem()
        t_ref_c = round(temperature_ref_k - 273.15, 2)
        iso = _jneqsim.standards.gasquality.Standard_ISO6976(gas_system, t_ref_c, t_ref_c, "volume")
        iso.calculate()

        return {
            "gcv_kj_m3": float(iso.getValue("GCV")),
            "lcv_kj_m3": float(iso.getValue("LCV")),
            "wobbe_kj_m3": float(iso.getValue("SuperiorWobbeIndex")),
            "relative_density": float(iso.getValue("RelativeDensity")),
            "compressibility_factor": float(iso.getValue("CompressionFactor")),
            "molar_mass_g_mol": float(iso.getValue("MolarMass")),
            "density_real": float(iso.getValue("DensityReal")),
            "density_ideal": float(iso.getValue("DensityIdeal")),
        }
    except Exception as e:
        logger.warning(f"NeqSim ISO 6976 hesaplaması başarısız: {e}")
        return None


def get_neqsim_hydrate_temperature(
    mixture,
    temperature_k: float,
    pressure_pa: float,
) -> Optional[float]:
    """
    Calculate hydrate formation temperature using NeqSim's CPA-based model.

    Args:
        mixture: GasMixture instance.
        temperature_k: Operating temperature (K).
        pressure_pa: Operating pressure (Pa).

    Returns:
        Hydrate formation temperature in Kelvin, or None if calculation fails.
    """
    if not NEQSIM_AVAILABLE:
        return None

    logger = logging.getLogger(__name__)
    try:
        fluid = _jneqsim.thermo.system.SystemSrkCPAstatoil(temperature_k, pressure_pa / 1e5)

        for comp in mixture.components:
            coolprop_name = mixture._format_gas_name_for_coolprop(comp.name).lower()
            neqsim_name = _get_neqsim_gas_name(coolprop_name)
            fluid.addComponent(neqsim_name, comp.fraction / 100.0)

        fluid.setMixingRule(10)
        fluid.setMultiPhaseCheck(True)

        ops = _jneqsim.thermodynamicoperations.ThermodynamicOperations(fluid)
        initial_temp = float(fluid.getTemperature())
        ops.hydrateFormationTemperature()
        final_temp = float(fluid.getTemperature())

        if abs(final_temp - initial_temp) < 0.01:
            logger.debug(
                f"Hidrat sıcaklığı yakınsamadı (T={initial_temp:.2f}K → {final_temp:.2f}K)"
            )
            return None

        return final_temp
    except Exception as e:
        logger.warning(f"NeqSim hidrat sıcaklığı hesaplanamadı: {e}")
        return None
