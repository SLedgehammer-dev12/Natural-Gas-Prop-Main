import os
import sys

from natural_gas_main.models.calculator import COOLPROP_AVAILABLE, ThermoCalculator
from natural_gas_main.models.gas_data import GasComponent, GasMixture

import pytest


pytestmark = pytest.mark.skipif(
    not COOLPROP_AVAILABLE or sys.platform == "win32",
    reason="CoolProp is not installed or PosixPath incompatibility on Windows"
)


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


class TestGetAvailableBackends:
    """Tests for config.get_available_backends() NeqSim filtering."""

    def test_filters_neqsim_when_not_available(self):
        from unittest.mock import patch
        from natural_gas_main.config.settings import config
        with patch("natural_gas_main.models.neqsim_calculator.NEQSIM_AVAILABLE", False):
            backends = config.get_available_backends()
        neqsim_backends = [b for b in backends if b.startswith("neqsim-")]
        assert len(neqsim_backends) == 0
        assert "HEOS" in backends
        assert "SRK" in backends
        assert "PR" in backends

    def test_includes_neqsim_when_available(self):
        from unittest.mock import patch
        from natural_gas_main.config.settings import config
        with patch("natural_gas_main.models.neqsim_calculator.NEQSIM_AVAILABLE", True):
            backends = config.get_available_backends()
        neqsim_backends = [b for b in backends if b.startswith("neqsim-")]
        assert len(neqsim_backends) > 0
        assert "neqsim-gerg2008" in backends

    def test_handles_import_error_gracefully(self):
        import sys
        from unittest.mock import patch
        from natural_gas_main.config.settings import config
        orig = sys.modules.pop("natural_gas_main.models.neqsim_calculator", None)
        try:
            backends = config.get_available_backends()
        finally:
            if orig is not None:
                sys.modules["natural_gas_main.models.neqsim_calculator"] = orig
        neqsim_backends = [b for b in backends if b.startswith("neqsim-")]
        assert len(neqsim_backends) == 0
        assert "HEOS" in backends
