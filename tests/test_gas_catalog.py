from natural_gas_main.config.settings import config
from natural_gas_main.models.gas_data import GasComponent, GasMixture
from natural_gas_main.models.heating_value_db import get_reference_heating_values


def test_natural_gas_focus_catalog_contains_expected_components():
    expected = {
        "Methane",
        "Ethane",
        "Propane",
        "n-Propane",
        "n-Butane",
        "IsoButane",
        "n-Pentane",
        "Nitrogen",
        "CarbonDioxide",
        "HydrogenSulfide",
        "CarbonylSulfide",
        "Hydrogen",
        "Helium",
    }
    assert expected.issubset(set(config.NATURAL_GAS_FOCUS_LIST))


def test_common_display_names_map_to_coolprop_names():
    mixture = GasMixture(
        components=[
            GasComponent(name="Propane", fraction=40.0),
            GasComponent(name="isobutane", fraction=30.0),
            GasComponent(name="Carbon Dioxide", fraction=30.0),
        ]
    )

    assert mixture.to_coolprop_string() == "n-Propane&IsoButane&CarbonDioxide"
    assert mixture.check_heos_compatibility() == []


def test_reference_heating_values_support_aliases():
    assert get_reference_heating_values("Propane") == get_reference_heating_values("n-Propane")
    assert get_reference_heating_values("Isobutane") == get_reference_heating_values("IsoButane")
