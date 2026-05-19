"""
Smoke tests for the AGA8 (pyaga8) calculator integration.

Validates that GERG-2008 and AGA8-Detail calls work with simple mixtures.
"""

import math
import pytest

from natural_gas_main.models.aga8_calculator import calculate_aga8, PYAGA8_AVAILABLE


pytestmark = pytest.mark.skipif(
    not PYAGA8_AVAILABLE,
    reason="pyaga8 is not installed",
)


@pytest.fixture
def simple_mixture():
    from natural_gas_main.models.gas_data import GasComponent, GasMixture
    return GasMixture(
        components=[
            GasComponent(name="Methane", fraction=100.0),
        ],
        fraction_type="molar",
    )


class TestAga8Gerg2008:
    def test_gerg2008_returns_compressibility(self, simple_mixture):
        res = calculate_aga8(simple_mixture, 288.15, 101325.0, "GERG-2008")
        assert res is not None
        assert 0.5 < res.compressibility_factor < 1.5
        assert res.density > 0
        assert res.molar_mass > 0

    def test_gerg2008_returns_enthalpy(self, simple_mixture):
        res = calculate_aga8(simple_mixture, 288.15, 101325.0, "GERG-2008")
        assert res.enthalpy is not None

    def test_gerg2008_returns_cp_cv(self, simple_mixture):
        res = calculate_aga8(simple_mixture, 288.15, 101325.0, "GERG-2008")
        assert res.cp is not None
        assert res.cv is not None


class TestAga8Detail:
    def test_aga8_detail_returns_compressibility(self, simple_mixture):
        res = calculate_aga8(simple_mixture, 288.15, 101325.0, "AGA8-Detail")
        assert res is not None
        assert 0.5 < res.compressibility_factor < 1.5
        assert res.density > 0

    def test_aga8_detail_returns_entropy(self, simple_mixture):
        res = calculate_aga8(simple_mixture, 288.15, 101325.0, "AGA8-Detail")
        assert res.entropy is not None

    def test_aga8_detail_consistent_results(self, simple_mixture):
        """GERG-2008 and AGA8-Detail should give similar Z-factor results."""
        gerg = calculate_aga8(simple_mixture, 288.15, 101325.0, "GERG-2008")
        aga8 = calculate_aga8(simple_mixture, 288.15, 101325.0, "AGA8-Detail")
        rel_diff = abs(gerg.compressibility_factor - aga8.compressibility_factor)
        assert rel_diff < 0.1, f"Gerg Z={gerg.compressibility_factor}, AGA8 Z={aga8.compressibility_factor}"


class TestAga8InvalidInputs:
    def test_empty_mixture_raises(self):
        from natural_gas_main.models.gas_data import GasMixture
        with pytest.raises(ValueError):
            GasMixture(components=[], fraction_type="molar")

    def test_unknown_method_defaults_to_detail(self, simple_mixture):
        """Unknown method name falls through to AGA8-Detail."""
        res = calculate_aga8(simple_mixture, 288.15, 101325.0, "UNKNOWN-METHOD")
        assert res.compressibility_factor > 0
