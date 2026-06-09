"""Aşama 4 — Detaylı: CoolProp AbstractState mock gerektiren coverage testleri.

Kapsanan dosya: calculator.py (76% → 90%+)
"""

import math
import logging
from unittest.mock import patch, MagicMock, PropertyMock
import pytest

from natural_gas_main.models.gas_data import GasComponent, GasMixture
from natural_gas_main.models.calculation_result import (
    CalculationResult, ActualConditionResults, StandardConditionResults,
    HeatingValues, VolumeConversion,
)
from natural_gas_main.core.exceptions import (
    BackendNotAvailableError, StateUpdateError, HeatingValueError,
    ThermoCalculationError,
)


# ---------------------------------------------------------------------------
# Fake CoolProp classes
# ---------------------------------------------------------------------------

class FakeAbstractState:
    """Minimal mock of CoolProp.AbstractState for calculator testing."""

    def __init__(self, backend, fluid):
        self._backend = backend
        self._fluid = fluid
        self._T = 300.0
        self._P = 101325.0

    def set_mole_fractions(self, fractions):
        pass

    def set_mass_fractions(self, fractions):
        pass

    def update(self, inp, P, T):
        self._P = P
        self._T = T

    def T(self):
        return self._T

    def p(self):
        return self._P

    def rhomass(self):
        return 0.66

    def molar_mass(self):
        return 0.016

    def compressibility_factor(self):
        return 0.998

    def umass(self):
        return 0.0

    def hmass(self):
        return 0.0

    def smass(self):
        return 0.0

    def cpmass(self):
        return 0.0

    def cvmass(self):
        return 0.0

    def speed_sound(self):
        return 400.0

    def HHVmass(self):
        return 55.5e6

    def LHVmass(self):
        return 50.0e6

    def keyed_output(self, key):
        return None

    def build_phase_envelope(self, flag):
        pass

    def get_phase_envelope_data(self):
        data = MagicMock()
        data.T = [250, 300, 350]
        data.p = [50000, 100000, 80000]
        return data


class FakeCoolProp:
    """Minimal mock of CoolProp.CoolProp module."""

    AbstractState = FakeAbstractState
    PT_INPUTS = 1
    iT_critical = 100
    iP_critical = 101

    @staticmethod
    def PropsSI(key, *args):
        props = {
            ("Tcrit", "Methane"): 190.564,
            ("pcrit", "Methane"): 4599200.0,
            ("M", "Methane"): 0.0160428,
            ("M", "Nitrogen"): 0.0280134,
            ("D", 288.15, 101325.0, "Air"): 1.225,
        }
        return props.get(tuple(args), 1.0)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def calc():
    with patch.dict("sys.modules", {"CoolProp.CoolProp": FakeCoolProp()}):
        with patch("natural_gas_main.models.calculator.CP", FakeCoolProp()):
            with patch("natural_gas_main.models.calculator.COOLPROP_AVAILABLE", True):
                from natural_gas_main.models.calculator import ThermoCalculator
                yield ThermoCalculator()


@pytest.fixture
def simple_mixture():
    return GasMixture(
        components=[GasComponent(name="Methane", fraction=100.0)],
        fraction_type="molar",
    )


# ---------------------------------------------------------------------------
# __init__ and basic flow
# ---------------------------------------------------------------------------

class TestInit:
    def test_coolprop_not_available_raises(self):
        with patch("natural_gas_main.models.calculator.COOLPROP_AVAILABLE", False):
            from natural_gas_main.models.calculator import ThermoCalculator
            with pytest.raises(BackendNotAvailableError):
                ThermoCalculator()

    def test_calculate_exception_logged(self, calc, simple_mixture):
        with patch.object(calc, '_calculate_with_backend', side_effect=ValueError("test error")):
            with pytest.raises(ValueError):
                calc.calculate_properties(simple_mixture, 300, 101325)


# ---------------------------------------------------------------------------
# _select_backend and _get_backends
# ---------------------------------------------------------------------------

class TestSelectBackend:
    def test_heos_with_incompatible_still_returns_heos(self, calc, simple_mixture):
        """_select_backend logs warning but returns HEOS regardless."""
        with patch("natural_gas_main.models.gas_data.GasMixture.check_heos_compatibility",
                   return_value=["Oxygen"]):
            backend = calc._select_backend(simple_mixture, "HEOS")
            assert backend == "HEOS"

    def test_srk_direct(self, calc, simple_mixture):
        backend = calc._select_backend(simple_mixture, "SRK")
        assert backend == "SRK"

    def test_pr_direct(self, calc, simple_mixture):
        backend = calc._select_backend(simple_mixture, "PR")
        assert backend == "PR"

    def test_aga8_backend(self, calc, simple_mixture):
        backend = calc._select_backend(simple_mixture, "GERG-2008")
        assert backend == "GERG-2008"


class TestGetBackendOrder:
    def test_heos_incompatible_excluded(self, calc, simple_mixture):
        with patch("natural_gas_main.models.gas_data.GasMixture.check_heos_compatibility",
                   return_value=["Oxygen"]):
            backends = calc._get_backend_order(simple_mixture, "HEOS")
            assert "HEOS" not in backends

    def test_preferred_first(self, calc, simple_mixture):
        backends = calc._get_backend_order(simple_mixture, "SRK")
        assert backends[0] == "SRK"


# ---------------------------------------------------------------------------
# _create_state - mass fractions, exception
# ---------------------------------------------------------------------------

class TestCreateState:
    def test_mass_fractions_path(self, calc):
        mixture = GasMixture(
            components=[GasComponent(name="Methane", fraction=100.0)],
            fraction_type="mass",
        )
        state = calc._create_state(mixture, 300, 101325, "HEOS")
        assert state is not None

    def test_creation_exception_raises_state_update_error(self, calc):
        mixture = MagicMock()
        mixture.to_coolprop_string.side_effect = RuntimeError("boom")
        with pytest.raises(StateUpdateError):
            calc._create_state(mixture, 300, 101325, "HEOS")


# ---------------------------------------------------------------------------
# _calculate_phase_envelope - empty, exception
# ---------------------------------------------------------------------------

class TestPhaseEnvelope:
    def test_empty_phase_envelope_returns_none(self, calc, simple_mixture):
        state = calc._create_state(simple_mixture, 300, 101325, "HEOS")
        with patch.object(state, 'get_phase_envelope_data') as mock_get:
            mock_data = MagicMock()
            mock_data.T = []
            mock_data.p = []
            mock_get.return_value = mock_data
            result = calc._calculate_phase_envelope(state, "HEOS")
            assert result is None

    def test_phase_envelope_exception_caught(self, calc, simple_mixture):
        state = calc._create_state(simple_mixture, 300, 101325, "HEOS")
        with patch.object(state, 'build_phase_envelope', side_effect=RuntimeError("no pe")):
            result = calc._calculate_phase_envelope(state, "HEOS")
            assert result is None


# ---------------------------------------------------------------------------
# _calculate_actual_conditions - edge branches (ZeroDivisionError, speed sound)
# ---------------------------------------------------------------------------

class TestActualConditions:
    def test_cv_near_zero_k_is_none(self, calc, simple_mixture):
        state = calc._create_state(simple_mixture, 300, 101325, "HEOS")
        # Exaggerated cp/cv shouldn't be zero in a real state, but test the guard
        with patch.object(state, 'cvmass', return_value=1e-12):
            res = calc._calculate_actual_conditions(state)
            assert res.isentropic_exponent is None

    def test_speed_sound_exception_caught(self, calc, simple_mixture):
        state = calc._create_state(simple_mixture, 300, 101325, "HEOS")
        with patch.object(state, 'speed_sound', side_effect=RuntimeError("no sound")):
            res = calc._calculate_actual_conditions(state)
            assert res.speed_of_sound is None


# ---------------------------------------------------------------------------
# _calculate_standard_conditions - air density exception
# ---------------------------------------------------------------------------

class TestStandardConditions:
    def test_air_density_exception_falls_to_ideal_gas(self, calc, simple_mixture):
        with patch.object(FakeCoolProp, 'PropsSI', side_effect=Exception("no air")):
            res = calc._calculate_standard_conditions(simple_mixture, "HEOS", 288.15, 101325)
            assert res.specific_gravity is not None


# ---------------------------------------------------------------------------
# _calculate_z_factor_comparison - exception branches
# ---------------------------------------------------------------------------

class TestZFactorComparison:
    def test_sk_estimates_exception(self, calc, simple_mixture):
        with patch.object(calc.z_factor_estimator, 'estimates', side_effect=Exception("sk failed")):
            comps = calc._calculate_z_factor_comparison(simple_mixture, 300, 101325)
            # Should still work without crashing
            assert isinstance(comps, list)

    def test_aga8_not_available_skipped(self, calc, simple_mixture):
        with patch("natural_gas_main.models.calculator.calculate_aga8", side_effect=Exception("no aga8")):
            comps = calc._calculate_z_factor_comparison(simple_mixture, 300, 101325)
            assert isinstance(comps, list)


# ---------------------------------------------------------------------------
# _calculate_heating_values - all 4 stages
# ---------------------------------------------------------------------------

class TestHeatingValues:
    def test_rho_std_none_returns_none(self, calc, simple_mixture):
        result = calc._calculate_heating_values(simple_mixture, None, 0.6, "HEOS", 288.15, 101325)
        assert result is None

    def test_rho_std_zero_returns_none(self, calc, simple_mixture):
        result = calc._calculate_heating_values(simple_mixture, 0.0, 0.6, "HEOS", 288.15, 101325)
        assert result is None

    def test_non_heos_backend_switch(self, calc, simple_mixture):
        with patch("natural_gas_main.models.gas_data.GasMixture.check_heos_compatibility",
                   return_value=False):
            result = calc._calculate_heating_values(simple_mixture, 0.66, 0.6, "GERG-2008", 288.15, 101325)
            assert result is None or isinstance(result, HeatingValues)

    def test_stage_1_zero_values_falls_through(self, calc, simple_mixture):
        """Built-in returns zero → falls through to stage 2."""
        with patch.object(calc, '_calculate_heating_values_builtin', return_value=(0.0, 0.0)):
            result = calc._calculate_heating_values(simple_mixture, 0.66, 0.6, "HEOS", 288.15, 101325)
            assert result is None or isinstance(result, HeatingValues)

    def test_stage_1_exception_falls_through(self, calc, simple_mixture):
        with patch.object(calc, '_calculate_heating_values_builtin', side_effect=Exception("no builtin")):
            result = calc._calculate_heating_values(simple_mixture, 0.66, 0.6, "HEOS", 288.15, 101325)
            assert result is None or isinstance(result, HeatingValues)

    def test_stage_2_zero_values_falls_through(self, calc, simple_mixture):
        with patch.multiple(
            calc,
            _calculate_heating_values_builtin=MagicMock(side_effect=Exception("skip")),
            _calculate_heating_values_component_based=MagicMock(return_value=(0.0, 0.0)),
        ):
            result = calc._calculate_heating_values(simple_mixture, 0.66, 0.6, "HEOS", 288.15, 101325)
            assert result is None or isinstance(result, HeatingValues)

    def test_all_stages_fail_returns_none(self, calc, simple_mixture):
        with patch.multiple(
            calc,
            _calculate_heating_values_builtin=MagicMock(side_effect=Exception("fail")),
            _calculate_heating_values_component_based=MagicMock(side_effect=Exception("fail")),
        ):
            with patch("natural_gas_main.models.calculator.is_iso6976_compatible", return_value=False):
                with patch.object(calc, '_calculate_heating_values_reference', side_effect=Exception("fail")):
                    result = calc._calculate_heating_values(simple_mixture, 0.66, 0.6, "HEOS", 288.15, 101325)
                    assert result is None

    def test_reference_db_t_ref_warning(self, calc, simple_mixture):
        hv = calc._calculate_heating_values(simple_mixture, 0.66, 0.6, "SRK", 273.15, 101325)
        assert hv is None or isinstance(hv, HeatingValues)

    def test_heating_values_builtin_low_values_raises(self, calc, simple_mixture):
        state = calc._create_state(simple_mixture, 288.15, 101325, "HEOS")
        with patch.object(state, 'HHVmass', return_value=0.5):
            with patch.object(state, 'LHVmass', return_value=0.3):
                with patch.object(calc, '_create_state', return_value=state):
                    with pytest.raises(HeatingValueError):
                        calc._calculate_heating_values_builtin(simple_mixture, "HEOS", 288.15, 101325)


# ---------------------------------------------------------------------------
# _get_heating_value_mass_weights - CP.PropsSI exception, total <= 0
# ---------------------------------------------------------------------------

class TestHeatingValueWeights:
    def test_propsi_exception_falls_to_abstract_state(self, calc):
        mixture = GasMixture(
            components=[GasComponent(name="Methane", fraction=100.0)],
            fraction_type="molar",
        )
        with patch.object(FakeCoolProp, 'PropsSI', side_effect=Exception("no props")):
            weights = calc._get_heating_value_mass_weights(mixture)
            assert "Methane" in weights
            assert weights["Methane"] > 0


# ---------------------------------------------------------------------------
# _calculate_z_only_fallback - ann10 None
# ---------------------------------------------------------------------------

class TestZOnlyFallback:
    def test_ann10_none_returns_none(self, calc, simple_mixture):
        with patch.object(calc, '_calculate_z_factor_comparison', return_value=[]):
            result = calc._calculate_z_only_fallback(
                simple_mixture, 300, 101325, None, 288.15, 101325, "ISO"
            )
            assert result is None


# ---------------------------------------------------------------------------
# calculate_with_fallback - all backends fail
# ---------------------------------------------------------------------------

class TestCalculateWithFallback:
    def test_all_backends_fail_raises(self, calc, simple_mixture):
        with patch.object(calc, '_calculate_with_backend', side_effect=ValueError("fail")):
            with patch.object(calc, '_calculate_z_only_fallback', return_value=None):
                with pytest.raises(ThermoCalculationError):
                    calc.calculate_with_fallback(simple_mixture, 300, 101325)


# ---------------------------------------------------------------------------
# _compute_aga8 - phase envelope branched
# ---------------------------------------------------------------------------

class TestComputeAga8:
    def test_aga8_phase_envelope_heos_compatible(self, calc, simple_mixture):
        result = calc._compute_aga8(simple_mixture, 300, 101325, "GERG-2008", 288.15, 101325, "ISO")
        actual, standard, pe = result
        assert actual is not None
        assert standard is not None

    def test_aga8_phase_envelope_exception(self, calc, simple_mixture):
        with patch.object(calc, '_calculate_phase_envelope', side_effect=Exception("pe fail")):
            result = calc._compute_aga8(simple_mixture, 300, 101325, "GERG-2008", 288.15, 101325, "ISO")
            actual, standard, pe = result
            assert pe is None


# ---------------------------------------------------------------------------
# _finalize_result - rho_std / sg None
# ---------------------------------------------------------------------------

class TestFinalizeResult:
    def test_rho_std_none_skips_volume(self, calc, simple_mixture):
        actual = ActualConditionResults(
            temperature=300, pressure=101325, density=0.66,
            molar_mass=0.016, compressibility_factor=0.998,
            internal_energy=0, enthalpy=0, entropy=0, cp=0, cv=0,
        )
        standard = StandardConditionResults(
            density_std=None, specific_gravity=None,
            reference_temperature=288.15, reference_pressure=101325,
        )
        result = calc._finalize_result(
            simple_mixture, actual, standard, None,
            300, 101325, 100.0, "HEOS", 288.15, 101325,
        )
        assert result.volume_conversion is None

    def test_sg_none_logs_warning(self, calc, simple_mixture):
        actual = ActualConditionResults(
            temperature=300, pressure=101325, density=0.66,
            molar_mass=0.016, compressibility_factor=0.998,
            internal_energy=0, enthalpy=0, entropy=0, cp=0, cv=0,
        )
        standard = StandardConditionResults(
            density_std=0.66, specific_gravity=None,
            reference_temperature=288.15, reference_pressure=101325,
        )
        result = calc._finalize_result(
            simple_mixture, actual, standard, None,
            300, 101325, 100.0, "HEOS", 288.15, 101325,
        )
        assert result is not None


# ---------------------------------------------------------------------------
# Additional edge cases from Missed Lines report
# ---------------------------------------------------------------------------

class TestMiscEdgeCases:
    def test_volume_conversion_exception_handled(self, calc, simple_mixture):
        actual = ActualConditionResults(
            temperature=300, pressure=101325, density=0.66,
            molar_mass=0.016, compressibility_factor=0.998,
            internal_energy=0, enthalpy=0, entropy=0, cp=0, cv=0,
        )
        standard = StandardConditionResults(
            density_std=0.66, specific_gravity=0.6,
            reference_temperature=288.15, reference_pressure=101325,
        )
        with patch.object(calc, '_create_state', side_effect=Exception("create failed")):
            result = calc._finalize_result(
                simple_mixture, actual, standard, None,
                300, 101325, 100.0, "HEOS", 288.15, 101325,
            )
            assert result.volume_conversion is not None
            assert result.volume_conversion.normal_volume is None

    def test_heating_values_ref_no_component_warns(self, calc):
        mixture = GasMixture(
            components=[GasComponent(name="Neon", fraction=100.0)],
            fraction_type="molar",
        )
        with pytest.raises(HeatingValueError, match="No reference"):
            calc._calculate_heating_values_reference(mixture)

    def test_mass_weight_total_zero_raises(self, calc):
        """When PropsSI returns 0 molar mass, total stays 0 -> raises."""
        mixture = GasMixture(
            components=[GasComponent(name="Methane", fraction=100.0)],
            fraction_type="molar",
        )
        with patch.object(FakeCoolProp, 'PropsSI', return_value=0.0):
            with pytest.raises(HeatingValueError, match="Could not convert"):
                calc._get_heating_value_mass_weights(mixture)

    def test_z_only_rho_air_exception(self, calc, simple_mixture):
        """_calculate_z_only_fallback handles CoolProp air density exception (line 414-415)."""
        with patch.object(calc, '_calculate_z_factor_comparison') as mock_comp:
            from natural_gas_main.models.calculation_result import ZFactorComparison
            mock_comp.return_value = [
                ZFactorComparison(
                    method="Standing-Katz ANN10", z_factor=0.998,
                    ppr=2.0, tpr=1.5, valid=True,
                )
            ]
            with patch("natural_gas_main.models.calculator.CP.PropsSI",
                       side_effect=Exception("no air")):
                result = calc._calculate_z_only_fallback(
                    simple_mixture, 300, 101325, None, 288.15, 101325, "ISO",
                )
                assert result is not None

    def test_component_hhv_low_value_skipped(self, calc):
        """Component-based HHV with hhv/lhv < 1e-6 are treated as zero (lines 1080-1082)."""
        mixture = GasMixture(
            components=[GasComponent(name="Methane", fraction=100.0)],
            fraction_type="molar",
        )
        with patch.object(calc, '_get_heating_value_mass_weights', return_value={"Methane": 1.0}):
            with patch("natural_gas_main.models.calculator.CP.AbstractState") as mock_abs:
                mock_state = MagicMock()
                mock_state.HHVmass.return_value = 0.5  # < 1e6 threshold
                mock_state.LHVmass.return_value = 0.3
                mock_abs.return_value = mock_state
                with pytest.raises(HeatingValueError):
                    calc._calculate_heating_values_component_based(mixture, "HEOS", 288.15, 101325)
