import pytest

from natural_gas_main.models.calculator import COOLPROP_AVAILABLE, ThermoCalculator
from natural_gas_main.models.gas_data import GasComponent, GasMixture


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


def test_reference_heating_values_convert_molar_to_mass_weighting():
    mixture = GasMixture(
        components=[
            GasComponent(name="Methane", fraction=50.0),
            GasComponent(name="Propane", fraction=50.0),
        ],
        fraction_type="molar",
    )

    hhv, lhv = ThermoCalculator()._calculate_heating_values_reference(mixture)

    methane_molar_mass = 0.0160428
    propane_molar_mass = 0.0440956
    methane_mass_weight = methane_molar_mass / (methane_molar_mass + propane_molar_mass)
    propane_mass_weight = propane_molar_mass / (methane_molar_mass + propane_molar_mass)

    expected_hhv = methane_mass_weight * 55.50 + propane_mass_weight * 50.36
    expected_lhv = methane_mass_weight * 50.01 + propane_mass_weight * 46.37

    assert hhv == pytest.approx(expected_hhv, rel=1e-3)
    assert lhv == pytest.approx(expected_lhv, rel=1e-3)


def test_reference_heating_values_use_mass_fractions_directly():
    mixture = GasMixture(
        components=[
            GasComponent(name="Methane", fraction=50.0),
            GasComponent(name="Propane", fraction=50.0),
        ],
        fraction_type="mass",
    )

    hhv, lhv = ThermoCalculator()._calculate_heating_values_reference(mixture)

    assert hhv == pytest.approx((55.50 + 50.36) / 2)
    assert lhv == pytest.approx((50.01 + 46.37) / 2)


def test_coolprop_missing_hhv_api_does_not_emit_warning(caplog):
    mixture = GasMixture(components=[GasComponent(name="Propane", fraction=100.0)])

    result = ThermoCalculator().calculate_properties(
        mixture=mixture,
        temperature_k=288.15,
        pressure_pa=101325.0,
        backend="HEOS",
    )

    warning_messages = [record.getMessage() for record in caplog.records if record.levelname == "WARNING"]

    assert result.heating is not None
    assert not any("HHVmass" in message or "LHVmass" in message for message in warning_messages)
