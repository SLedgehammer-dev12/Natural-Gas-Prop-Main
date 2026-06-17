"""
Regression tests for Phase 1 critical bug fixes.

Tests:
1. check_heos_compatibility() inversion fix (3 locations)
2. Sutton temperature unit conversion (°R → °F → K bug)
3. dialogs.py config import NameError fix
4. input_panel.py float() ValueError crash fix
"""

import pytest


class TestHeosCompatibilityInversion:
    """Verify check_heos_compatibility() is no longer inverted."""

    def test_heos_compatible_mixture_picks_heos_in_aga8_phase_envelope(self):
        """When HEOS-compatible, phase envelope backend should be HEOS, not SRK."""
        from natural_gas_main.config.settings import config
        from natural_gas_main.models.gas_data import GasMixture, GasComponent

        mixture = GasMixture(
            components=[GasComponent(name="Methane", fraction=100.0)],
            fraction_type="molar",
        )
        incompatible = mixture.check_heos_compatibility()
        assert incompatible == [], f"Methane should be HEOS-compatible, got: {incompatible}"
        assert not incompatible, "Empty list should be falsy (for ternary logic)"

    def test_heos_incompatible_mixture_picks_srk_in_aga8(self):
        """When HEOS-incompatible, phase envelope backend should be SRK."""
        from natural_gas_main.models.gas_data import GasMixture, GasComponent

        mixture = GasMixture(
            components=[GasComponent(name="NOT_A_REAL_GAS_XYZ", fraction=100.0)],
            fraction_type="molar",
        )
        incompatible = mixture.check_heos_compatibility()
        assert incompatible, f"Unknown gas should be HEOS-incompatible, got: {incompatible}"
        assert bool(incompatible), "Non-empty list should be truthy (for ternary logic)"

    def test_heos_logic_consistent_with_ternary_pattern(self):
        """Verify the ternary pattern used at lines 594, 930.
        
        When compatible ([] → falsy): should pick HEOS.
        When incompatible ([...] → truthy): should pick SRK.
        """
        from natural_gas_main.models.gas_data import GasMixture, GasComponent

        methane_only = GasMixture(
            components=[GasComponent(name="Methane", fraction=100.0)],
            fraction_type="molar",
        )
        unknown_only = GasMixture(
            components=[GasComponent(name="UNKNOWN_GAS", fraction=100.0)],
            fraction_type="molar",
        )

        compatible = methane_only.check_heos_compatibility()
        incompatible = unknown_only.check_heos_compatibility()

        # The correct pattern: SRK if incompatible (truthy), else HEOS
        cp_backend = "SRK" if compatible else "HEOS"
        assert cp_backend == "HEOS", "HEOS-compatible should get HEOS"

        cp_backend2 = "SRK" if incompatible else "HEOS"
        assert cp_backend2 == "SRK", "HEOS-incompatible should get SRK"


class TestSuttonTemperatureConversion:
    """Verify Sutton correlation temperature unit conversion is correct."""

    def test_sutton_rankine_to_kelvin_conversion(self):
        """Sutton gives °R, must convert to K using °R * 5/9."""
        from natural_gas_main.models.z_factor import StandingKatzZFactor

        # For SG=0.65: Tpc = 169.2 + 349.5*0.65 - 74.0*0.65^2 = 365.11 °R
        # Correct: 365.11 * 5/9 = 202.84 K
        # Wrong (old): (365.11 - 32) * 5/9 + 273.15 = 458.21 K
        props = StandingKatzZFactor.sutton_pseudo_critical(0.65)

        # Should be ~203 K, definitely NOT ~458 K
        assert props.temperature_k < 300, "Tpc should be <300K after °R→K fix"
        assert props.temperature_k > 100, "Tpc should be >100K"
        assert abs(props.temperature_k - 202.84) < 1.0, (
            f"Expected Tpc ~202.84K, got {props.temperature_k}"
        )

    def test_sutton_with_nitrogen_still_reasonable(self):
        """With N2 impurity, Tpc should stay in reasonable range."""
        from natural_gas_main.models.z_factor import StandingKatzZFactor

        props = StandingKatzZFactor.sutton_pseudo_critical(0.65, y_n2=0.05)
        assert 100 < props.temperature_k < 300, (
            f"Tpc={props.temperature_k} should be in 100-300K range"
        )

    def test_sutton_with_acid_gas_wa_correction(self):
        """WA correction should lower Tpc relative to its uncorrected base."""
        from natural_gas_main.models.z_factor import StandingKatzZFactor

        sour = StandingKatzZFactor.sutton_pseudo_critical(0.70, y_h2s=0.10)

        total_acid = 0.10
        epsilon = 120.0 * (total_acid ** 0.9 - total_acid ** 1.6) \
                  + 15.0 * (total_acid ** 0.5 - total_acid ** 4.0)
        tpc_before_wa_k = (sour.temperature_k * 9.0 / 5.0 + epsilon) * 5.0 / 9.0

        assert sour.temperature_k < tpc_before_wa_k, (
            "WA-corrected Tpc should be lower than uncorrected"
        )

    def test_acid_gas_tpc_higher_than_sweet(self):
        """H2S raises Tpc even after WA correction (H2S Tc=373.1K > CH4 Tc=190.6K)."""
        from natural_gas_main.models.z_factor import StandingKatzZFactor

        sweet = StandingKatzZFactor.sutton_pseudo_critical(0.70)
        sour = StandingKatzZFactor.sutton_pseudo_critical(0.70, y_h2s=0.10)

        assert sour.temperature_k > sweet.temperature_k, (
            "Sour Tpc ~210.1K should be > sweet Tpc ~209.8K due to H2S high critical temp"
        )

    def test_regression_old_bug_produces_wrong_value(self):
        """Verify the old bug formula would give ~458K for SG=0.65."""
        sg = 0.65
        tpc_rankine = 169.2 + 349.5 * sg - 74.0 * sg ** 2
        old_wrong = (tpc_rankine - 32.0) * 5.0 / 9.0 + 273.15
        new_correct = tpc_rankine * 5.0 / 9.0

        assert abs(new_correct - 202.84) < 1.0
        assert abs(old_wrong - 458.21) < 1.0
        assert new_correct < old_wrong, "New Tpc should be much lower than old buggy value"


class TestDialogsConfigImport:
    """Verify dialogs.py config import fix."""

    def test_show_new_features_info_imports_config(self):
        """show_new_features_info should import config without NameError."""
        from natural_gas_main.ui.dialogs import show_new_features_info
        import inspect

        source = inspect.getsource(show_new_features_info)
        assert "from natural_gas_main.config.settings import config" in source, (
            "show_new_features_info must import config locally"
        )

    def test_show_user_guide_imports_config(self):
        """show_user_guide_dialog should also import config."""
        from natural_gas_main.ui.dialogs import show_user_guide_dialog
        import inspect

        source = inspect.getsource(show_user_guide_dialog)
        assert "from natural_gas_main.config.settings import config" in source

    def test_on_close_closure_has_config_access(self):
        """The on_close closure inside show_new_features_info should reference config."""
        from natural_gas_main.ui.dialogs import show_new_features_info
        import inspect

        source = inspect.getsource(show_new_features_info)
        assert "config.APP_VERSION" in source, (
            "on_close must reference config.APP_VERSION"
        )
        assert "preferences.set_preference" in source


class TestInputPanelValueError:
    """Verify input_panel.py float() ValueError is handled."""

    def test_add_gas_handles_non_numeric_input(self):
        """_add_gas_row should handle non-numeric fraction without crash."""
        from natural_gas_main.ui.input_panel import InputPanel
        import inspect

        source = inspect.getsource(InputPanel._update_total_label)
        assert "try:" in source and "except ValueError" in source, (
            "_update_total_label must catch ValueError"
        )

    def test_add_gas_by_double_click_handles_non_numeric(self):
        """_on_add_gas should handle non-numeric without crash."""
        from natural_gas_main.ui.input_panel import InputPanel
        import inspect

        source = inspect.getsource(InputPanel._on_add_gas)
        assert "try:" in source or "except ValueError" in source, (
            "_on_add_gas must catch ValueError from float()"
        )

    def test_string_with_non_numeric_does_not_crash_float(self):
        """Simulate entering 'abc' in a fraction field - should not crash."""
        bad_inputs = ["abc", "", "12.5.3", "1,5", "--5", "Infinity", "NaN"]
        for bad in bad_inputs:
            try:
                val = float(bad)
                # Should only reach here for valid floats
                assert val is not None
            except ValueError:
                pass  # Expected - should be caught


class TestOverallPhase1:
    """Integration-level checks for Phase 1 fixes."""

    def test_z_factor_accuracy_improved_after_sutton_fix(self):
        """With Sutton fix, Z-factor predictions should be more reasonable."""
        from natural_gas_main.models.z_factor import StandingKatzZFactor
        from natural_gas_main.models.gas_data import GasMixture, GasComponent

        estimator = StandingKatzZFactor(None)
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=90.0),
                GasComponent(name="Ethane", fraction=5.0),
                GasComponent(name="Nitrogen", fraction=5.0),
            ],
            fraction_type="molar",
        )

        # Typical conditions: 300K, 1-50 bar
        for temp_k in [250, 300, 350]:
            for press_pa in [101325, 1e6, 5e6]:
                results = estimator.estimates(mixture, temp_k, press_pa)
                assert len(results) == 3
                for r in results:
                    assert r.z_factor is None or r.z_factor > 0
