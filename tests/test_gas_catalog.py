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


def test_industry_abbreviations_map_to_coolprop_names():
    """Verify common chromatography abbreviations resolve correctly."""
    cases = [
        ("CO2", "CarbonDioxide"),
        ("H2S", "HydrogenSulfide"),
        ("N2", "Nitrogen"),
        ("O2", "Oxygen"),
        ("H2", "Hydrogen"),
        ("H2O", "Water"),
        ("C1", "Methane"),
        ("C2", "Ethane"),
        ("C3", "n-Propane"),
        ("iC4", "IsoButane"),
        ("nC4", "n-Butane"),
        ("iC5", "Isopentane"),
        ("nC5", "n-Pentane"),
        ("C6", "n-Hexane"),
        ("C7", "n-Heptane"),
        ("C8", "n-Octane"),
        ("C9", "n-Nonane"),
        ("C10", "n-Decane"),
        ("He", "Helium"),
        ("Ar", "Argon"),
        ("CO", "CarbonMonoxide"),
    ]
    for abbr, expected_coolprop in cases:
        result = GasMixture._format_gas_name_for_coolprop(abbr)
        assert result == expected_coolprop, (
            f"Abbreviation '{abbr}' → '{result}', expected '{expected_coolprop}'"
        )


def test_abbreviation_mixture_works_with_coolprop_string():
    """A mixture using abbreviations should produce valid CoolProp string."""
    mixture = GasMixture(
        components=[
            GasComponent(name="C1", fraction=90.0),
            GasComponent(name="C2", fraction=5.0),
            GasComponent(name="CO2", fraction=3.0),
            GasComponent(name="N2", fraction=2.0),
        ]
    )
    assert mixture.to_coolprop_string() == "Methane&Ethane&CarbonDioxide&Nitrogen"
    assert mixture.check_heos_compatibility() == []
