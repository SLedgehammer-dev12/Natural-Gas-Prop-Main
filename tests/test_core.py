import pytest
from natural_gas_main.core import converters
from natural_gas_main.core.converters import VolumeUnit, PressureUnit, TemperatureUnit
from natural_gas_main.core.exceptions import ValidationError


class TestTemperatureConversion:
    def test_celsius_to_kelvin(self):
        assert converters.convert_temperature_to_K(25.0, "°C") == pytest.approx(298.15)

    def test_fahrenheit_to_kelvin(self):
        assert converters.convert_temperature_to_K(32.0, "°F") == pytest.approx(273.15)

    def test_kelvin_identity(self):
        assert converters.convert_temperature_to_K(300.0, "K") == 300.0

    def test_kelvin_to_celsius(self):
        assert converters.convert_temperature_from_K(298.15, "°C") == pytest.approx(25.0)

    def test_kelvin_to_fahrenheit(self):
        result = converters.convert_temperature_from_K(273.15, "°F")
        assert result == pytest.approx(32.0, abs=0.1)

    def test_enum_unit_accepted(self):
        result = converters.convert_temperature_to_K(15.0, TemperatureUnit.CELSIUS)
        assert result == pytest.approx(288.15)

    def test_invalid_unit_raises(self):
        with pytest.raises(ValidationError, match="Geçersiz birim"):
            converters.convert_temperature_to_K(100.0, "Rankine")

    def test_empty_string_causes_error(self):
        with pytest.raises(ValidationError):
            converters.convert_temperature_to_K(0.0, "")

    def test_negative_kelvin_passes_through(self):
        result = converters.convert_temperature_to_K(-500.0, "K")
        assert result == -500.0


class TestPressureConversion:
    def test_kpa_to_pa(self):
        assert converters.convert_pressure_to_Pa(100.0, "kPa") == pytest.approx(100000.0)

    def test_bara_to_pa(self):
        assert converters.convert_pressure_to_Pa(1.0, "bar(a)") == pytest.approx(100000.0)

    def test_barg_to_pa(self):
        result = converters.convert_pressure_to_Pa(0.0, "bar(g)")
        assert result > 100000.0

    def test_psia_to_pa(self):
        result = converters.convert_pressure_to_Pa(14.6959, "psi(a)")
        assert result == pytest.approx(101325.0, rel=0.01)

    def test_mpa_to_pa(self):
        assert converters.convert_pressure_to_Pa(1.0, "MPa") == 1_000_000.0

    def test_atm_to_pa(self):
        assert converters.convert_pressure_to_Pa(1.0, "atm") == 101325.0

    def test_pa_identity(self):
        assert converters.convert_pressure_to_Pa(500.0, "Pa") == 500.0

    def test_invalid_unit_raises(self):
        with pytest.raises(ValidationError, match="Geçersiz birim"):
            converters.convert_pressure_to_Pa(1.0, "torr")

    def test_zero_pressure_converts(self):
        assert converters.convert_pressure_to_Pa(0.0, "bar(a)") == 0.0

    def test_back_conversion_roundtrip(self):
        pa = converters.convert_pressure_to_Pa(2.5, "bar(a)")
        bar = converters.convert_pressure_from_Pa(pa, "bar(a)")
        assert bar == pytest.approx(2.5)


class TestVolumeConversion:
    def test_m3_identity(self):
        assert converters.convert_volume_to_m3(100.0, "m³") == 100.0

    def test_liter_to_m3(self):
        assert converters.convert_volume_to_m3(1000.0, "L") == pytest.approx(1.0)

    def test_ft3_to_m3(self):
        assert converters.convert_volume_to_m3(1.0, "ft³") == pytest.approx(0.0283168, abs=1e-5)

    def test_enum_unit_accepted(self):
        result = converters.convert_volume_to_m3(1.0, VolumeUnit.M3)
        assert result == 1.0

    def test_invalid_unit_raises(self):
        with pytest.raises(ValidationError, match="Geçersiz birim"):
            converters.convert_volume_to_m3(1.0, "gal")
