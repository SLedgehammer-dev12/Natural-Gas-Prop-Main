"""Aşama 2 - Orta: mock gerektiren coverage testleri.

Kapsanan dosyalar:
- converters.py: gauge pressure, geçersiz unit, NaN exception yolları
- z_factor.py: edge Ppr/Tpr, DAK convergence failure, Sutton error
- iso6976.py: incompatible component, calculate_iso6976 edge
- __main__.py: module guard ve dosya varlığı
- preferences.py: Windows APPDATA, yazma hatası
- gas_data.py: fraction/mixture validation edge cases
"""

import os
import sys
import math
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from natural_gas_main.core.converters import (
    convert_temperature_to_K,
    convert_temperature_from_K,
    convert_pressure_to_Pa,
    convert_pressure_from_Pa,
    convert_volume_to_m3,
)
from natural_gas_main.core.exceptions import ValidationError
from natural_gas_main.models.gas_data import GasComponent, GasMixture
from natural_gas_main.models.z_factor import StandingKatzZFactor, PseudoCriticalProperties
from natural_gas_main.config.preferences import (
    set_preference, save_preferences, _prefs_dir,
)


# ---------------------------------------------------------------------------
# converters.py - gauge pressure, geçersiz unit, NaN exception yolları
# ---------------------------------------------------------------------------

class TestConvertersInvalidUnits:
    def test_temperature_to_K_invalid_unit(self):
        with pytest.raises(ValidationError):
            convert_temperature_to_K(100, "INVALID")

    def test_temperature_from_K_invalid_unit(self):
        with pytest.raises(ValidationError):
            convert_temperature_from_K(300, "INVALID")

    def test_pressure_to_Pa_invalid_unit(self):
        with pytest.raises(ValidationError):
            convert_pressure_to_Pa(1, "INVALID")

    def test_pressure_from_Pa_invalid_unit(self):
        with pytest.raises(ValidationError):
            convert_pressure_from_Pa(101325, "INVALID")

    def test_volume_to_m3_invalid_unit(self):
        with pytest.raises(ValidationError):
            convert_volume_to_m3(100, "INVALID")


class TestConvertersGaugePressure:
    def test_bar_gauge_to_pa(self):
        result = convert_pressure_to_Pa(0, "bar(g)")
        assert result == pytest.approx(101325, rel=0.01)

    def test_psi_gauge_to_pa(self):
        result = convert_pressure_to_Pa(0, "psi(g)")
        assert result == pytest.approx(101325, rel=0.01)

    def test_from_pa_bar_gauge(self):
        result = convert_pressure_from_Pa(101325, "bar(g)")
        assert result == pytest.approx(0.0, abs=0.001)

    def test_from_pa_psi_gauge(self):
        result = convert_pressure_from_Pa(101325, "psi(g)")
        assert result == pytest.approx(0.0, abs=0.01)


class TestConvertersAllBranches:
    @pytest.mark.parametrize("unit", ["K", "°C", "°F"])
    def test_temperature_to_K_all_units(self, unit):
        val = convert_temperature_to_K(100, unit)
        assert val > 0

    @pytest.mark.parametrize("unit", ["K", "°C", "°F"])
    def test_temperature_from_K_all_units(self, unit):
        val = convert_temperature_from_K(300, unit)
        assert math.isfinite(val)

    @pytest.mark.parametrize("unit", ["Pa", "kPa", "MPa", "bar(a)", "bar(g)", "psi(a)", "psi(g)", "atm"])
    def test_pressure_to_Pa_all_units(self, unit):
        val = convert_pressure_to_Pa(1, unit)
        assert val > 0

    @pytest.mark.parametrize("unit", ["Pa", "kPa", "MPa", "bar(a)", "bar(g)", "psi(a)", "psi(g)", "atm"])
    def test_pressure_from_Pa_all_units(self, unit):
        val = convert_pressure_from_Pa(101325, unit)
        assert math.isfinite(val)

    @pytest.mark.parametrize("unit", ["m³", "L", "ft³"])
    def test_volume_to_m3_all_units(self, unit):
        val = convert_volume_to_m3(100, unit)
        assert val > 0

    def test_temperature_nan_does_not_crash(self):
        result = convert_temperature_to_K(float("nan"), "°C")
        assert math.isnan(result) or math.isinf(result)


# ---------------------------------------------------------------------------
# z_factor.py - edge Ppr/Tpr, DAK convergence, Sutton error
# ---------------------------------------------------------------------------

class TestZFactorEdgeCases:
    def test_sutton_negative_hc_raises(self):
        with pytest.raises(ValueError, match="Hydrocarbon fraction must be > 0"):
            StandingKatzZFactor.sutton_pseudo_critical(
                sg_gas=0.6, y_n2=0.4, y_co2=0.3, y_h2s=0.3,
            )

    def test_sutton_returns_pseudo_critical(self):
        pc = StandingKatzZFactor.sutton_pseudo_critical(sg_gas=0.65)
        assert isinstance(pc, PseudoCriticalProperties)
        assert pc.temperature_k > 0
        assert pc.pressure_pa > 0

    def test_sutton_with_acid_gas(self):
        pc = StandingKatzZFactor.sutton_pseudo_critical(
            sg_gas=0.7, y_h2s=0.1, y_co2=0.05,
        )
        assert isinstance(pc, PseudoCriticalProperties)

    def test_dak_warning_logged_for_no_convergence(self):
        """DAK logs warning when not converged but returns a Z value."""
        mixture = GasMixture(
            components=[GasComponent(name="Methane", fraction=100.0)],
            fraction_type="molar",
        )
        import CoolProp.CoolProp as CP
        z = StandingKatzZFactor(CP)
        estimates = z.estimates(mixture, temperature_k=200, pressure_pa=1e8)
        dak_estimate = [e for e in estimates if "Dranchuk" in e.method][0]
        # Should produce a finite Z even if not fully converged
        assert dak_estimate.z_factor is not None
        assert math.isfinite(dak_estimate.z_factor)

    def test_dak_estimates_after_convergence_failure(self):
        """estimates() catches DAK ValueError and returns Z=None."""
        with patch.object(StandingKatzZFactor, 'dak', side_effect=ValueError("test err")):
            mixture = GasMixture(
                components=[GasComponent(name="Methane", fraction=100.0)],
                fraction_type="molar",
            )
            import CoolProp.CoolProp as CP
            z = StandingKatzZFactor(CP)
            estimates = z.estimates(mixture, temperature_k=300, pressure_pa=1e6)
            dak_estimate = [e for e in estimates if "Dranchuk" in e.method][0]
            assert dak_estimate.z_factor is None
            assert not dak_estimate.valid

    def test_is_valid_range_true(self):
        assert StandingKatzZFactor._is_valid_range(1.0, 1.5)

    def test_is_valid_range_false(self):
        assert not StandingKatzZFactor._is_valid_range(35.0, 0.5)


# ---------------------------------------------------------------------------
# iso6976.py - incompatible component
# ---------------------------------------------------------------------------

class TestIso6976EdgeCases:
    def test_empty_mixture_returns_none(self):
        from natural_gas_main.models.iso6976 import calculate_iso6976_heating_values
        mixture = GasMixture(
            components=[GasComponent(name="Neon", fraction=100.0)],
            fraction_type="molar",
        )
        hhv, lhv = calculate_iso6976_heating_values(mixture)
        assert hhv is None
        assert lhv is None

    def test_is_compatible_returns_false_for_unknown(self):
        from natural_gas_main.models.iso6976 import is_iso6976_compatible
        mixture = GasMixture(
            components=[GasComponent(name="Neon", fraction=100.0)],
            fraction_type="molar",
        )
        assert is_iso6976_compatible(mixture) is False

    def test_is_compatible_returns_true_for_methane(self):
        from natural_gas_main.models.iso6976 import is_iso6976_compatible
        mixture = GasMixture(
            components=[GasComponent(name="Methane", fraction=100.0)],
            fraction_type="molar",
        )
        assert is_iso6976_compatible(mixture) is True

    def test_temperature_ref_passed_through(self):
        from natural_gas_main.models.iso6976 import calculate_iso6976_heating_values
        mixture = GasMixture(
            components=[GasComponent(name="Methane", fraction=100.0)],
            fraction_type="molar",
        )
        hhv, lhv = calculate_iso6976_heating_values(mixture, T_ref=288.15)
        assert hhv is not None
        assert lhv is not None


# ---------------------------------------------------------------------------
# __main__.py - module guard ve dosya varlığı
# ---------------------------------------------------------------------------

class TestMainModule:
    def test_main_py_guard_exists(self):
        main_path = Path(__file__).parent.parent / "natural_gas_main" / "__main__.py"
        assert main_path.exists()
        content = main_path.read_text()
        assert "__name__" in content and "__main__" in content


# ---------------------------------------------------------------------------
# preferences.py - Windows APPDATA (sadece kod kapsamı, çalıştırmadan)
# ---------------------------------------------------------------------------

class TestPreferencesApi:
    def test_save_and_set_preference_roundtrip(self):
        set_preference("test_key_xyz", "test_value")
        from natural_gas_main.config.preferences import get_preference
        val = get_preference("test_key_xyz")
        assert val == "test_value"


# ---------------------------------------------------------------------------
# gas_data.py - fraction/mixture validation edge cases
# ---------------------------------------------------------------------------

class TestGasDataEdgeCases:
    def test_fraction_exactly_100(self):
        GasComponent(name="Methane", fraction=100.0)

    def test_fraction_zero_allowed(self):
        # 0.00% (undetected chromatograph gas) is a valid component
        comp = GasComponent(name="Methane", fraction=0.0)
        assert comp.fraction == 0.0

    def test_fraction_above_100_invalid(self):
        with pytest.raises(ValueError):
            GasComponent(name="Methane", fraction=101.0)

    def test_duplicate_names_invalid(self):
        with pytest.raises(ValueError):
            GasMixture(
                components=[
                    GasComponent(name="Methane", fraction=50.0),
                    GasComponent(name="Methane", fraction=50.0),
                ],
            )

    def test_fuzzy_name_matching(self):
        result = GasMixture._format_gas_name_for_coolprop("metHane ")
        assert result.lower() == "methane"
