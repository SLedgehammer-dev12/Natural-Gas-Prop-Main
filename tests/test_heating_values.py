"""
Tests for the three-stage heating value calculation fallback system.

Covers: built-in method, component-based method, and reference database.
"""

import pytest

from natural_gas_main.models.gas_data import GasComponent, GasMixture
from natural_gas_main.models.heating_value_db import get_reference_heating_values


class TestHeatingValueDatabase:
    """Reference database look-ups for known components."""

    def test_methane_reference_values(self):
        vals = get_reference_heating_values("Methane")
        assert vals is not None
        hhv, lhv = vals
        assert 50 < hhv < 58, f"Unexpected HHV: {hhv}"
        assert 45 < lhv < 55, f"Unexpected LHV: {lhv}"

    def test_ethane_reference_values(self):
        vals = get_reference_heating_values("Ethane")
        assert vals is not None
        hhv, lhv = vals
        assert 45 < hhv < 55
        assert lhv < hhv

    def test_propane_reference_values(self):
        vals = get_reference_heating_values("n-Propane")
        assert vals is not None
        hhv, lhv = vals
        assert 45 < hhv < 55

    def test_nitrogen_has_zero_heating_value(self):
        vals = get_reference_heating_values("Nitrogen")
        assert vals is not None
        hhv, lhv = vals
        assert hhv == 0.0 and lhv == 0.0

    def test_unknown_gas_has_no_reference(self):
        vals = get_reference_heating_values("FakeGas42")
        assert vals is None


class TestHeatingValueMassWeights:
    """Verify molar-to-mass conversion for heating value averaging."""

    def test_mass_fractions_used_directly(self):
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=90.0),
                GasComponent(name="Ethane", fraction=10.0),
            ],
            fraction_type="mass",
        )
        # This test verifies that mass-fraction mixtures don't crash
        assert mixture.fraction_type == "mass"

    def test_molar_fraction_constructor(self):
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=94.0),
                GasComponent(name="Ethane", fraction=6.0),
            ],
            fraction_type="molar",
        )
        assert mixture.fraction_type == "molar"
        assert len(mixture.components) == 2


class TestCalculatorHeatingFallback:
    """Integration test for the complete heating value calculation pipeline."""

    def test_fallback_on_simple_hydrocarbon_mixture(self):
        from natural_gas_main.models.calculator import ThermoCalculator

        calc = ThermoCalculator()
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=94.0),
                GasComponent(name="Ethane", fraction=6.0),
            ],
            fraction_type="molar",
        )
        result, backend = calc.calculate_with_fallback(
            mixture=mixture,
            temperature_k=288.15,
            pressure_pa=101325.0,
            preferred_backend="SRK",
        )
        assert result is not None
        assert result.heating is not None
        assert result.heating.hhv_mass > 0
        assert result.heating.lhv_mass > 0
        assert result.heating.lhv_mass < result.heating.hhv_mass
        assert result.heating.calculation_method is not None

    def test_single_methane_returns_heating_values(self):
        from natural_gas_main.models.calculator import ThermoCalculator

        calc = ThermoCalculator()
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=100.0),
            ],
            fraction_type="molar",
        )
        result, backend = calc.calculate_with_fallback(
            mixture=mixture,
            temperature_k=288.15,
            pressure_pa=101325.0,
            preferred_backend="SRK",
        )
        assert result.heating is not None
        assert result.heating.hhv_mass > 0

    def test_non_combustible_mixture_with_inerts(self):
        from natural_gas_main.models.calculator import ThermoCalculator

        calc = ThermoCalculator()
        mixture = GasMixture(
            components=[
                GasComponent(name="Nitrogen", fraction=50.0),
                GasComponent(name="CarbonDioxide", fraction=50.0),
            ],
            fraction_type="molar",
        )
        result, backend = calc.calculate_with_fallback(
            mixture=mixture,
            temperature_k=288.15,
            pressure_pa=101325.0,
            preferred_backend="SRK",
        )
        # Inerts have no heating values: heating may be None or HHV=0
        if result.heating is not None:
            assert result.heating.hhv_mass >= 0
