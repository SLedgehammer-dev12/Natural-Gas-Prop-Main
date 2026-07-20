"""Tests for phase envelope calculation across different backends."""

import pytest
from natural_gas_main.models.calculator import ThermoCalculator
from natural_gas_main.models.gas_data import GasComponent, GasMixture
from natural_gas_main.models.calculation_result import PhaseEnvelopeData


class TestPhaseEnvelope:
    """Verify phase envelope generation for different backends."""

    @pytest.fixture
    def calc(self):
        from natural_gas_main.models.calculator import COOLPROP_AVAILABLE
        if not COOLPROP_AVAILABLE:
            pytest.skip("CoolProp not available")
        return ThermoCalculator()

    @pytest.fixture
    def methane_mixture(self):
        return GasMixture(
            components=[GasComponent(name="Methane", fraction=100.0)],
            fraction_type="molar",
        )

    @pytest.fixture
    def nglike_mixture(self):
        return GasMixture(
            components=[
                GasComponent(name="Methane", fraction=90.0),
                GasComponent(name="Ethane", fraction=5.0),
                GasComponent(name="Propane", fraction=3.0),
                GasComponent(name="n-Butane", fraction=2.0),
            ],
            fraction_type="molar",
        )

    def test_heos_produces_phase_envelope_for_methane(self, calc, methane_mixture):
        result, backend = calc.calculate_with_fallback(
            methane_mixture, 250, 1e6, preferred_backend="HEOS"
        )
        assert result.phase_envelope is not None
        assert isinstance(result.phase_envelope, PhaseEnvelopeData)
        assert len(result.phase_envelope.temperature_k) > 10
        assert len(result.phase_envelope.pressure_pa) > 10

    def test_heos_phase_envelope_has_cricondentherm(self, calc, methane_mixture):
        result, _ = calc.calculate_with_fallback(
            methane_mixture, 250, 1e6, preferred_backend="HEOS"
        )
        pe = result.phase_envelope
        assert pe is not None
        assert pe.cricondentherm_t > 0

    def test_heos_phase_envelope_has_cricondenbar(self, calc, methane_mixture):
        result, _ = calc.calculate_with_fallback(
            methane_mixture, 250, 1e6, preferred_backend="HEOS"
        )
        pe = result.phase_envelope
        assert pe is not None
        assert pe.cricondenbar_p is not None
        assert pe.cricondenbar_p > 0

    def test_srk_produces_phase_envelope(self, calc, nglike_mixture):
        result, _ = calc.calculate_with_fallback(
            nglike_mixture, 300, 5e6, preferred_backend="SRK"
        )
        assert result.phase_envelope is not None

    def test_pr_produces_phase_envelope(self, calc, nglike_mixture):
        result, _ = calc.calculate_with_fallback(
            nglike_mixture, 300, 5e6, preferred_backend="PR"
        )
        assert result.phase_envelope is not None

    def test_aga8_backend_produces_phase_envelope_via_coolprop(self, calc, methane_mixture):
        result, _ = calc.calculate_with_fallback(
            methane_mixture, 250, 1e6, preferred_backend="GERG-2008"
        )
        assert result.phase_envelope is not None

    def test_cricondenbar_is_max_pressure_of_primary_lobe(self, calc, nglike_mixture):
        """Cricondenbar is max pressure on primary (widest temp-range) lobe."""
        result, _ = calc.calculate_with_fallback(
            nglike_mixture, 300, 5e6, preferred_backend="HEOS"
        )
        pe = result.phase_envelope
        if pe is not None and pe.cricondenbar_p is not None:
            # cricondenbar should be within the phase envelope pressure range
            min_p = min(pe.pressure_pa)
            max_p = max(pe.pressure_pa)
            assert pe.cricondenbar_p >= min_p
            assert pe.cricondenbar_p <= max_p

    def test_phase_envelope_temperature_pressure_same_length(self, calc, methane_mixture):
        result, _ = calc.calculate_with_fallback(
            methane_mixture, 250, 1e6, preferred_backend="HEOS"
        )
        pe = result.phase_envelope
        assert pe is not None
        assert len(pe.temperature_k) == len(pe.pressure_pa)

    def test_multi_component_still_produces_envelope(self, calc):
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=80.0),
                GasComponent(name="Ethane", fraction=10.0),
                GasComponent(name="Propane", fraction=5.0),
                GasComponent(name="Nitrogen", fraction=3.0),
                GasComponent(name="CarbonDioxide", fraction=2.0),
            ],
            fraction_type="molar",
        )
        result, used = calc.calculate_with_fallback(
            mixture, 300, 1e6, preferred_backend="HEOS"
        )
        assert result.phase_envelope is not None
        assert used == "HEOS"

    def test_critical_point_extracted(self, calc, methane_mixture):
        result, _ = calc.calculate_with_fallback(
            methane_mixture, 250, 1e6, preferred_backend="HEOS"
        )
        pe = result.phase_envelope
        if pe is not None:
            assert pe.critical_t is not None
            assert pe.critical_p is not None
            assert pe.critical_t > 100
            assert pe.critical_p > 1e5

    def test_phase_envelope_via_aga8_uses_coolprop_fallback(self, calc, methane_mixture):
        """AGA8 doesn't have its own phase envelope; falls back to CoolProp."""
        result, _ = calc.calculate_with_fallback(
            methane_mixture, 250, 1e6, preferred_backend="GERG-2008"
        )
        assert result.phase_envelope is not None
        assert result.backend_used == "GERG-2008"


class TestComparisonTable:
    """Verify Z-factor comparison table has entries for all backends."""

    @pytest.fixture
    def calc(self):
        from natural_gas_main.models.calculator import COOLPROP_AVAILABLE
        if not COOLPROP_AVAILABLE:
            pytest.skip("CoolProp not available")
        return ThermoCalculator()

    @pytest.fixture
    def mixture(self):
        return GasMixture(
            components=[
                GasComponent(name="Methane", fraction=90.0),
                GasComponent(name="Ethane", fraction=10.0),
            ],
            fraction_type="molar",
        )

    def test_comparison_has_heos_srk_pr(self, calc, mixture):
        result, _ = calc.calculate_with_fallback(mixture, 300, 1e5, "HEOS")
        methods = {c.method for c in result.z_factor_comparison}
        for m in ["HEOS", "SRK", "PR"]:
            assert m in methods, f"{m} missing from comparison"

    def test_comparison_has_aga8_methods(self, calc, mixture):
        result, _ = calc.calculate_with_fallback(mixture, 300, 1e5, "HEOS")
        methods = {c.method for c in result.z_factor_comparison}
        for m in ["GERG-2008", "AGA8-Detail"]:
            assert m in methods, f"{m} missing from comparison"

    def test_comparison_has_standing_katz(self, calc, mixture):
        result, _ = calc.calculate_with_fallback(mixture, 300, 1e5, "HEOS")
        methods = {c.method for c in result.z_factor_comparison}
        assert "Standing-Katz ANN10" in methods
        assert "Dranchuk-Abou-Kassem" in methods

    def test_comparison_values_are_numeric(self, calc, mixture):
        result, _ = calc.calculate_with_fallback(mixture, 300, 1e5, "HEOS")
        for c in result.z_factor_comparison:
            if c.z_factor is not None:
                assert c.z_factor > 0, f"{c.method}: z_factor invalid"
                assert c.z_factor < 5, f"{c.method}: z_factor out of range"

    def test_comparison_negsim_if_available(self, calc, mixture):
        from natural_gas_main.models.neqsim_calculator import NEQSIM_AVAILABLE
        result, _ = calc.calculate_with_fallback(mixture, 300, 1e5, "HEOS")
        methods = {c.method for c in result.z_factor_comparison}
        if NEQSIM_AVAILABLE:
            assert "neqsim-gerg2008" in methods
        else:
            assert "neqsim-gerg2008" not in methods

    def test_comparison_with_isobutane_mixture(self, calc):
        """Isobutane should work with fixed neqsim gas mapping."""
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=90.0),
                GasComponent(name="isobutane", fraction=10.0),
            ],
            fraction_type="molar",
        )
        result, used = calc.calculate_with_fallback(mixture, 300, 1e5, "HEOS")
        assert result.z_factor_comparison is not None
        # At minimum, CoolProp methods should have values
        heos_found = any(c.method == "HEOS" and c.z_factor is not None
                        for c in result.z_factor_comparison)
        assert heos_found, "HEOS Z-factor should be present"
