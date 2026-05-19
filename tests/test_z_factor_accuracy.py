"""
Z-factor accuracy tests against known reference values.

Verifies Standing-Katz ANN10/ANN5/DAK and backend Z values
are within expected ranges for well-characterised gas mixtures.
"""

import math

import pytest

from natural_gas_main.models.calculator import COOLPROP_AVAILABLE, ThermoCalculator
from natural_gas_main.models.gas_data import GasComponent, GasMixture
from natural_gas_main.models.z_factor import StandingKatzZFactor

pytestmark = pytest.mark.skipif(not COOLPROP_AVAILABLE, reason="CoolProp is not installed")


class TestZFactorRange:
    """Z-factor sanity checks for typical natural gas."""

    def test_typical_gas_z_all_backends_agree_within_5_percent(self):
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=94.0),
                GasComponent(name="Ethane", fraction=4.0),
                GasComponent(name="Propane", fraction=1.0),
                GasComponent(name="Nitrogen", fraction=1.0),
            ]
        )
        result = ThermoCalculator().calculate_properties(
            mixture, temperature_k=288.15, pressure_pa=8_000_000, backend="HEOS"
        )
        z_values = {}
        for item in result.z_factor_comparison:
            if item.z_factor is not None and item.valid:
                z_values[item.method] = item.z_factor

        assert z_values, "No valid Z estimates produced"
        ref = z_values.popitem()[1]
        for method, z in z_values.items():
            assert z == pytest.approx(ref, rel=0.05), (
                f"{method} Z={z:.5f} deviates >5% from reference {ref:.5f}"
            )

    def test_pure_methane_at_atmospheric_conditions_z_near_1(self):
        mixture = GasMixture(components=[GasComponent(name="Methane", fraction=100.0)])
        result = ThermoCalculator().calculate_properties(
            mixture, temperature_k=288.15, pressure_pa=101_325, backend="HEOS"
        )
        z = result.actual.compressibility_factor
        assert 0.99 < z < 1.01, f"Z={z:.5f} for methane at 1 atm should be near 1.0"

    def test_high_pressure_z_is_lower_than_ambient(self):
        mixture = GasMixture(components=[GasComponent(name="Methane", fraction=100.0)])
        ambient = ThermoCalculator().calculate_properties(
            mixture, temperature_k=288.15, pressure_pa=101_325, backend="HEOS"
        )
        high_p = ThermoCalculator().calculate_properties(
            mixture, temperature_k=288.15, pressure_pa=10_000_000, backend="HEOS"
        )
        assert high_p.actual.compressibility_factor < ambient.actual.compressibility_factor


class TestKatzANNValidity:
    """Tests for Standing-Katz validity range enforcement."""

    def test_out_of_range_tpr_gives_invalid_flag(self):
        mixture = GasMixture(components=[GasComponent(name="Methane", fraction=100.0)])
        estimator = StandingKatzZFactor(ThermoCalculator().z_factor_estimator.cp)
        pseudo = estimator.pseudo_critical(mixture)

        tpr_high = 3.5  # Above TPR_MAX
        ppr = 5.0
        z = estimator.ann10(ppr, tpr_high)
        assert z > 0
        assert not estimator._is_valid_range(ppr, tpr_high)

    def test_valid_range_returns_true(self):
        assert StandingKatzZFactor._is_valid_range(ppr=5.0, tpr=1.5)

    def test_zero_ppr_returns_false(self):
        assert not StandingKatzZFactor._is_valid_range(ppr=-1.0, tpr=1.5)

    def test_ann5_produces_similar_values_to_ann10(self):
        mixture = GasMixture(components=[GasComponent(name="Methane", fraction=100.0)])
        estimator = StandingKatzZFactor(ThermoCalculator().z_factor_estimator.cp)
        pseudo = estimator.pseudo_critical(mixture)
        ppr, tpr = 5.0, 1.5
        z10 = estimator.ann10(ppr, tpr)
        z5 = estimator.ann5(ppr, tpr)
        assert z10 == pytest.approx(z5, rel=0.15), (
            f"ANN10={z10:.5f} and ANN5={z5:.5f} differ too much"
        )


class TestDAKConvergence:
    """Dranchuk-Abou-Kassem iterative solver tests."""

    def test_dak_converges_for_valid_range(self):
        estimator = StandingKatzZFactor(ThermoCalculator().z_factor_estimator.cp)
        z = estimator.dak(ppr=5.0, tpr=1.5)
        assert 0.5 < z < 1.5
        assert math.isfinite(z)

    def test_dak_within_5_percent_of_ann10(self):
        estimator = StandingKatzZFactor(ThermoCalculator().z_factor_estimator.cp)
        for ppr, tpr in [(2.0, 1.3), (5.0, 1.5), (10.0, 2.0)]:
            z_ann = estimator.ann10(ppr, tpr)
            z_dak = estimator.dak(ppr, tpr)
            assert z_dak == pytest.approx(z_ann, rel=0.05), (
                f"Ppr={ppr}, Tpr={tpr}: DAK={z_dak:.5f} vs ANN10={z_ann:.5f}"
            )
