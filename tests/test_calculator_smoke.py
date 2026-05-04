import pytest

from natural_gas_g5.models.calculator import COOLPROP_AVAILABLE, ThermoCalculator
from natural_gas_g5.models.gas_data import GasComponent, GasMixture


pytestmark = pytest.mark.skipif(not COOLPROP_AVAILABLE, reason="CoolProp is not installed")


def test_calculator_handles_typical_natural_gas_with_volume_conversion():
    mixture = GasMixture(
        components=[
            GasComponent(name="Methane", fraction=94.0),
            GasComponent(name="Ethane", fraction=4.0),
            GasComponent(name="Propane", fraction=1.0),
            GasComponent(name="Nitrogen", fraction=1.0),
        ]
    )

    result = ThermoCalculator().calculate_properties(
        mixture=mixture,
        temperature_k=288.15,
        pressure_pa=101325.0,
        backend="HEOS",
        volume_m3=100.0,
        standard_T=288.15,
        standard_P=101325.0,
        standard_name="ISO 13443",
    )

    assert result.backend_used == "HEOS"
    assert result.actual.density > 0
    assert 0.8 < result.actual.compressibility_factor < 1.2
    assert result.standard.standard_name == "ISO 13443"
    assert result.volume_conversion is not None
    assert result.volume_conversion.standard_volume > 0
    assert result.heating is not None
    assert result.heating.hhv_volume > 0


def test_calculator_accepts_propane_display_name():
    mixture = GasMixture(components=[GasComponent(name="Propane", fraction=100.0)])
    result = ThermoCalculator().calculate_properties(
        mixture=mixture,
        temperature_k=288.15,
        pressure_pa=101325.0,
        backend="HEOS",
    )

    assert mixture.to_coolprop_string() == "n-Propane"
    assert result.actual.density > 0
    assert result.heating is not None
