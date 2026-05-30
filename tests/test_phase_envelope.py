"""Tests for phase envelope critical point extraction and StandardConditionResults."""

import logging
import pytest
from natural_gas_main.models.calculator import ThermoCalculator
from natural_gas_main.models.gas_data import GasComponent, GasMixture
from natural_gas_main.models.calculation_result import (
    CalculationResult,
    StandardConditionResults,
    ActualConditionResults,
    PhaseEnvelopeData,
)


class TestStandardConditionResults:
    """Verify StandardConditionResults handles None fields."""

    def test_create_with_none(self):
        """Creating with None density_sgd and specific_gravity should work."""
        result = StandardConditionResults(
            density_std=None,
            specific_gravity=None,
            reference_temperature=288.15,
            reference_pressure=101325.0,
            standard_name="ISO 13443",
        )
        assert result.density_std is None
        assert result.specific_gravity is None

    def test_create_with_values(self):
        """Normal creation with float values should work."""
        result = StandardConditionResults(
            density_std=0.8,
            specific_gravity=0.65,
            reference_temperature=288.15,
            reference_pressure=101325.0,
            standard_name="ISO 13443",
        )
        assert result.density_std == pytest.approx(0.8)

    def test_to_display_list_none_density(self):
        """to_display_list should not crash with None density/SG."""
        result = CalculationResult(
            backend_used="HEOS",
            actual=ActualConditionResults(
                temperature=288.15,
                pressure=101325.0,
                density=0.7,
                molar_mass=0.018,
                compressibility_factor=0.98,
                internal_energy=0.0,
                enthalpy=0.0,
                entropy=0.0,
                cp=1.0,
                cv=0.7,
            ),
            standard=StandardConditionResults(
                density_std=None,
                specific_gravity=None,
                reference_temperature=288.15,
                reference_pressure=101325.0,
                standard_name="ISO 13443",
            ),
        )
        display = result.to_display_list()
        assert any("Hesaplanamadı" in str(item[1]) for item in display)


class TestPhaseEnvelopeData:
    """Verify PhaseEnvelopeData model fields."""

    def test_create_minimal(self):
        """Create with just temperature and pressure arrays."""
        pe = PhaseEnvelopeData(
            temperature_k=[200.0, 250.0, 300.0],
            pressure_pa=[1e5, 5e5, 1e6],
            cricondentherm_t=300.0,
            cricondenbar_p=1e6,
        )
        assert pe.temperature_k == [200.0, 250.0, 300.0]
        assert pe.cricondentherm_t == 300.0
        assert pe.cricondenbar_p == 1e6

    def test_create_with_critical(self):
        """Critical point fields should be settable."""
        pe = PhaseEnvelopeData(
            temperature_k=[200.0, 250.0, 300.0],
            pressure_pa=[1e5, 5e5, 1e6],
            cricondentherm_t=300.0,
            cricondenbar_p=1e6,
            critical_t=250.0,
            critical_p=5e5,
        )
        assert pe.critical_t == 250.0
        assert pe.critical_p == 5e5


class TestPhaseEnvelopeCalculation:
    def test_phase_envelope_for_methane(self):
        """Methane phase envelope should return valid data."""
        calc = ThermoCalculator()
        mixture = GasMixture(
            components=[GasComponent(name="Methane", fraction=100.0)],
            fraction_type="molar",
        )
        state = calc._create_state(mixture, 190.0, 4e6, "HEOS")
        pe = calc._calculate_phase_envelope(state, "HEOS")
        assert pe is not None
        assert len(pe.temperature_k) > 0
        assert pe.cricondentherm_t is not None

    def test_cricondenbar_is_max_pressure(self):
        """cricondenbar_p should equal max(P_array)."""
        calc = ThermoCalculator()
        mixture = GasMixture(
            components=[GasComponent(name="Methane", fraction=100.0)],
            fraction_type="molar",
        )
        state = calc._create_state(mixture, 190.0, 4e6, "HEOS")
        pe = calc._calculate_phase_envelope(state, "HEOS")
        if pe:
            assert pe.cricondenbar_p == pytest.approx(max(pe.pressure_pa))
