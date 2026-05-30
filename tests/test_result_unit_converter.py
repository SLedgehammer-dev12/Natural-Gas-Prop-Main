"""Tests for result unit converter."""

import pytest
from natural_gas_main.utils.result_unit_converter import (
    ResultUnitConverter,
    UnitSystem,
)


class TestUnitPreferences:
    def test_si_system(self):
        prefs = ResultUnitConverter.get_unit_preferences(UnitSystem.SI)
        assert prefs["density"] == "kg/m³"
        assert prefs["volume"] == "m³"
        assert prefs["mass"] == "kg"

    def test_imperial_system(self):
        prefs = ResultUnitConverter.get_unit_preferences(UnitSystem.IMPERIAL)
        assert prefs["density"] == "lb/ft³"
        assert prefs["volume"] == "ft³"
        assert prefs["mass"] == "lb"
        assert prefs["heating_value_volume"] == "Btu/SCF"

    def test_mixed_system(self):
        prefs = ResultUnitConverter.get_unit_preferences(UnitSystem.MIXED)
        assert prefs["density"] == "kg/m³"
        assert prefs["heating_value_mass"] == "Btu/lb"

    def test_unit_system_enum_values(self):
        assert UnitSystem.SI.value == "SI"
        assert UnitSystem.IMPERIAL.value == "Imperial"
        assert UnitSystem.MIXED.value == "Mixed"


class TestDensityConversion:
    def test_kgm3_identity(self):
        val, unit = ResultUnitConverter.convert_density(10.0, "kg/m³")
        assert val == 10.0
        assert unit == "kg/m³"

    def test_kgm3_to_lbft3(self):
        val, unit = ResultUnitConverter.convert_density(16.0185, "lb/ft³")
        assert val == pytest.approx(1.0, rel=0.02)
        assert unit == "lb/ft³"

    def test_unknown_unit_falls_back(self):
        val, unit = ResultUnitConverter.convert_density(5.0, "unknown")
        assert val == 5.0
        assert unit == "kg/m³"


class TestEnergyMassConversion:
    def test_kjkg_identity(self):
        val, unit = ResultUnitConverter.convert_energy_mass(100.0, "kJ/kg")
        assert val == 100.0

    def test_kjkg_to_btulb(self):
        val, unit = ResultUnitConverter.convert_energy_mass(1.0, "Btu/lb")
        assert val == pytest.approx(0.4299, rel=0.02)
        assert unit == "Btu/lb"


class TestSpeedConversion:
    def test_ms_to_fts(self):
        val, unit = ResultUnitConverter.convert_speed(1.0, "ft/s")
        assert val == pytest.approx(3.28084, rel=0.01)

    def test_ms_to_kmh(self):
        val, unit = ResultUnitConverter.convert_speed(1.0, "km/h")
        assert val == 3.6


class TestHeatingValueMass:
    def test_mjkg_to_btulb(self):
        val, unit = ResultUnitConverter.convert_heating_value_mass(1.0, "Btu/lb")
        assert val == pytest.approx(429.92, rel=0.01)
        assert unit == "Btu/lb"


class TestHeatingValueVolume:
    def test_mjsm3_to_btuscf(self):
        val, unit = ResultUnitConverter.convert_heating_value_volume(1.0, "Btu/SCF")
        assert val == pytest.approx(26.839, rel=0.01)
        assert unit == "Btu/SCF"


class TestVolumeConversion:
    def test_m3_identity(self):
        val, unit = ResultUnitConverter.convert_volume(5.0, "m³")
        assert val == 5.0

    def test_m3_to_ft3(self):
        val, unit = ResultUnitConverter.convert_volume(1.0, "ft³")
        assert val == pytest.approx(35.3147, rel=0.01)
        assert unit == "ft³"

    def test_m3_to_L(self):
        val, unit = ResultUnitConverter.convert_volume(1.0, "L")
        assert val == 1000.0
        assert unit == "L"


class TestMassConversion:
    def test_kg_identity(self):
        val, unit = ResultUnitConverter.convert_mass(10.0, "kg")
        assert val == 10.0

    def test_kg_to_lb(self):
        val, unit = ResultUnitConverter.convert_mass(1.0, "lb")
        assert val == pytest.approx(2.2046, rel=0.01)
        assert unit == "lb"


class TestEntropyConversion:
    def test_kjkgk_identity(self):
        val, unit = ResultUnitConverter.convert_entropy(5.0, "kJ/(kg·K)")
        assert val == 5.0
