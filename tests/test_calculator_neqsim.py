"""Tests for ThermoCalculator NeqSim integration paths.

Covers:
- _compute_neqsim error handling
- NeqSim ISO 6976 heating value stage (lines 1074-1089)
- NeqSim preferred fallback order
- _is_neqsim_backend with all known backends
- _select_backend for NeqSim
- hydrate temperature NeqSim path
"""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock

from natural_gas_main.models.gas_data import GasComponent, GasMixture
from natural_gas_main.models.calculation_result import (
    ActualConditionResults, TransportProperties, CalculationResult,
    StandardConditionResults
)
from natural_gas_main.core.exceptions import BackendNotAvailableError


@pytest.fixture
def simple_mixture():
    return GasMixture(
        components=[
            GasComponent(name="Methane", fraction=90.0),
            GasComponent(name="Ethane", fraction=10.0),
        ],
        fraction_type="molar"
    )


@pytest.fixture
def std_conds():
    return StandardConditionResults(
        reference_temperature=288.15,
        reference_pressure=101325.0,
    )


class TestThermoCalculatorNeqSimDispatch:
    """Test _compute_neqsim and related dispatch."""

    def test_compute_neqsim_raises_when_unavailable(self, simple_mixture):
        from natural_gas_main.models.calculator import ThermoCalculator
        calc = ThermoCalculator()
        with patch("natural_gas_main.models.calculator.NEQSIM_AVAILABLE", False):
            with pytest.raises(BackendNotAvailableError):
                calc._compute_neqsim(
                    simple_mixture, 300.0, 1e5, None, "neqsim-srk",
                    288.15, 101325.0, "ISO 13443"
                )

    @patch("natural_gas_main.models.calculator.NEQSIM_AVAILABLE", True)
    @patch("natural_gas_main.models.calculator.calculate_neqsim")
    def test_compute_neqsim_wraps_transport_into_result(self, mock_calc_neqsim, simple_mixture):
        from natural_gas_main.models.calculator import ThermoCalculator

        mock_transport = TransportProperties(
            viscosity_cp=0.012,
            thermal_conductivity=0.035,
            joule_thomson_coefficient=0.0005,
            surface_tension=0.015,
            has_liquid_hc_phase=True,
        )
        mock_actual = ActualConditionResults(
            temperature=300.0, pressure=1e5, density=20.0,
            molar_mass=0.016, compressibility_factor=0.95,
            internal_energy=-500.0, enthalpy=-480.0, entropy=3.0,
            cp=2.2, cv=1.6, isentropic_exponent=1.375, speed_of_sound=450.0,
        )
        mock_calc_neqsim.return_value = (mock_actual, mock_transport)

        calc = ThermoCalculator()
        result = calc._compute_neqsim(
            simple_mixture, 300.0, 1e5, 100.0, "neqsim-srk",
            288.15, 101325.0, "ISO 13443"
        )

        assert isinstance(result, CalculationResult)
        assert result.backend_used == "neqsim-srk"
        assert result.actual.compressibility_factor == 0.95
        assert result.transport is not None
        assert result.transport.viscosity_cp == 0.012

    @patch("natural_gas_main.models.calculator.NEQSIM_AVAILABLE", True)
    @patch("natural_gas_main.models.calculator.calculate_neqsim")
    def test_compute_neqsim_without_volume(self, mock_calc_neqsim, simple_mixture):
        from natural_gas_main.models.calculator import ThermoCalculator

        mock_transport = TransportProperties()
        mock_actual = ActualConditionResults(
            temperature=300.0, pressure=1e5, density=20.0,
            molar_mass=0.016, compressibility_factor=0.95,
            internal_energy=-500.0, enthalpy=-480.0, entropy=3.0,
            cp=2.2, cv=1.6,
        )
        mock_calc_neqsim.return_value = (mock_actual, mock_transport)

        calc = ThermoCalculator()
        result = calc._compute_neqsim(
            simple_mixture, 300.0, 1e5, None, "neqsim-srk",
            288.15, 101325.0, "ISO 13443"
        )

        assert result.volume_conversion is None


class TestThermoCalculatorNeqSimHeatingValues:
    """Test NeqSim ISO 6976 Stage 0 in _calculate_heating_values."""

    @patch("natural_gas_main.models.calculator.NEQSIM_AVAILABLE", True)
    @patch("natural_gas_main.models.calculator.get_neqsim_iso6976")
    def test_neqsim_iso_used_when_available(self, mock_get_iso, simple_mixture):
        from natural_gas_main.models.calculator import ThermoCalculator

        mock_get_iso.return_value = {
            "gcv_kj_m3": 40000.0,
            "lcv_kj_m3": 36000.0,
            "wobbe_kj_m3": 52000.0,
        }

        calc = ThermoCalculator()
        result = calc._calculate_heating_values(
            simple_mixture, 1.0, 0.65, "neqsim-srk", 288.15, 101325.0
        )

        assert result is not None
        assert result.calculation_method == "NeqSim ISO 6976"
        assert result.hhv_mass > 0
        assert result.lhv_mass > 0

    @patch("natural_gas_main.models.calculator.NEQSIM_AVAILABLE", True)
    @patch("natural_gas_main.models.calculator.get_neqsim_iso6976")
    def test_neqsim_iso_fallback_when_returns_none(self, mock_get_iso, simple_mixture):
        from natural_gas_main.models.calculator import ThermoCalculator

        mock_get_iso.return_value = None

        calc = ThermoCalculator()
        with patch.object(calc, '_calculate_heating_values_builtin') as mock_builtin:
            mock_builtin.return_value = (50.0, 45.0)
            result = calc._calculate_heating_values(
                simple_mixture, 1.0, 0.65, "neqsim-srk", 288.15, 101325.0
            )

        assert result is not None
        assert result.calculation_method == "CoolProp yerleşik"
        mock_builtin.assert_called_once()

    @patch("natural_gas_main.models.calculator.NEQSIM_AVAILABLE", True)
    @patch("natural_gas_main.models.calculator.get_neqsim_iso6976")
    def test_neqsim_iso_fallback_when_returns_zero_gcv(self, mock_get_iso, simple_mixture):
        from natural_gas_main.models.calculator import ThermoCalculator

        mock_get_iso.return_value = {"gcv_kj_m3": 0.0, "lcv_kj_m3": 0.0, "wobbe_kj_m3": 0.0}

        calc = ThermoCalculator()
        with patch.object(calc, '_calculate_heating_values_builtin') as mock_builtin:
            mock_builtin.return_value = (50.0, 45.0)
            result = calc._calculate_heating_values(
                simple_mixture, 1.0, 0.65, "neqsim-srk", 288.15, 101325.0
            )

        assert result is not None
        assert result.calculation_method == "CoolProp yerleşik"

    @patch("natural_gas_main.models.calculator.NEQSIM_AVAILABLE", True)
    @patch("natural_gas_main.models.calculator.get_neqsim_iso6976")
    def test_neqsim_iso_exception_falls_through(self, mock_get_iso, simple_mixture):
        from natural_gas_main.models.calculator import ThermoCalculator

        mock_get_iso.side_effect = RuntimeError("NeqSim error")

        calc = ThermoCalculator()
        with patch.object(calc, '_calculate_heating_values_builtin') as mock_builtin:
            mock_builtin.return_value = (50.0, 45.0)
            result = calc._calculate_heating_values(
                simple_mixture, 1.0, 0.65, "neqsim-srk", 288.15, 101325.0
            )

        assert result is not None
        assert result.calculation_method == "CoolProp yerleşik"

    def test_neqsim_iso_skipped_when_neqsim_unavailable(self, simple_mixture):
        from natural_gas_main.models.calculator import ThermoCalculator

        calc = ThermoCalculator()
        with patch("natural_gas_main.models.calculator.NEQSIM_AVAILABLE", False):
            with patch("natural_gas_main.models.calculator.get_neqsim_iso6976") as mock_get_iso:
                with patch.object(calc, '_calculate_heating_values_builtin') as mock_builtin:
                    mock_builtin.return_value = (50.0, 45.0)
                    result = calc._calculate_heating_values(
                        simple_mixture, 1.0, 0.65, "neqsim-srk", 288.15, 101325.0
                    )

        mock_get_iso.assert_not_called()
        assert result is not None
        assert result.calculation_method == "CoolProp yerleşik"


class TestThermoCalculatorNeqSimFallbackOrder:
    """Test NeqSim preferred fallback ordering."""

    def test_neqsim_preferred_adds_neqsim_fallbacks_first(self, simple_mixture):
        from natural_gas_main.models.calculator import ThermoCalculator

        calc = ThermoCalculator()
        with patch.object(calc, '_has_non_aga8_components', return_value=False):
            with patch("natural_gas_main.models.gas_data.GasMixture.check_heos_compatibility",
                       return_value=False):
                order = calc._get_backend_order(simple_mixture, "neqsim-srk")

        assert order[0] == "neqsim-srk"
        neqsim_in_order = [b for b in order if b.startswith("neqsim-")]
        assert len(neqsim_in_order) > 1

    def test_non_neqsim_preferred_does_not_add_neqsim(self, simple_mixture):
        from natural_gas_main.models.calculator import ThermoCalculator

        calc = ThermoCalculator()
        with patch.object(calc, '_has_non_aga8_components', return_value=False):
            with patch("natural_gas_main.models.gas_data.GasMixture.check_heos_compatibility",
                       return_value=False):
                order = calc._get_backend_order(simple_mixture, "HEOS")

        neqsim_in_order = [b for b in order if b.startswith("neqsim-")]
        assert len(neqsim_in_order) == 0


class TestThermoCalculatorNeqSimHydrate:
    """Test that NeqSim hydrate is called in _calculate_hydrate_formation."""

    @patch("natural_gas_main.models.calculator.NEQSIM_AVAILABLE", True)
    @patch("natural_gas_main.models.calculator.get_neqsim_hydrate_temperature")
    def test_neqsim_hydrate_included_when_available(self, mock_get_hydrate, simple_mixture):
        """When NeqSim is available, hydrate temperature should include NeqSim result."""
        from natural_gas_main.models.calculator import ThermoCalculator

        mock_get_hydrate.return_value = 285.0

        calc = ThermoCalculator()
        # SG=0.65 triggers the hydrate formula path; mixture triggers NeqSim path
        result = calc._calculate_hydrate_formation(
            290.0, 50e5, 0.65, mixture=simple_mixture
        )

        mock_get_hydrate.assert_called_once_with(simple_mixture, 290.0, 50e5)
        assert result is not None
        # NeqSim affects the average — all 4 values averaged
        temps = [result.t_hydrate_hammerschmidt, result.t_hydrate_motiee,
                 result.t_hydrate_towler_mokhatab, 285.0]
        expected_avg = sum(temps) / len(temps)
        assert abs(result.t_hydrate_average - expected_avg) < 0.01

    def test_neqsim_hydrate_skipped_when_unavailable(self, simple_mixture):
        """When NeqSim is unavailable, hydrate should work without NeqSim."""
        from natural_gas_main.models.calculator import ThermoCalculator

        calc = ThermoCalculator()
        with patch("natural_gas_main.models.calculator.NEQSIM_AVAILABLE", False):
            result = calc._calculate_hydrate_formation(
                290.0, 50e5, 0.65, mixture=simple_mixture
            )

        assert result is not None
        # With SG=0.65, all 3 models should produce valid temps
        assert result.t_hydrate_hammerschmidt is not None
        assert result.t_hydrate_motiee is not None
        assert result.t_hydrate_towler_mokhatab is not None


class TestThermoCalculatorIsNeqSimBackend:
    """Test _is_neqsim_backend static method."""

    def test_all_registered_backends_detected(self):
        from natural_gas_main.models.calculator import ThermoCalculator
        from natural_gas_main.models.neqsim_calculator import NEQSIM_AVAILABLE_BACKENDS
        for backend in NEQSIM_AVAILABLE_BACKENDS:
            assert ThermoCalculator._is_neqsim_backend(backend) is True

    def test_legacy_backends_not_detected(self):
        from natural_gas_main.models.calculator import ThermoCalculator
        for backend in ["HEOS", "SRK", "PR", "GERG-2008", "AGA8-Detail"]:
            assert ThermoCalculator._is_neqsim_backend(backend) is False


class TestThermoCalculatorDispatchToBackend:
    """Test _calculate_with_backend dispatches correctly for NeqSim."""

    @patch("natural_gas_main.models.calculator.NEQSIM_AVAILABLE", True)
    def test_dispatches_to_neqsim_when_backend_is_neqsim(self, simple_mixture):
        from natural_gas_main.models.calculator import ThermoCalculator

        calc = ThermoCalculator()
        with patch.object(calc, '_compute_neqsim') as mock_compute_neqsim:
            mock_compute_neqsim.return_value = CalculationResult(
                backend_used="neqsim-srk",
                actual=ActualConditionResults(
                    temperature=300.0, pressure=1e5, density=20.0,
                    molar_mass=0.016, compressibility_factor=0.95,
                    internal_energy=-500.0, enthalpy=-480.0, entropy=3.0,
                    cp=2.2, cv=1.6,
                ),
                standard=StandardConditionResults(
                    reference_temperature=288.15,
                    reference_pressure=101325.0,
                ),
            )

            calc._calculate_with_backend(
                simple_mixture, 300.0, 1e5, None, "neqsim-srk"
            )
            mock_compute_neqsim.assert_called_once()
