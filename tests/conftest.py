"""Shared test fixtures for Natural Gas Prop."""

import pytest
from natural_gas_main.models.gas_data import GasComponent, GasMixture


def _tk_available() -> bool:
    """Return True if a Tk root can be created (i.e. a display is available)."""
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.destroy()
        return True
    except Exception:
        return False


TK_AVAILABLE = _tk_available()

requires_tk = pytest.mark.skipif(
    not TK_AVAILABLE,
    reason="No display available for GUI tests",
)


@pytest.fixture
def tk_root():
    """Provide a reusable CustomTkinter root, destroyed after the test.

    Skips automatically in headless environments. Using one shared fixture
    avoids the Tk-global-state fragility of creating/destroying many roots.
    """
    if not TK_AVAILABLE:
        pytest.skip("No display available for GUI tests")
    import customtkinter as ctk
    root = ctk.CTk()
    root.withdraw()
    try:
        yield root
    finally:
        try:
            root.destroy()
        except Exception:
            pass


@pytest.fixture
def simple_mixture():
    """A simple 2-component natural gas mixture (90% Methane, 10% Ethane molar)."""
    return GasMixture(
        components=[
            GasComponent(name="Methane", fraction=90.0),
            GasComponent(name="Ethane", fraction=10.0),
        ],
        fraction_type="molar",
    )


@pytest.fixture
def sour_gas_mixture():
    """Sour gas mixture with H₂S and CO₂."""
    return GasMixture(
        components=[
            GasComponent(name="Methane", fraction=70.0),
            GasComponent(name="Ethane", fraction=10.0),
            GasComponent(name="CarbonDioxide", fraction=10.0),
            GasComponent(name="HydrogenSulfide", fraction=10.0),
        ],
        fraction_type="molar",
    )


@pytest.fixture
def mass_fraction_mixture():
    """Mixture using mass fractions."""
    return GasMixture(
        components=[
            GasComponent(name="Methane", fraction=80.0),
            GasComponent(name="Ethane", fraction=15.0),
            GasComponent(name="Nitrogen", fraction=5.0),
        ],
        fraction_type="mass",
    )


@pytest.fixture
def unknown_gas_mixture():
    """Mixture with a non-existent gas name for error testing."""
    return GasMixture(
        components=[
            GasComponent(name="Unobtanium", fraction=100.0),
        ],
        fraction_type="molar",
    )


@pytest.fixture
def make_mixture():
    """Factory fixture to create GasMixture with custom components."""
    def _make(components_dict, fraction_type="molar"):
        return GasMixture(
            components=[
                GasComponent(name=name, fraction=frac)
                for name, frac in components_dict.items()
            ],
            fraction_type=fraction_type,
        )
    return _make
