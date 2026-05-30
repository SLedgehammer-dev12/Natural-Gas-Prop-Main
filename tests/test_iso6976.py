"""Tests for ISO 6976:2016 heating value module."""

import pytest
from natural_gas_main.models.gas_data import GasComponent, GasMixture
from natural_gas_main.models import iso6976


def test_pure_methane():
    mixture = GasMixture(
        components=[GasComponent(name="Methane", fraction=100.0)],
        fraction_type="molar",
    )
    hhv, lhv = iso6976.calculate_iso6976_heating_values(mixture)
    assert hhv == pytest.approx(55.575, rel=0.01)
    assert lhv == pytest.approx(50.046, rel=0.01)


def test_two_component():
    mixture = GasMixture(
        components=[
            GasComponent(name="Methane", fraction=90.0),
            GasComponent(name="Ethane", fraction=10.0),
        ],
        fraction_type="molar",
    )
    hhv, lhv = iso6976.calculate_iso6976_heating_values(mixture)
    assert hhv > 0
    assert lhv > 0
    assert hhv > lhv


def test_mass_fraction():
    mixture = GasMixture(
        components=[
            GasComponent(name="Methane", fraction=80.0),
            GasComponent(name="Ethane", fraction=20.0),
        ],
        fraction_type="mass",
    )
    hhv, lhv = iso6976.calculate_iso6976_heating_values(mixture)
    assert hhv > 0
    assert lhv > 0


def test_inert_only():
    mixture = GasMixture(
        components=[GasComponent(name="Nitrogen", fraction=100.0)],
        fraction_type="molar",
    )
    hhv, lhv = iso6976.calculate_iso6976_heating_values(mixture)
    assert hhv == 0.0
    assert lhv == 0.0


def test_unknown_component_returns_none():
    mixture = GasMixture(
        components=[GasComponent(name="Unobtanium", fraction=100.0)],
        fraction_type="molar",
    )
    hhv, lhv = iso6976.calculate_iso6976_heating_values(mixture)
    assert hhv is None
    assert lhv is None


def test_compatibility_check():
    valid = GasMixture(
        components=[
            GasComponent(name="Methane", fraction=90.0),
            GasComponent(name="Ethane", fraction=10.0),
        ],
        fraction_type="molar",
    )
    assert iso6976.is_iso6976_compatible(valid) is True

    invalid = GasMixture(
        components=[GasComponent(name="Unobtanium", fraction=100.0)],
        fraction_type="molar",
    )
    assert iso6976.is_iso6976_compatible(invalid) is False


def test_propane_aliases():
    mixture = GasMixture(
        components=[GasComponent(name="Propane", fraction=100.0)],
        fraction_type="molar",
    )
    hhv, lhv = iso6976.calculate_iso6976_heating_values(mixture)
    assert hhv is not None
    assert lhv is not None


def test_hydrogen_sulfide():
    mixture = GasMixture(
        components=[GasComponent(name="HydrogenSulfide", fraction=100.0)],
        fraction_type="molar",
    )
    hhv, lhv = iso6976.calculate_iso6976_heating_values(mixture)
    assert hhv == pytest.approx(16.495, rel=0.01)
    assert lhv == pytest.approx(15.192, rel=0.01)
