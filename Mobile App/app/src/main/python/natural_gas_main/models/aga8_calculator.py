"""
AGA8 (GERG-2008 / AGA8-Detail) calculation module.

Delegates natural gas property calculations to the pyaga8 library.
Kept separate from the main ThermoCalculator to maintain modularity
and reduce file size.
"""

from __future__ import annotations

import logging
import os
from typing import Dict

from natural_gas_main.models.calculation_result import ActualConditionResults
from natural_gas_main.core.exceptions import BackendNotAvailableError

PYAGA8_AVAILABLE = False

try:
    import pyaga8
    PYAGA8_AVAILABLE = True
    logging.info("pyaga8 başarıyla yüklendi")
except ImportError as e:
    logging.error(f"pyaga8 içe aktarılamadı: {e}")

AGA8_MAPPING: Dict[str, str] = {
    "methane": "methane",
    "ethane": "ethane",
    "n-propane": "propane",
    "propane": "propane",
    "n-butane": "n_butane",
    "isobutane": "isobutane",
    "n-pentane": "n_pentane",
    "isopentane": "isopentane",
    "n-hexane": "hexane",
    "n-heptane": "heptane",
    "n-octane": "octane",
    "n-nonane": "nonane",
    "n-decane": "decane",
    "hydrogen": "hydrogen",
    "oxygen": "oxygen",
    "carbonmonoxide": "carbon_monoxide",
    "water": "water",
    "hydrogensulfide": "hydrogen_sulfide",
    "helium": "helium",
    "argon": "argon",
    "carbondioxide": "carbon_dioxide",
    "nitrogen": "nitrogen",
}


def calculate_aga8(
    mixture,
    temperature_k: float,
    pressure_pa: float,
    method: str = "GERG-2008",
) -> ActualConditionResults:
    """
    Calculate thermodynamic properties using AGA8-based methods.

    Args:
        mixture: GasMixture instance with component fractions.
        temperature_k: Temperature in Kelvin.
        pressure_pa: Pressure in Pascals.
        method: "GERG-2008" or "AGA8-Detail".

    Returns:
        ActualConditionResults with density, Z, enthalpy etc.

    Raises:
        BackendNotAvailableError: If pyaga8 is not installed.
        ValueError: If total valid AGA8 fraction < 0.99.
    """
    if not PYAGA8_AVAILABLE:
        raise BackendNotAvailableError(method)

    logger = logging.getLogger(__name__)

    if method not in ("GERG-2008", "AGA8-Detail"):
        logger.warning(
            f"Bilinmeyen AGA8 metodu '{method}', AGA8-Detail kullanılıyor."
        )
        method = "AGA8-Detail"

    comp = pyaga8.Composition()

    sum_fractions = 0.0
    mapped_count = 0
    unmapped_gases = []
    for gas in mixture.components:
        coolprop_name = mixture._format_gas_name_for_coolprop(gas.name).lower()
        aga8_name = AGA8_MAPPING.get(coolprop_name)
        if aga8_name:
            val = gas.fraction / 100.0
            setattr(comp, aga8_name, val)
            sum_fractions += val
            mapped_count += 1
        else:
            unmapped_gases.append(gas.name)
            logger.warning(
                f"Bileşen {gas.name} AGA8 standardında desteklenmiyor. Yoksayılıyor."
            )

    if sum_fractions < 0.95:
        raise ValueError(
            f"AGA8 için geçerli gazların toplamı {sum_fractions} (< 0.95). "
            f"Atlanan bileşenler: {', '.join(unmapped_gases)}. AGA8 kullanılamaz."
        )

    if unmapped_gases and sum_fractions >= 0.95:
        logger.warning(
            f"AGA8'de tanınmayan eser bileşenler: {', '.join(unmapped_gases)}. "
            f"Bunlar yoksayılacak, kalan oranlar yeniden ölçeklenecek."
        )
        # Do NOT raise — rescale below like the normal 1e-5 path

    if abs(sum_fractions - 1.0) > 1e-5:
        for gas in mixture.components:
            coolprop_name = mixture._format_gas_name_for_coolprop(gas.name).lower()
            aga8_name = AGA8_MAPPING.get(coolprop_name)
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

    # Redirect fd 2 to suppress Rust panic messages from pyaga8
    old_fd = os.dup(2)
    devnull_fd = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull_fd, 2)
    os.close(devnull_fd)
    try:
        if method == "GERG-2008":
            engine.calc_density(0)
        else:
            engine.calc_density()
        engine.calc_properties()
    except BaseException as e:
        raise ValueError(
            f"AGA8 {method} density calculation failed at "
            f"T={temperature_k} K, P={pressure_pa} Pa: {e}"
        ) from e
    finally:
        os.dup2(old_fd, 2)
        os.close(old_fd)

    return ActualConditionResults(
        temperature=temperature_k,
        pressure=pressure_pa,
        density=engine.d * engine.mm,
        molar_mass=engine.mm / 1000.0,
        compressibility_factor=engine.z,
        internal_energy=engine.u / engine.mm,
        enthalpy=engine.h / engine.mm,
        entropy=engine.s / engine.mm,
        cp=engine.cp / engine.mm,
        cv=engine.cv / engine.mm,
        isentropic_exponent=engine.kappa,
        speed_of_sound=engine.w,
    )
