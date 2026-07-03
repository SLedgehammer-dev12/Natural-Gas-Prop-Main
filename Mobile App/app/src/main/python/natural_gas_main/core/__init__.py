"""Core utilities package."""

from natural_gas_main.core.converters import (
    convert_temperature_to_K,
    convert_temperature_from_K,
    convert_pressure_to_Pa,
    convert_pressure_from_Pa,
    convert_volume_to_m3,
    TemperatureUnit,
    PressureUnit,
    VolumeUnit,
)
from natural_gas_main.core.exceptions import (
    ThermoCalculationError,
    BackendNotAvailableError,
    MixtureCompatibilityError,
    HeatingValueError,
    ValidationError,
    CalculationConvergenceError,
    StateUpdateError,
)
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

__all__ = [
    "convert_temperature_to_K",
    "convert_temperature_from_K",
    "convert_pressure_to_Pa",
    "convert_pressure_from_Pa",
    "convert_volume_to_m3",
    "TemperatureUnit",
    "PressureUnit",
    "VolumeUnit",
    "ThermoCalculationError",
    "BackendNotAvailableError",
    "MixtureCompatibilityError",
    "HeatingValueError",
    "ValidationError",
    "CalculationConvergenceError",
    "StateUpdateError",
    "validate_numeric_input",
    "validate_temperature",
    "validate_pressure",
    "validate_volume",
    "validate_gas_fraction",
    "validate_total_fraction",
    "validate_backend",
    "validate_component_count",
    "validate_gas_name",
]
