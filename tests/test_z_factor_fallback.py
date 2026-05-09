import math

import pytest

from natural_gas_main.models.calculator import COOLPROP_AVAILABLE, ThermoCalculator
from natural_gas_main.models.gas_data import GasComponent, GasMixture


pytestmark = pytest.mark.skipif(not COOLPROP_AVAILABLE, reason="CoolProp is required")


def test_z_factor_comparison_is_added_to_successful_result():
    mixture = GasMixture(
        components=[
            GasComponent(name="Methane", fraction=90.0),
            GasComponent(name="Ethane", fraction=5.0),
            GasComponent(name="Propane", fraction=3.0),
            GasComponent(name="Nitrogen", fraction=2.0),
        ]
    )

    result = ThermoCalculator().calculate_properties(
        mixture,
        temperature_k=288.15,
        pressure_pa=8_000_000,
        backend="HEOS",
    )

    estimates = {item.method: item for item in result.z_factor_comparison}
    assert "Standing-Katz ANN10" in estimates
    assert "Dranchuk-Abou-Kassem" in estimates
    assert estimates["Standing-Katz ANN10"].valid
    assert 0.6 < estimates["Standing-Katz ANN10"].z_factor < 1.1


def test_z_only_fallback_returns_limited_result_when_backends_fail(monkeypatch):
    calculator = ThermoCalculator()
    mixture = GasMixture(
        components=[
            GasComponent(name="Methane", fraction=92.0),
            GasComponent(name="Ethane", fraction=5.0),
            GasComponent(name="Propane", fraction=2.0),
            GasComponent(name="Nitrogen", fraction=1.0),
        ]
    )

    monkeypatch.setattr(calculator, "_get_backend_order", lambda _mixture, _preferred: ["BAD"])

    result, backend = calculator.calculate_with_fallback(
        mixture,
        temperature_k=288.15,
        pressure_pa=8_000_000,
        preferred_backend="HEOS",
    )

    assert backend == "Standing-Katz ANN10"
    assert result is not None
    assert result.z_fallback_warning
    assert result.backend_used == "Standing-Katz ANN10 (Z-only fallback)"
    assert 0.6 < result.actual.compressibility_factor < 1.1
    assert result.actual.density > 0
    assert math.isnan(result.actual.enthalpy)
