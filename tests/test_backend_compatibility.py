"""Tests for backend-gas compatibility functions and non-AGA8 filtering."""

import pytest
from natural_gas_main.models.calculator import (
    check_gas_backend_support,
    get_unsupported_gases_for_backend,
    ThermoCalculator,
)
from natural_gas_main.models.gas_data import GasComponent, GasMixture
from natural_gas_main.models.aga8_calculator import AGA8_MAPPING


# ---------------------------------------------------------------------------
# check_gas_backend_support
# ---------------------------------------------------------------------------

class TestCheckGasBackendSupport:
    """Unit tests for check_gas_backend_support()."""

    def test_aga8_known_gas_returns_true(self):
        supported, reason = check_gas_backend_support("Methane", "GERG-2008")
        assert supported is True
        assert reason is None

    def test_aga8_unknown_gas_returns_false(self):
        supported, reason = check_gas_backend_support("Cyclopentane", "GERG-2008")
        assert supported is False
        assert "tanımlı değil" in reason

    def test_aga8_detail_same_as_gerg2008(self):
        r1 = check_gas_backend_support("Neopentane", "AGA8-Detail")
        r2 = check_gas_backend_support("Neopentane", "GERG-2008")
        assert r1 == r2

    def test_heos_supported_gas(self):
        supported, reason = check_gas_backend_support("Methane", "HEOS")
        assert supported is True

    def test_heos_cyclopentane_is_supported(self):
        supported, _ = check_gas_backend_support("Cyclopentane", "HEOS")
        assert supported is True

    def test_srk_always_supports(self):
        supported, reason = check_gas_backend_support("Cyclopentane", "SRK")
        assert supported is True
        assert reason is None

    def test_pr_always_supports(self):
        supported, reason = check_gas_backend_support("UnknownGas", "PR")
        assert supported is True

    def test_neqsim_gerg2008_supports_cyclopentane(self):
        supported, reason = check_gas_backend_support("Cyclopentane", "neqsim-gerg2008")
        assert supported is True

    def test_neqsim_srk_supports_neohexane(self):
        supported, _ = check_gas_backend_support("Neopentane", "neqsim-srk")
        assert supported is True

    def test_neqsim_unknown_gas_fails(self):
        supported, reason = check_gas_backend_support("FakeGasXYZ", "neqsim-srk")
        assert supported is False
        assert "veritabanında yok" in reason

    def test_case_insensitive_gas_name(self):
        supported, _ = check_gas_backend_support("METHANE", "GERG-2008")
        assert supported is True

    def test_all_aga8_mapped_gases_pass(self):
        for coolprop_name in AGA8_MAPPING:
            supported, reason = check_gas_backend_support(coolprop_name, "GERG-2008")
            assert supported is True, f"{coolprop_name} should be supported"


# ---------------------------------------------------------------------------
# get_unsupported_gases_for_backend
# ---------------------------------------------------------------------------

class TestGetUnsupportedGasesForBackend:
    """Unit tests for get_unsupported_gases_for_backend()."""

    def test_all_supported_returns_empty(self):
        result = get_unsupported_gases_for_backend(
            ["Methane", "Ethane", "Nitrogen"], "GERG-2008"
        )
        assert result == []

    def test_mixed_returns_only_unsupported(self):
        result = get_unsupported_gases_for_backend(
            ["Methane", "Cyclopentane", "Ethane", "Isohexane"], "GERG-2008"
        )
        assert result == ["Cyclopentane", "Isohexane"]

    def test_all_unsupported(self):
        result = get_unsupported_gases_for_backend(
            ["Cyclopentane", "Neopentane", "CycloHexane"], "GERG-2008"
        )
        assert len(result) == 3

    def test_srk_always_empty(self):
        result = get_unsupported_gases_for_backend(
            ["Cyclopentane", "FakeGas"], "SRK"
        )
        assert result == []

    def test_empty_list_returns_empty(self):
        result = get_unsupported_gases_for_backend([], "GERG-2008")
        assert result == []


# ---------------------------------------------------------------------------
# _has_non_aga8_components
# ---------------------------------------------------------------------------

class TestHasNonAga8Components:
    """Tests for _has_non_aga8_components()."""

    @pytest.fixture
    def calc(self):
        from natural_gas_main.models.calculator import COOLPROP_AVAILABLE
        import CoolProp.CoolProp as CP
        if not COOLPROP_AVAILABLE:
            pytest.skip("CoolProp not available")
        return ThermoCalculator()

    def test_aga8_only_mixture_returns_false(self, calc):
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=90.0),
                GasComponent(name="Ethane", fraction=5.0),
                GasComponent(name="Nitrogen", fraction=5.0),
            ],
            fraction_type="molar",
        )
        assert calc._has_non_aga8_components(mixture) is False

    def test_mixture_with_cyclopentane_returns_true(self, calc):
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=90.0),
                GasComponent(name="Cyclopentane", fraction=10.0),
            ],
            fraction_type="molar",
        )
        assert calc._has_non_aga8_components(mixture) is True

    def test_mixture_with_isohexane_returns_true(self, calc):
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=90.0),
                GasComponent(name="Isohexane", fraction=10.0),
            ],
            fraction_type="molar",
        )
        assert calc._has_non_aga8_components(mixture) is True

    def test_no_component_is_false(self, calc):
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=100.0),
            ],
            fraction_type="molar",
        )
        assert calc._has_non_aga8_components(mixture) is False


# ---------------------------------------------------------------------------
# _get_backend_order — non-AGA8 filtering
# ---------------------------------------------------------------------------

class TestGetBackendOrderNonAga8:
    """Verify that non-AGA8 components correctly exclude AGA8 backends."""

    @pytest.fixture
    def calc(self):
        from natural_gas_main.models.calculator import COOLPROP_AVAILABLE
        if not COOLPROP_AVAILABLE:
            pytest.skip("CoolProp not available")
        return ThermoCalculator()

    @pytest.fixture
    def aga8_mixture(self):
        return GasMixture(
            components=[
                GasComponent(name="Methane", fraction=90.0),
                GasComponent(name="Ethane", fraction=10.0),
            ],
            fraction_type="molar",
        )

    @pytest.fixture
    def non_aga8_mixture(self):
        return GasMixture(
            components=[
                GasComponent(name="Methane", fraction=90.0),
                GasComponent(name="Cyclopentane", fraction=10.0),
            ],
            fraction_type="molar",
        )

    def test_all_aga8_mixture_includes_gerg2008(self, calc, aga8_mixture):
        backends = calc._get_backend_order(aga8_mixture, "HEOS")
        assert "GERG-2008" in backends
        assert "AGA8-Detail" in backends

    def test_non_aga8_mixture_excludes_gerg2008(self, calc, non_aga8_mixture):
        backends = calc._get_backend_order(non_aga8_mixture, "HEOS")
        assert "GERG-2008" not in backends
        assert "AGA8-Detail" not in backends

    def test_non_aga8_preferred_gerg2008_excluded(self, calc, non_aga8_mixture):
        backends = calc._get_backend_order(non_aga8_mixture, "GERG-2008")
        assert "GERG-2008" not in backends
        assert "AGA8-Detail" not in backends

    def test_non_aga8_preferred_aga8_detail_excluded(self, calc, non_aga8_mixture):
        backends = calc._get_backend_order(non_aga8_mixture, "AGA8-Detail")
        assert "AGA8-Detail" not in backends
        assert "GERG-2008" not in backends

    def test_non_aga8_still_includes_coolprop(self, calc, non_aga8_mixture):
        backends = calc._get_backend_order(non_aga8_mixture, "HEOS")
        for b in ["HEOS", "SRK", "PR"]:
            assert b in backends, f"{b} should be in fallback list"

    def test_all_aga8_preferred_gerg2008_stays(self, calc, aga8_mixture):
        backends = calc._get_backend_order(aga8_mixture, "GERG-2008")
        assert backends[0] == "GERG-2008"
