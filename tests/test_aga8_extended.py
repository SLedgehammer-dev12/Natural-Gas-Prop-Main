"""Tests for AGA8 normalization warnings and behavior."""

import pytest
from natural_gas_main.models.aga8_calculator import (
    PYAGA8_AVAILABLE,
    AGA8_MAPPING,
    calculate_aga8,
)
from natural_gas_main.models.gas_data import GasComponent, GasMixture
from natural_gas_main.core.exceptions import BackendNotAvailableError


pytestmark = pytest.mark.skipif(not PYAGA8_AVAILABLE, reason="pyaga8 not installed")


class TestAga8Mapping:
    def test_all_methane_maps_correctly(self):
        """Methane should map to methane."""
        mixture = GasMixture(
            components=[GasComponent(name="Methane", fraction=100.0)],
            fraction_type="molar",
        )
        result = calculate_aga8(mixture, 300.0, 101325.0, "GERG-2008")
        assert result.compressibility_factor > 0

    def test_ethane_maps(self):
        """Ethane should map correctly."""
        mixture = GasMixture(
            components=[GasComponent(name="Ethane", fraction=100.0)],
            fraction_type="molar",
        )
        result = calculate_aga8(mixture, 300.0, 101325.0, "GERG-2008")
        assert result.compressibility_factor > 0

    def test_propane_aliases(self):
        """Both 'Propane' and 'n-Propane' should map to propane."""
        for name in ["Propane", "n-Propane"]:
            mixture = GasMixture(
                components=[GasComponent(name=name, fraction=100.0)],
                fraction_type="molar",
            )
            result = calculate_aga8(mixture, 300.0, 101325.0, "GERG-2008")
            assert result.density > 0

    def test_nitrogen_carbondioxide_mixture(self):
        """Mixture of inerts (no hydrocarbons)."""
        mixture = GasMixture(
            components=[
                GasComponent(name="Nitrogen", fraction=50.0),
                GasComponent(name="CarbonDioxide", fraction=50.0),
            ],
            fraction_type="molar",
        )
        result = calculate_aga8(mixture, 300.0, 101325.0, "GERG-2008")
        assert result.compressibility_factor > 0

    def test_aga8_detail_method(self):
        """AGA8-Detail method should also work."""
        mixture = GasMixture(
            components=[GasComponent(name="Methane", fraction=100.0)],
            fraction_type="molar",
        )
        result = calculate_aga8(mixture, 300.0, 101325.0, "AGA8-Detail")
        assert result.compressibility_factor > 0

    def test_mixture_with_unmapped_component(self):
        """Mixture with an unmapped gas should raise if total < 0.95."""
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=30.0),
                GasComponent(name="Unobtanium", fraction=70.0),
            ],
            fraction_type="molar",
        )
        with pytest.raises(ValueError, match="Atlanan"):
            calculate_aga8(mixture, 300.0, 101325.0, "GERG-2008")

    def test_high_pressure(self):
        """Test at high pressure."""
        mixture = GasMixture(
            components=[GasComponent(name="Methane", fraction=100.0)],
            fraction_type="molar",
        )
        result = calculate_aga8(mixture, 350.0, 20e6, "GERG-2008")
        assert result.compressibility_factor > 0

    def test_enthalpy_consistency(self):
        """Enthalpy and internal energy should be consistent (h > u for gas)."""
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=90.0),
                GasComponent(name="Ethane", fraction=10.0),
            ],
            fraction_type="molar",
        )
        result = calculate_aga8(mixture, 350.0, 5e6, "GERG-2008")
        assert result.enthalpy > result.internal_energy

    def test_mapping_coverage(self):
        """All gases in AGA8_MAPPING should have valid keys."""
        for key in AGA8_MAPPING:
            assert isinstance(key, str)
            assert len(key) > 0
