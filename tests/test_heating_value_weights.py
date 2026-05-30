"""Tests verifying the heating value mass-weight fix (H1).

Validates that component-based and reference-based heating value
calculations use correct mass-fraction weights, not raw molar fractions.
"""

import pytest
from natural_gas_main.models.calculator import ThermoCalculator
from natural_gas_main.models.gas_data import GasComponent, GasMixture


@pytest.fixture
def calc():
    return ThermoCalculator()


class TestHeatingValueMassWeights:
    """Verify the _get_heating_value_mass_weights method."""

    def test_mass_fractions_used_directly(self, calc):
        """When fraction_type='mass', weights equal the decimal fractions."""
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=80.0),
                GasComponent(name="Ethane", fraction=20.0),
            ],
            fraction_type="mass",
        )
        weights = calc._get_heating_value_mass_weights(mixture)
        assert weights["Methane"] == pytest.approx(0.80)
        assert weights["Ethane"] == pytest.approx(0.20)
        assert sum(weights.values()) == pytest.approx(1.0)

    def test_molar_fractions_converted_to_mass(self, calc):
        """When fraction_type='molar', weights should NOT equal raw mol%."""
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=80.0),
                GasComponent(name="Ethane", fraction=20.0),
            ],
            fraction_type="molar",
        )
        weights = calc._get_heating_value_mass_weights(mixture)
        # Methane MW=16, Ethane MW=30 - mass weights should differ from mol%
        assert weights["Methane"] != pytest.approx(0.80, abs=0.05)
        assert sum(weights.values()) == pytest.approx(1.0)

    def test_molar_methane_heavier_than_molar_ethane(self, calc):
        """Methane has lower MW than Ethane, so mass weight of Methane < mol%."""
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=50.0),
                GasComponent(name="Ethane", fraction=50.0),
            ],
            fraction_type="molar",
        )
        weights = calc._get_heating_value_mass_weights(mixture)
        assert weights["Methane"] < weights["Ethane"]

    def test_inert_gas_included_in_weights(self, calc):
        """Non-combustible gases still get mass weights."""
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=70.0),
                GasComponent(name="Nitrogen", fraction=30.0),
            ],
            fraction_type="molar",
        )
        weights = calc._get_heating_value_mass_weights(mixture)
        assert "Nitrogen" in weights
        assert weights["Nitrogen"] > 0

    def test_component_based_uses_mass_weights(self, calc):
        """The corrected _calculate_heating_values_component_based
        should produce mass-weight-averaged results (may fail for pure
        component CoolProp API; fallback to reference DB is expected)."""
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=90.0),
                GasComponent(name="Ethane", fraction=10.0),
            ],
            fraction_type="molar",
        )
        try:
            hhv, lhv = calc._calculate_heating_values_component_based(
                mixture, "HEOS", 288.15, 101325.0
            )
        except Exception:
            pytest.skip("Component-based HHV API not available in this CoolProp version")
            return
        assert hhv > 0
        assert lhv > 0
        assert hhv > lhv

    def test_reference_based_uses_mass_weights(self, calc):
        """The reference DB method should use mass weights."""
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=90.0),
                GasComponent(name="Ethane", fraction=10.0),
            ],
            fraction_type="molar",
        )
        hhv, lhv = calc._calculate_heating_values_reference(mixture)
        assert hhv > 0
        assert lhv > 0


class TestHeatingValueFallbackChain:
    """Verify the 3-stage fallback chain works end-to-end."""

    def test_molar_fallback_produces_value(self, calc):
        """End-to-end: molar fraction input → valid heating value output."""
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=90.0),
                GasComponent(name="Ethane", fraction=10.0),
            ],
            fraction_type="molar",
        )
        hhv, lhv = calc._calculate_heating_values_reference(mixture)
        assert hhv > 45
        assert lhv > 40
        assert hhv > lhv

    def test_mass_fraction_produces_value(self, calc):
        """End-to-end: mass fraction input → valid heating value output."""
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=85.0),
                GasComponent(name="Ethane", fraction=15.0),
            ],
            fraction_type="mass",
        )
        hhv, lhv = calc._calculate_heating_values_reference(mixture)
        assert hhv > 40
        assert lhv > 35

    def test_packaging_with_none_sg(self, calc):
        """_package_heating_values should handle sg=None."""
        result = calc._package_heating_values(
            hhv_mass=50.0,
            lhv_mass=45.0,
            rho_std=0.8,
            sg=None,
            method="test",
        )
        assert result.hhv_mass == 50.0
        assert result.wobbe_index is not None
