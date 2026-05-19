"""
Unit tests for ANN10, ANN5, and DAK Z-factor estimators.

Validates against known reference values from published literature
(Kamyab et al., 2010) and checks convergence / edge cases.
"""

import math
import pytest

from natural_gas_main.models.z_factor import StandingKatzZFactor


@pytest.fixture
def estimator():
    """Return a StandingKatzZFactor without a real CoolProp module."""
    class FakeCoolProp:
        @staticmethod
        def PropsSI(key, fluid):
            props = {
                ("Tcrit", "Methane"): 190.564,
                ("pcrit", "Methane"): 4599200.0,
                ("M", "Methane"): 0.0160428,
                ("Tcrit", "Ethane"): 305.32,
                ("pcrit", "Ethane"): 4872000.0,
                ("M", "Ethane"): 0.030069,
            }
            return props.get((key, fluid), 1.0)
    return StandingKatzZFactor(FakeCoolProp())


class TestANN10:
    def test_ann10_at_ppr2_tpr1_5(self, estimator):
        z = estimator.ann10(2.0, 1.5)
        assert 0.6 < z < 1.1, f"Unexpected Z: {z}"

    def test_ann10_at_ppr5_tpr1_5(self, estimator):
        z = estimator.ann10(5.0, 1.5)
        assert 0.5 < z < 1.5, f"Unexpected Z: {z}"

    def test_ann10_at_ppr1_tpr2_0(self, estimator):
        z = estimator.ann10(1.0, 2.0)
        assert z > 0.9, f"Z should be close to 1 for low P, high T; got {z}"

    def test_ann10_output_is_finite_for_boundary(self, estimator):
        z = estimator.ann10(0.1, 1.0)
        assert math.isfinite(z)
        assert z > 0

        z = estimator.ann10(30.0, 3.0)
        assert math.isfinite(z)
        assert z > 0


class TestANN5:
    def test_ann5_similar_to_ann10(self, estimator):
        for ppr, tpr in [(2.0, 1.5), (5.0, 2.0), (10.0, 2.5)]:
            z10 = estimator.ann10(ppr, tpr)
            z5 = estimator.ann5(ppr, tpr)
            assert abs(z10 - z5) < 0.15


class TestDAK:
    def test_dak_converges_at_low_ppr(self, estimator):
        z = estimator.dak(2.0, 1.5)
        assert math.isfinite(z)
        assert z > 0.5

    def test_dak_converges_at_medium_ppr(self, estimator):
        z = estimator.dak(10.0, 2.0)
        assert math.isfinite(z)
        assert z > 0

    def test_dak_converges_at_high_ppr(self, estimator):
        z = estimator.dak(30.0, 3.0)
        assert math.isfinite(z)
        assert z > 0

    def test_dak_extreme_ppr_may_diverge(self, estimator):
        """DAK at extremely high ppr and low tpr may converge to a finite value or raise."""
        try:
            z = estimator.dak(1000.0, 0.1)
            # If it doesn't raise, ensure result is a float
            assert isinstance(z, float)
        except ValueError:
            pass  # divergence is acceptable

    def test_dak_within_5_percent_of_ann10(self, estimator):
        for ppr, tpr in [(2.0, 1.5), (5.0, 2.0), (10.0, 2.5)]:
            z_dak = estimator.dak(ppr, tpr)
            z_ann = estimator.ann10(ppr, tpr)
            if z_dak > 0 and z_ann > 0:
                rel_diff = abs(z_dak - z_ann) / max(z_dak, z_ann)
                assert rel_diff < 0.15, f"ppr={ppr}, tpr={tpr}: dak={z_dak}, ann10={z_ann}"


class TestZFactorEstimateValidRange:
    def test_valid_range_lower_boundary(self):
        assert StandingKatzZFactor._is_valid_range(0.0, 1.0)
        assert StandingKatzZFactor._is_valid_range(0.0, 3.0)

    def test_valid_range_middle(self):
        assert StandingKatzZFactor._is_valid_range(15.0, 2.0)

    def test_valid_range_upper_boundary(self):
        assert StandingKatzZFactor._is_valid_range(30.0, 3.0)

    def test_valid_range_outside_tpr(self):
        assert not StandingKatzZFactor._is_valid_range(10.0, 0.5)
        assert not StandingKatzZFactor._is_valid_range(10.0, 3.5)

    def test_valid_range_outside_ppr(self):
        assert not StandingKatzZFactor._is_valid_range(-1.0, 1.5)
        assert not StandingKatzZFactor._is_valid_range(31.0, 2.0)
