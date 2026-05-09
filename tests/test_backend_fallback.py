from natural_gas_main.models.calculator import COOLPROP_AVAILABLE, ThermoCalculator
from natural_gas_main.models.gas_data import GasComponent, GasMixture

import pytest


pytestmark = pytest.mark.skipif(not COOLPROP_AVAILABLE, reason="CoolProp is not installed")


def test_calculation_fallback_uses_cubic_backend_when_heos_pair_data_is_missing():
    mixture = GasMixture(
        components=[
            GasComponent(name="Methane", fraction=90.0),
            GasComponent(name="CycloPropane", fraction=10.0),
        ]
    )

    result, backend = ThermoCalculator().calculate_with_fallback(
        mixture=mixture,
        temperature_k=279.15,
        pressure_pa=4101325.0,
        preferred_backend="HEOS",
    )

    assert result is not None
    assert backend in {"SRK", "PR"}
    assert result.backend_used == backend
    assert result.actual.density > 0
