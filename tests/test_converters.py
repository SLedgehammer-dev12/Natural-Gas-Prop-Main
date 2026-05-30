"""
Unit tests for temperature, pressure, and volume converters.

Validates correctness of all unit conversion paths and edge cases.
"""

import pytest
from natural_gas_main.core.converters import (
    convert_temperature_to_K,
    convert_temperature_from_K,
    convert_pressure_to_Pa,
    convert_pressure_from_Pa,
    convert_volume_to_m3,
    TemperatureUnit,
)
from natural_gas_main.core.exceptions import ValidationError


class TestTemperatureToKelvin:
    def test_celsius_to_kelvin_zero(self):
        assert convert_temperature_to_K(0, "°C") == pytest.approx(273.15)

    def test_celsius_to_kelvin_25(self):
        assert convert_temperature_to_K(25, "°C") == pytest.approx(298.15)

    def test_kelvin_identity(self):
        assert convert_temperature_to_K(300, "K") == pytest.approx(300.0)

    def test_fahrenheit_32_to_kelvin(self):
        assert convert_temperature_to_K(32, "°F") == pytest.approx(273.15)

    def test_fahrenheit_212_to_kelvin(self):
        assert convert_temperature_to_K(212, "°F") == pytest.approx(373.15)

    def test_temperature_unit_enum(self):
        assert convert_temperature_to_K(0, TemperatureUnit.CELSIUS) == pytest.approx(273.15)

    def test_invalid_unit_raises(self):
        with pytest.raises(ValidationError):
            convert_temperature_to_K(100, "Rankine")

    def test_empty_string_raises(self):
        with pytest.raises(ValidationError):
            convert_temperature_to_K(0.0, "")

    def test_negative_kelvin_passes_through(self):
        assert convert_temperature_to_K(-500.0, "K") == -500.0


class TestTemperatureFromKelvin:
    def test_kelvin_to_celsius(self):
        assert convert_temperature_from_K(298.15, "°C") == pytest.approx(25.0)

    def test_kelvin_to_fahrenheit(self):
        assert convert_temperature_from_K(373.15, "°F") == pytest.approx(212.0, abs=1e-4)

    def test_invalid_target_raises(self):
        with pytest.raises(ValidationError):
            convert_temperature_from_K(300, "Rankine")


class TestPressureToPascal:
    def test_kpa_to_pa(self):
        assert convert_pressure_to_Pa(101.325, "kPa") == pytest.approx(101325.0)

    def test_bar_absolute_to_pa(self):
        assert convert_pressure_to_Pa(1.01325, "bar(a)") == pytest.approx(101325.0)

    def test_bar_gauge_to_pa(self):
        result = convert_pressure_to_Pa(0, "bar(g)")
        assert result == pytest.approx(101325.0)

    def test_mpa_to_pa(self):
        assert convert_pressure_to_Pa(1, "MPa") == pytest.approx(1e6)

    def test_psi_absolute_to_pa(self):
        assert convert_pressure_to_Pa(14.6959, "psi(a)") == pytest.approx(101325.0, rel=1e-4)

    def test_psi_gauge_to_pa(self):
        result = convert_pressure_to_Pa(0, "psi(g)")
        assert result == pytest.approx(101325.0, rel=1e-4)

    def test_atm_to_pa(self):
        assert convert_pressure_to_Pa(1, "atm") == pytest.approx(101325.0)

    def test_invalid_unit_raises(self):
        with pytest.raises(ValidationError):
            convert_pressure_to_Pa(100, "torr")

    def test_negative_pressure_converts(self):
        result = convert_pressure_to_Pa(-1, "bar(a)")
        assert result < 0

    def test_zero_pressure_converts(self):
        assert convert_pressure_to_Pa(0.0, "bar(a)") == 0.0

    def test_roundtrip_bar(self):
        pa = convert_pressure_to_Pa(2.5, "bar(a)")
        bar = convert_pressure_from_Pa(pa, "bar(a)")
        assert bar == pytest.approx(2.5)


class TestPressureFromPascal:
    def test_pa_to_bar(self):
        result = convert_pressure_from_Pa(101325.0, "bar(a)")
        assert result == pytest.approx(1.01325)

    def test_pa_to_psi(self):
        result = convert_pressure_from_Pa(101325.0, "psi(a)")
        assert result == pytest.approx(14.6959, rel=1e-4)

    def test_pa_to_kpa(self):
        assert convert_pressure_from_Pa(100000, "kPa") == pytest.approx(100.0)

    def test_invalid_target_raises(self):
        with pytest.raises(ValidationError):
            convert_pressure_from_Pa(100000, "torr")


class TestVolumeConversion:
    def test_m3_identity(self):
        assert convert_volume_to_m3(1, "m³") == pytest.approx(1.0)

    def test_litre_to_m3(self):
        assert convert_volume_to_m3(1000, "L") == pytest.approx(1.0)

    def test_cubic_feet_to_m3(self):
        result = convert_volume_to_m3(35.3147, "ft³")
        assert result == pytest.approx(1.0, rel=1e-4)

    def test_negative_volume_converts(self):
        result = convert_volume_to_m3(-1, "m³")
        assert result < 0

    def test_invalid_unit_raises(self):
        with pytest.raises(ValidationError):
            convert_volume_to_m3(1.0, "gal")

    def test_large_volume(self):
        assert convert_volume_to_m3(1e9, "m³") == pytest.approx(1e9)
