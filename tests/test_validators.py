"""Tests for core validators module."""

import pytest
from natural_gas_main.core.validators import (
    validate_numeric_input,
    validate_temperature,
    validate_pressure,
    validate_volume,
    validate_gas_fraction,
    validate_total_fraction,
    validate_backend,
    validate_component_count,
    validate_gas_name,
)
from natural_gas_main.core.exceptions import ValidationError


class TestValidateNumericInput:
    def test_valid_number(self):
        assert validate_numeric_input("25.5", "Test") == 25.5

    def test_comma_decimal(self):
        assert validate_numeric_input("25,5", "Test") == 25.5

    def test_integer(self):
        assert validate_numeric_input("100", "Test") == 100.0

    def test_negative(self):
        assert validate_numeric_input("-5", "Test") == -5.0

    def test_scientific_notation(self):
        assert validate_numeric_input("1e3", "Test") == 1000.0

    def test_inf_nan_pass_through(self):
        """float('inf') and float('nan') convert without ValueError."""
        result = validate_numeric_input("inf", "Test")
        import math
        assert math.isinf(result)

    def test_empty_string_raises(self):
        with pytest.raises(ValidationError, match="boş"):
            validate_numeric_input("", "Test")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValidationError, match="boş"):
            validate_numeric_input("   ", "Test")

    def test_non_numeric_raises(self):
        with pytest.raises(ValidationError):
            validate_numeric_input("abc", "Test")

    def test_thousands_separator_fails(self):
        with pytest.raises(ValidationError):
            validate_numeric_input("1,234.56", "Test")

    def test_min_violation(self):
        with pytest.raises(ValidationError):
            validate_numeric_input("5", "Test", min_val=10)

    def test_max_violation(self):
        with pytest.raises(ValidationError):
            validate_numeric_input("15", "Test", max_val=10)

    def test_zero_allowed(self):
        assert validate_numeric_input("0", "Test", allow_zero=True) == 0.0

    def test_zero_not_allowed(self):
        with pytest.raises(ValidationError, match="sıfır"):
            validate_numeric_input("0", "Test", allow_zero=False)


class TestValidateTemperature:
    def test_valid(self):
        validate_temperature(300.0)

    def test_too_cold(self):
        with pytest.raises(ValidationError):
            validate_temperature(0.0)

    def test_at_min_rejected(self):
        from natural_gas_main.config.settings import config
        with pytest.raises(ValidationError):
            validate_temperature(config.MIN_TEMPERATURE)

    def test_too_hot(self):
        with pytest.raises(ValidationError, match="yüksek"):
            validate_temperature(1e9)


class TestValidatePressure:
    def test_valid(self):
        validate_pressure(101325.0)

    def test_zero_raises(self):
        with pytest.raises(ValidationError):
            validate_pressure(0.0)

    def test_negative_raises(self):
        with pytest.raises(ValidationError):
            validate_pressure(-1.0)

    def test_too_high(self):
        with pytest.raises(ValidationError, match="yüksek"):
            validate_pressure(1e10)


class TestValidateVolume:
    def test_valid(self):
        validate_volume(1.0)

    def test_zero_raises(self):
        with pytest.raises(ValidationError):
            validate_volume(0.0)

    def test_too_large(self):
        with pytest.raises(ValidationError):
            validate_volume(1e10)


class TestValidateGasFraction:
    def test_valid_fraction(self):
        validate_gas_fraction(50.0)

    def test_zero_allowed(self):
        # 0.00% (undetected chromatograph gas) is a valid input
        validate_gas_fraction(0.0)

    def test_negative_raises(self):
        with pytest.raises(ValidationError):
            validate_gas_fraction(-1.0)

    def test_over_100_raises(self):
        with pytest.raises(ValidationError):
            validate_gas_fraction(100.1)

    def test_100_valid(self):
        validate_gas_fraction(100.0)


class TestValidateTotalFraction:
    def test_exact_100(self):
        validate_total_fraction([50.0, 50.0])

    def test_within_tolerance(self):
        validate_total_fraction([50.0, 49.99995])

    def test_not_100_raises(self):
        with pytest.raises(ValidationError, match="toplamı 100"):
            validate_total_fraction([50.0, 40.0])

    def test_empty_list(self):
        with pytest.raises(ValidationError):
            validate_total_fraction([])


class TestValidateBackend:
    def test_valid_backend(self):
        validate_backend("HEOS")
        validate_backend("SRK")
        validate_backend("PR")
        validate_backend("GERG-2008")
        validate_backend("AGA8-Detail")

    def test_invalid_raises(self):
        with pytest.raises(ValidationError, match="backend"):
            validate_backend("InvalidBackend")

    def test_empty_raises(self):
        with pytest.raises(ValidationError):
            validate_backend("")


class TestValidateComponentCount:
    def test_valid_count(self):
        validate_component_count(5)

    def test_zero_raises(self):
        with pytest.raises(ValidationError):
            validate_component_count(0)

    def test_too_many_raises(self):
        with pytest.raises(ValidationError):
            validate_component_count(1000)

    def test_at_limit(self):
        from natural_gas_main.config.settings import config
        validate_component_count(config.MAX_COMPONENTS)


class TestValidateGasName:
    def test_valid_name(self):
        validate_gas_name("Methane")

    def test_empty_raises(self):
        with pytest.raises(ValidationError, match="Boş"):
            validate_gas_name("")

    def test_whitespace_raises(self):
        with pytest.raises(ValidationError):
            validate_gas_name("   ")

    def test_duplicate_raises(self):
        with pytest.raises(ValidationError, match="zaten listede"):
            validate_gas_name("Methane", ["Methane"])

    def test_case_insensitive_duplicate(self):
        with pytest.raises(ValidationError):
            validate_gas_name("methane", ["METHANE"])

    def test_unique_ok(self):
        validate_gas_name("Ethane", ["Methane", "Propane"])
