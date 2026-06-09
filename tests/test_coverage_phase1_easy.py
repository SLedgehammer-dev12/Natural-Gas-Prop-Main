"""Aşama 1 — Kolay: coverage için temel testler (hiç mock yok).

Kapsanan dosyalar:
- calculation_result.py: to_display_list tüm branşlar (SI/Imperial, None, fallback)
- exceptions.py: tüm exception sınıfları tüm parametre kombinasyonları
- settings.py: REPO_URL property
- heating_value_db.py: case-insensitive match, get_all_reference_gases
- result_unit_converter.py: geçersiz target_unit
"""

import math
import pytest
from typing import List, Tuple, Optional

from natural_gas_main.models.calculation_result import (
    CalculationResult,
    ActualConditionResults,
    StandardConditionResults,
    HeatingValues,
    VolumeConversion,
    HydrateResults,
    PhaseEnvelopeData,
    ZFactorComparison,
)
from natural_gas_main.core.exceptions import (
    BackendNotAvailableError,
    MixtureCompatibilityError,
    HeatingValueError,
    ValidationError,
    CalculationConvergenceError,
    StateUpdateError,
)
from natural_gas_main.utils.result_unit_converter import ResultUnitConverter
from natural_gas_main.models.heating_value_db import (
    get_reference_heating_values,
    get_all_reference_gases,
)
from natural_gas_main.config.settings import config


# ---------------------------------------------------------------------------
# calculation_result.py — to_display_list tüm branşlar
# ---------------------------------------------------------------------------

@pytest.fixture
def base_actual():
    return ActualConditionResults(
        temperature=300.0,
        pressure=1e6,
        density=10.0,
        molar_mass=0.018,
        compressibility_factor=0.95,
        internal_energy=-100.0,
        enthalpy=50.0,
        entropy=5.0,
        cp=2.0,
        cv=1.5,
        isentropic_exponent=1.33,
        speed_of_sound=400.0,
    )


@pytest.fixture
def base_standard():
    return StandardConditionResults(
        reference_temperature=288.15,
        reference_pressure=101325.0,
        density_std=0.8,
        specific_gravity=0.65,
    )


@pytest.fixture
def base_heating():
    return HeatingValues(
        calculation_method="HEOS Builtin",
        hhv_mass=55.0,
        lhv_mass=50.0,
        hhv_volume=38.0,
        lhv_volume=34.0,
        wobbe_index=50.0,
        hhv_btu_scf=1020.0,
    )


@pytest.fixture
def base_volume():
    return VolumeConversion(
        actual_volume=100.0,
        mass=80.0,
        standard_volume=95.0,
        normal_volume=90.0,
    )


@pytest.fixture
def base_hydrate():
    return HydrateResults(
        operating_temperature=280.0,
        operating_pressure=5e6,
        specific_gravity=0.6,
        t_hydrate_hammerschmidt=290.0,
        t_hydrate_motiee=288.0,
        t_hydrate_towler_mokhatab=287.0,
        t_hydrate_average=288.3,
        risk_hammerschmidt=True,
        risk_motiee=False,
        risk_towler_mokhatab=True,
        risk_average=True,
    )


class TestToDisplayListSI:
    def test_full_result_si(self, base_actual, base_standard, base_heating, base_volume, base_hydrate):
        result = CalculationResult(
            backend_used="HEOS",
            actual=base_actual,
            standard=base_standard,
            heating=base_heating,
            volume_conversion=base_volume,
            hydrate=base_hydrate,
        )
        display = result.to_display_list("SI")
        assert len(display) > 20
        assert any("HEOS" in str(r) for r in display)
        assert any("RİSK VAR" in str(r) for r in display)
        assert any("GÜVENLİ" in str(r) for r in display)

    def test_backend_fallback_warning(self, base_actual, base_standard):
        result = CalculationResult(
            backend_used="SRK",
            actual=base_actual,
            standard=base_standard,
            z_fallback_warning="Z-only fallback used",
        )
        display = result.to_display_list()
        assert any("Z-only" in str(r) for r in display)

    def test_no_heating_no_volume_no_hydrate(self, base_actual, base_standard):
        result = CalculationResult(
            backend_used="HEOS",
            actual=base_actual,
            standard=base_standard,
        )
        display = result.to_display_list()
        assert any("Veri/Yöntem Yok" in str(r) for r in display)
        assert any("Hesaplanamadı" in str(r) for r in display)


class TestToDisplayListBranches:
    def test_isentropic_none(self, base_actual, base_standard):
        base_actual.isentropic_exponent = None
        result = CalculationResult(
            backend_used="HEOS", actual=base_actual, standard=base_standard,
        )
        display = result.to_display_list()
        assert any("Hesaplanamadı" in str(r) for r in display if "Üs" in str(r))

    def test_speed_of_sound_none(self, base_actual, base_standard):
        base_actual.speed_of_sound = None
        result = CalculationResult(
            backend_used="HEOS", actual=base_actual, standard=base_standard,
        )
        display = result.to_display_list()
        assert any("Hesaplanamadı" in str(r) for r in display if "Ses" in str(r))

    def test_std_density_none(self, base_actual):
        std = StandardConditionResults(
            reference_temperature=288.15, reference_pressure=101325.0,
            density_std=None, specific_gravity=0.65,
        )
        result = CalculationResult(backend_used="HEOS", actual=base_actual, standard=std)
        display = result.to_display_list()
        assert any("Hesaplanamadı" in str(r) for r in display if "ρ_std" in str(r))

    def test_sg_none(self, base_actual):
        std = StandardConditionResults(
            reference_temperature=288.15, reference_pressure=101325.0,
            density_std=0.8, specific_gravity=None,
        )
        result = CalculationResult(backend_used="HEOS", actual=base_actual, standard=std)
        display = result.to_display_list()
        assert any("Hesaplanamadı" in str(r) for r in display if "Bağıl" in str(r))

    def test_heating_btu_scf_skip(self, base_actual, base_standard):
        heating = HeatingValues(
            calculation_method="HEOS", hhv_mass=55, lhv_mass=50,
            hhv_volume=38, lhv_volume=34, wobbe_index=50, hhv_btu_scf=1020,
        )
        result = CalculationResult(
            backend_used="HEOS", actual=base_actual, standard=base_standard,
            heating=heating,
        )
        # Heating volume already Btu/SCF → skip extra row
        display = result.to_display_list("Imperial")
        # The "HHV (Endüstriyel)" row should still appear because prefs != Btu/SCF check
        assert any("Btu/SCF" in str(r) for r in display)

    def test_volume_std_ft3_branch(self, base_actual, base_standard):
        vol = VolumeConversion(
            actual_volume=100.0, mass=80.0, standard_volume=95.0,
        )
        result = CalculationResult(
            backend_used="HEOS", actual=base_actual, standard=base_standard,
            volume_conversion=vol,
        )
        display = result.to_display_list("Imperial")
        assert any("SCF" in str(r) or "ft³" in str(r) for r in display)

    def test_normal_volume_error(self, base_actual, base_standard):
        vol = VolumeConversion(
            actual_volume=100.0, mass=80.0, standard_volume=95.0,
            normal_volume=None,
            normal_volume_error="CoolProp failed",
        )
        result = CalculationResult(
            backend_used="HEOS", actual=base_actual, standard=base_standard,
            volume_conversion=vol,
        )
        display = result.to_display_list()
        assert any("Hesaplanamadı" in str(r) for r in display if "Normal" in str(r))

    def test_hydrate_imperial(self, base_actual, base_standard, base_hydrate):
        result = CalculationResult(
            backend_used="HEOS", actual=base_actual, standard=base_standard,
            hydrate=base_hydrate,
        )
        display = result.to_display_list("Imperial")
        assert any("°F" in str(r) for r in display)
        assert any("psi(a)" in str(r) for r in display)


class TestFormatFloat:
    def test_none(self):
        assert CalculationResult._format_float(None, 4) == "Hesaplanamadı"

    def test_nan(self):
        assert CalculationResult._format_float(float("nan"), 4) == "Hesaplanamadı"

    def test_inf(self):
        assert CalculationResult._format_float(float("inf"), 4) == "Hesaplanamadı"

    def test_finite(self):
        assert CalculationResult._format_float(3.14159, 2) == "3.14"

    def test_negative_inf(self):
        assert CalculationResult._format_float(float("-inf"), 4) == "Hesaplanamadı"


class TestToDict:
    def test_to_dict(self, base_actual, base_standard):
        result = CalculationResult(
            backend_used="HEOS", actual=base_actual, standard=base_standard,
        )
        d = result.to_dict()
        assert d["backend_used"] == "HEOS"
        assert d["actual"]["temperature"] == 300.0


class TestToDisplayListInvalidUnitSystem:
    def test_invalid_unit_system_falls_back_to_si(self, base_actual, base_standard):
        result = CalculationResult(
            backend_used="HEOS", actual=base_actual, standard=base_standard,
        )
        display = result.to_display_list("INVALID")
        assert len(display) > 0


# ---------------------------------------------------------------------------
# exceptions.py — tüm exception sınıfları
# ---------------------------------------------------------------------------

class TestBackendNotAvailableError:
    def test_coolprop_message(self):
        err = BackendNotAvailableError("CoolProp")
        assert "CoolProp" in str(err)

    def test_other_backend_message(self):
        err = BackendNotAvailableError("SRK")
        assert "SRK" in str(err)

    def test_none_backend_message(self):
        err = BackendNotAvailableError(None)
        assert "kullanılamıyor" in str(err)

    def test_custom_message(self):
        err = BackendNotAvailableError("HEOS", "Custom error")
        assert str(err) == "Custom error"

    def test_no_args(self):
        err = BackendNotAvailableError()
        assert "kullanılamıyor" in str(err)


class TestMixtureCompatibilityError:
    def test_default_message(self):
        err = MixtureCompatibilityError(["H2S", "CO2"], "HEOS")
        assert "H2S" in str(err)
        assert "CO2" in str(err)
        assert "HEOS" in str(err)

    def test_custom_message(self):
        err = MixtureCompatibilityError(["H2S"], "HEOS", "Custom msg")
        assert str(err) == "Custom msg"

    def test_single_gas(self):
        err = MixtureCompatibilityError(["H2S"], "SRK")
        assert "H2S" in str(err)

    def test_attributes(self):
        err = MixtureCompatibilityError(["H2S", "CO2"], "HEOS")
        assert err.incompatible_gases == ["H2S", "CO2"]
        assert err.backend == "HEOS"


class TestHeatingValueError:
    def test_with_component(self):
        err = HeatingValueError("Methane")
        assert "Methane" in str(err)

    def test_without_component(self):
        err = HeatingValueError()
        assert "hesaplanamadı" in str(err).lower()

    def test_custom_message(self):
        err = HeatingValueError(None, "Custom msg")
        assert str(err) == "Custom msg"

    def test_component_attribute(self):
        err = HeatingValueError("Ethane")
        assert err.component == "Ethane"


class TestValidationError:
    def test_message_format(self):
        err = ValidationError("Sıcaklık", "Çok düşük")
        assert "Sıcaklık" in str(err)
        assert "Çok düşük" in str(err)

    def test_field_attribute(self):
        err = ValidationError("Basınç", "Geçersiz")
        assert err.field_name == "Basınç"


class TestCalculationConvergenceError:
    def test_default_message(self):
        err = CalculationConvergenceError()
        assert "yakınsamadı" in str(err)

    def test_custom_message(self):
        err = CalculationConvergenceError("Custom")
        assert str(err) == "Custom"


class TestStateUpdateError:
    def test_without_original(self):
        err = StateUpdateError("HEOS", 300.0, 1e6)
        assert "300.00" in str(err)
        assert "HEOS" in str(err)

    def test_with_original(self):
        orig = ValueError("CoolProp failed")
        err = StateUpdateError("SRK", 400.0, 2e6, original_error=orig)
        assert "CoolProp failed" in str(err)

    def test_attributes(self):
        err = StateUpdateError("HEOS", 300.0, 1e6)
        assert err.backend == "HEOS"
        assert err.temperature == 300.0
        assert err.pressure == 1e6


# ---------------------------------------------------------------------------
# settings.py — REPO_URL property
# ---------------------------------------------------------------------------

class TestSettingsRepoUrl:
    def test_repo_url_property(self):
        url = config.REPO_URL
        assert url.startswith("https://github.com/")
        assert "Natural-Gas-Prop-Main" in url


# ---------------------------------------------------------------------------
# heating_value_db.py — case-insensitive match + get_all_reference_gases
# ---------------------------------------------------------------------------

class TestHeatingValueDb:
    def test_case_sensitive_match(self):
        hhv, lhv = get_reference_heating_values("Methane")
        assert hhv is not None
        assert lhv is not None

    def test_case_insensitive_match(self):
        hhv, lhv = get_reference_heating_values("methane")
        assert hhv is not None
        assert lhv is not None

    def test_uppercase_match(self):
        hhv, lhv = get_reference_heating_values("METHANE")
        assert hhv is not None
        assert lhv is not None

    def test_nonexistent_gas(self):
        result = get_reference_heating_values("NonExistentGas123")
        assert result is None

    def test_get_all_gases(self):
        gases = get_all_reference_gases()
        assert len(gases) > 5
        assert "Methane" in gases

    def test_exact_match(self):
        hhv, lhv = get_reference_heating_values("HydrogenSulfide")
        assert hhv is not None


# ---------------------------------------------------------------------------
# result_unit_converter.py — geçersiz target_unit
# ---------------------------------------------------------------------------

class TestResultUnitConverterInvalidUnit:
    @pytest.mark.parametrize("converter,value,args", [
        (ResultUnitConverter.convert_density, 10.0, ("invalid_unit",)),
        (ResultUnitConverter.convert_energy_mass, 50.0, ("invalid_unit",)),
        (ResultUnitConverter.convert_entropy, 2.0, ("invalid_unit",)),
        (ResultUnitConverter.convert_speed, 400.0, ("invalid_unit",)),
        (ResultUnitConverter.convert_heating_value_mass, 55.0, ("invalid_unit",)),
        (ResultUnitConverter.convert_heating_value_volume, 38.0, ("invalid_unit",)),
        (ResultUnitConverter.convert_volume, 100.0, ("invalid_unit",)),
        (ResultUnitConverter.convert_mass, 80.0, ("invalid_unit",)),
    ])
    def test_invalid_unit_returns_original(self, converter, value, args):
        result_val, result_unit = converter(value, *args)
        assert result_val == value
        assert result_unit != "invalid_unit"

    def test_get_unit_preferences_invalid(self):
        prefs = ResultUnitConverter.get_unit_preferences(None)
        assert "density" in prefs
