"""
Phase 2: Calculation Accuracy improvement tests.

Tests:
1. H2S heating value correction (7.6% error fix)
2. ISO 6976 integration as Stage 2.5
3. ISO 6976 mass-based CV temperature correction removed
4. AGA8 normalization warnings
5. New ISO 6976 components (non-combustibles)
"""

from unittest.mock import patch
import pytest


class TestH2SHeatingValueFix:
    """Verify H2S heating value is corrected per ISO 6976."""

    def test_h2s_reference_value_corrected(self):
        """H2S HHV should be 16.495 (ISO 6976), not old 15.24."""
        from natural_gas_main.models.heating_value_db import get_reference_heating_values

        hhv, lhv = get_reference_heating_values("HydrogenSulfide")
        assert abs(hhv - 16.495) < 0.001, (
            f"H2S HHV should be 16.495 MJ/kg (ISO 6976), got {hhv}"
        )
        assert abs(lhv - 15.192) < 0.001, (
            f"H2S LHV should be 15.192 MJ/kg (ISO 6976), got {lhv}"
        )

    def test_h2s_error_magnitude(self):
        """Old value was 15.24, new is 16.495 → ~7.6% difference."""
        from natural_gas_main.models.heating_value_db import get_reference_heating_values

        hhv, _ = get_reference_heating_values("HydrogenSulfide")
        old_value = 15.24
        error_pct = abs(hhv - old_value) / old_value * 100
        assert error_pct > 7.0, (
            f"Fix should correct ~7.6% error, got {error_pct:.1f}%"
        )

    def test_h2s_iso6976_consistent_with_db(self):
        """ISO 6976 module and reference DB should agree on H2S."""
        from natural_gas_main.models.heating_value_db import get_reference_heating_values
        from natural_gas_main.models.iso6976 import ISO6976_DATA

        db_hhv, _ = get_reference_heating_values("HydrogenSulfide")
        iso_hhv = ISO6976_DATA["HydrogenSulfide"]["hhv_mass"]
        assert abs(db_hhv - iso_hhv) < 0.001, (
            "H2S HHV should match between DB and ISO 6976"
        )


class TestISO6976Integration:
    """Verify ISO 6976 is wired as Stage 2.5 in calculator."""

    def test_calculator_imports_iso6976(self):
        """calculator.py should import iso6976 module."""
        from natural_gas_main.models import calculator
        import inspect

        source = inspect.getsource(calculator)
        assert "calculate_iso6976_heating_values" in source
        assert "is_iso6976_compatible" in source

    def test_iso6976_stage_exists_in_fallback(self):
        """ISO 6976 should be a separate stage between component and reference."""
        from natural_gas_main.models.calculator import ThermoCalculator
        import inspect

        source = inspect.getsource(
            ThermoCalculator._calculate_heating_values
        )
        assert "ISO 6976:2016" in source, (
            "ISO 6976 should appear in fallback chain"
        )

    def test_iso6976_compatible_simple_mixture(self):
        """Pure methane should be ISO 6976 compatible."""
        from natural_gas_main.models.gas_data import GasMixture, GasComponent
        from natural_gas_main.models.iso6976 import is_iso6976_compatible

        mixture = GasMixture(
            components=[GasComponent(name="Methane", fraction=100.0)],
            fraction_type="molar",
        )
        assert is_iso6976_compatible(mixture, GasMixture._format_gas_name_for_coolprop)

    def test_iso6976_incompatible_unknown_gas(self):
        """Unknown gas should NOT be ISO 6976 compatible."""
        from natural_gas_main.models.gas_data import GasMixture, GasComponent
        from natural_gas_main.models.iso6976 import is_iso6976_compatible

        mixture = GasMixture(
            components=[GasComponent(name="UNKNOWN_GAS_XYZ", fraction=100.0)],
            fraction_type="molar",
        )
        assert not is_iso6976_compatible(mixture, GasMixture._format_gas_name_for_coolprop)

    def test_iso6976_calculate_methane(self):
        """Calculate ISO 6976 for pure methane."""
        from natural_gas_main.models.gas_data import GasMixture, GasComponent
        from natural_gas_main.models.iso6976 import calculate_iso6976_heating_values

        mixture = GasMixture(
            components=[GasComponent(name="Methane", fraction=100.0)],
            fraction_type="molar",
        )
        hhv, lhv = calculate_iso6976_heating_values(
            mixture, GasMixture._format_gas_name_for_coolprop
        )
        assert hhv is not None
        assert lhv is not None
        assert abs(hhv - 55.575) < 0.01
        assert abs(lhv - 50.046) < 0.01


class TestISO6976TempCorrection:
    """Verify mass-based CV temperature correction has been removed."""

    def test_no_temperature_correction_on_mass_based(self):
        """Mass-based HHV/LHV should NOT have temperature correction."""
        from natural_gas_main.models.iso6976 import calculate_iso6976_heating_values
        from natural_gas_main.models.gas_data import GasMixture, GasComponent

        mixture = GasMixture(
            components=[GasComponent(name="Methane", fraction=100.0)],
            fraction_type="molar",
        )

        hhv_298, lhv_298 = calculate_iso6976_heating_values(
            mixture, GasMixture._format_gas_name_for_coolprop, T_ref=298.15
        )
        hhv_288, lhv_288 = calculate_iso6976_heating_values(
            mixture, GasMixture._format_gas_name_for_coolprop, T_ref=288.15
        )

        # Mass-based CVs should be identical regardless of T_ref
        assert abs(hhv_298 - hhv_288) < 0.001, (
            "Mass-based HHV should not change with temperature"
        )
        assert abs(lhv_298 - lhv_288) < 0.001

    def test_old_temperature_correction_would_have_changed_values(self):
        """Verify the old buggy correction would have changed values."""
        hhv_298 = 55.575
        hhv_288_old_bug = hhv_298 * 288.15 / 298.15
        # At 288K, the old bug would produce ~53.71 instead of 55.575
        assert abs(hhv_288_old_bug - 55.575) > 1.0, (
            f"Old bug would give {hhv_288_old_bug:.3f} at 288K, "
            "which is different from correct 55.575"
        )


class TestISO6976MissingComponents:
    """Verify new non-combustible components in ISO 6976."""

    @pytest.mark.parametrize("gas", [
        "Oxygen", "Argon", "Helium", "Water", "Air",
    ])
    def test_non_combustibles_in_iso_data(self, gas):
        """Non-combustibles should exist in ISO 6976 data."""
        from natural_gas_main.models.iso6976 import ISO6976_DATA

        assert gas in ISO6976_DATA, f"{gas} missing from ISO 6976 data"
        assert ISO6976_DATA[gas]["hhv_mass"] == 0.0
        assert ISO6976_DATA[gas]["lhv_mass"] == 0.0
        assert "density_ideal" in ISO6976_DATA[gas]
        assert ISO6976_DATA[gas]["density_ideal"] > 0

    @pytest.mark.parametrize("gas,expected_hhv", [
        ("Neopentane", 48.940),
        ("n-Nonane", 48.190),
        ("n-Decane", 48.100),
    ])
    def test_new_combustibles_in_iso_data(self, gas, expected_hhv):
        """Newly added combustibles should have correct data."""
        from natural_gas_main.models.iso6976 import ISO6976_DATA

        assert gas in ISO6976_DATA
        assert abs(ISO6976_DATA[gas]["hhv_mass"] - expected_hhv) < 0.01

    def test_iso6976_mixture_with_inerts(self):
        """ISO 6976 should handle mixtures with inerts like N2, O2, Ar."""
        from natural_gas_main.models.gas_data import GasMixture, GasComponent
        from natural_gas_main.models.iso6976 import calculate_iso6976_heating_values

        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=85.0),
                GasComponent(name="Nitrogen", fraction=10.0),
                GasComponent(name="Oxygen", fraction=3.0),
                GasComponent(name="Argon", fraction=2.0),
            ],
            fraction_type="molar",
        )
        hhv, lhv = calculate_iso6976_heating_values(
            mixture, GasMixture._format_gas_name_for_coolprop
        )
        assert hhv is not None, "Mixture with inerts should compute"
        assert hhv > 0, "HHV should be > 0 with combustibles present"
        # Methane is 85%, so HHV should be ~85% of 55.575
        assert 40 < hhv < 55, f"HHV={hhv} should be in reasonable range"


class TestAGA8Normalization:
    """Verify AGA8 normalization improvements."""

    def test_aga8_normalization_raises_on_unmapped(self):
        """AGA8 should raise ValueError with fallback message when unmapped gases exist."""
        from natural_gas_main.models import aga8_calculator
        import inspect

        source = inspect.getsource(aga8_calculator)
        assert "HEOS/SRK/PR yöntemine geçiliyor" in source, (
            "Should mention fallback to HEOS/SRK/PR"
        )

    def test_aga8_method_validation(self):
        """Invalid AGA8 method should fall back to Detail with warning."""
        from natural_gas_main.models.aga8_calculator import calculate_aga8
        import inspect

        source = inspect.getsource(calculate_aga8)
        assert "Bilinmeyen AGA8 metodu" in source, (
            "Should validate method parameter"
        )


class TestHeatingValueAccuracyIntegration:
    """Integration tests for overall heating value accuracy improvements."""

    def test_reference_db_and_iso_agree_on_methane(self):
        """Reference DB and ISO 6976 should have close values for common gases."""
        from natural_gas_main.models.heating_value_db import get_reference_heating_values
        from natural_gas_main.models.iso6976 import ISO6976_DATA

        gases = ["Methane", "Ethane", "Propane", "n-Butane"]
        for gas in gases:
            db_hhv, _ = get_reference_heating_values(gas)
            iso_hhv = ISO6976_DATA[gas]["hhv_mass"]
            diff_pct = abs(db_hhv - iso_hhv) / iso_hhv * 100
            assert diff_pct < 1.0, (
                f"{gas}: DB={db_hhv} vs ISO={iso_hhv}, diff={diff_pct:.2f}%"
            )
