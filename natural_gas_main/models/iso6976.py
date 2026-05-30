"""
ISO 6976:2016 — Natural gas — Calculation of calorific values.

Provides stoichiometric HHV/LHV calculation per the international standard.
Values are at combustion reference temperature 25 °C (298.15 K) by default,
with optional temperature correction factors.

Components not in this database fall back to the CoolProp component-based
method; the caller is responsible for the fallback chain.
"""

ISO6976_DATA = {
    "Methane": {
        "hhv_mass": 55.575,
        "lhv_mass": 50.046,
        "hhv_vol": 37.706,
        "lhv_vol": 33.948,
        "density_ideal": 0.6784,
    },
    "Ethane": {
        "hhv_mass": 51.951,
        "lhv_mass": 47.521,
        "hhv_vol": 66.065,
        "lhv_vol": 60.423,
        "density_ideal": 1.2719,
    },
    "Propane": {
        "hhv_mass": 50.368,
        "lhv_mass": 46.333,
        "hhv_vol": 95.164,
        "lhv_vol": 87.536,
        "density_ideal": 1.8902,
    },
    "n-Propane": {
        "hhv_mass": 50.368,
        "lhv_mass": 46.333,
        "hhv_vol": 95.164,
        "lhv_vol": 87.536,
        "density_ideal": 1.8902,
    },
    "n-Butane": {
        "hhv_mass": 49.546,
        "lhv_mass": 45.724,
        "hhv_vol": 123.838,
        "lhv_vol": 114.334,
        "density_ideal": 2.5100,
    },
    "IsoButane": {
        "hhv_mass": 49.416,
        "lhv_mass": 45.594,
        "hhv_vol": 123.413,
        "lhv_vol": 113.872,
        "density_ideal": 2.5072,
    },
    "n-Pentane": {
        "hhv_mass": 49.011,
        "lhv_mass": 45.367,
        "hhv_vol": 153.065,
        "lhv_vol": 141.865,
        "density_ideal": 3.1259,
    },
    "Isopentane": {
        "hhv_mass": 48.939,
        "lhv_mass": 45.295,
        "hhv_vol": 152.520,
        "lhv_vol": 141.167,
        "density_ideal": 3.1184,
    },
    "n-Hexane": {
        "hhv_mass": 48.704,
        "lhv_mass": 45.105,
        "hhv_vol": 182.976,
        "lhv_vol": 169.500,
        "density_ideal": 3.7610,
    },
    "n-Heptane": {
        "hhv_mass": 48.445,
        "lhv_mass": 44.887,
        "hhv_vol": 212.631,
        "lhv_vol": 197.011,
        "density_ideal": 4.3915,
    },
    "n-Octane": {
        "hhv_mass": 48.227,
        "lhv_mass": 44.715,
        "hhv_vol": 237.220,
        "lhv_vol": 219.887,
        "density_ideal": 4.9202,
    },
    "Nitrogen": {
        "hhv_mass": 0.0,
        "lhv_mass": 0.0,
        "hhv_vol": 0.0,
        "lhv_vol": 0.0,
        "density_ideal": 1.1651,
    },
    "CarbonDioxide": {
        "hhv_mass": 0.0,
        "lhv_mass": 0.0,
        "hhv_vol": 0.0,
        "lhv_vol": 0.0,
        "density_ideal": 1.8299,
    },
    "Hydrogen": {
        "hhv_mass": 141.771,
        "lhv_mass": 119.956,
        "hhv_vol": 12.737,
        "lhv_vol": 10.780,
        "density_ideal": 0.08994,
    },
    "CarbonMonoxide": {
        "hhv_mass": 10.100,
        "lhv_mass": 10.100,
        "hhv_vol": 12.636,
        "lhv_vol": 12.636,
        "density_ideal": 1.2504,
    },
    "HydrogenSulfide": {
        "hhv_mass": 16.495,
        "lhv_mass": 15.192,
        "hhv_vol": 23.788,
        "lhv_vol": 21.910,
        "density_ideal": 1.5248,
    },
}

_COOLPROP_TO_ISO = {
    "methane": "Methane",
    "ethane": "Ethane",
    "propane": "Propane",
    "n-propane": "n-Propane",
    "n-butane": "n-Butane",
    "isobutane": "IsoButane",
    "n-pentane": "n-Pentane",
    "isopentane": "Isopentane",
    "n-hexane": "n-Hexane",
    "n-heptane": "n-Heptane",
    "n-octane": "n-Octane",
    "nitrogen": "Nitrogen",
    "carbondioxide": "CarbonDioxide",
    "hydrogen": "Hydrogen",
    "carbonmonoxide": "CarbonMonoxide",
    "hydrogensulfide": "HydrogenSulfide",
}


def calculate_iso6976_heating_values(
    mixture,
    format_name_func=None,
    T_ref: float = 298.15,
) -> tuple[float, float] | tuple[None, None]:
    """Calculate HHV and LHV per ISO 6976:2016 stoichiometric method.

    Args:
        mixture: GasMixture with components and fraction_type
        format_name_func: Function to format gas name to CoolProp name
        T_ref: Combustion reference temperature (K).
                ISO 6976 specifies 25 °C = 298.15 K.

    Returns:
        (HHV_mass_MJ_kg, LHV_mass_MJ_kg) or (None, None) if not all
        components are in the database.
    """
    if format_name_func is None:
        try:
            from natural_gas_main.models.gas_data import GasMixture
            format_name_func = GasMixture._format_gas_name_for_coolprop
        except Exception:
            format_name_func = lambda x: x

    weights = _get_mass_weights(mixture, format_name_func)
    if weights is None:
        return None, None

    hhv_total = 0.0
    lhv_total = 0.0
    found_count = 0

    for component in mixture.components:
        cp_name = format_name_func(component.name).lower()
        iso_name = _COOLPROP_TO_ISO.get(cp_name)
        if iso_name is None or iso_name not in ISO6976_DATA:
            return None, None

        data = ISO6976_DATA[iso_name]
        weight = weights.get(component.name, 0.0)
        if weight <= 0:
            continue

        hhv_total += weight * data["hhv_mass"]
        lhv_total += weight * data["lhv_mass"]
        found_count += 1

    if found_count == 0:
        return None, None

    if hhv_total < 1e-6:
        return 0.0, 0.0

    if abs(T_ref - 298.15) > 5.0:
        ratio = T_ref / 298.15
        hhv_total *= ratio
        lhv_total *= ratio

    return hhv_total, lhv_total


def _get_mass_weights(mixture, format_name_func) -> dict | None:
    """Return mass-fraction weights for each component."""
    if mixture.fraction_type == "mass":
        return {
            c.name: c.to_decimal()
            for c in mixture.components
        }

    weighted = {}
    total = 0.0
    try:
        import CoolProp.CoolProp as CP
    except Exception:
        return None

    for component in mixture.components:
        cp_name = format_name_func(component.name)
        try:
            mw = CP.PropsSI("M", cp_name)
        except Exception:
            return None
        wm = component.to_decimal() * mw
        weighted[component.name] = wm
        total += wm

    if total <= 0:
        return None
    return {k: v / total for k, v in weighted.items()}


def is_iso6976_compatible(mixture, format_name_func=None) -> bool:
    """Check if all mixture components have ISO 6976 data."""
    if format_name_func is None:
        try:
            from natural_gas_main.models.gas_data import GasMixture
            format_name_func = GasMixture._format_gas_name_for_coolprop
        except Exception:
            format_name_func = lambda x: x

    for component in mixture.components:
        cp_name = format_name_func(component.name).lower()
        iso_name = _COOLPROP_TO_ISO.get(cp_name)
        if iso_name is None or iso_name not in ISO6976_DATA:
            return False
    return True
