"""
GUI smoke test — verifies the application can be created without errors.

Skips when no display is available (CI/headless environments).
"""

import os
import pytest


def _tk_available() -> bool:
    """Check whether a Tk root can be created."""
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.destroy()
        return True
    except Exception:
        return False


@pytest.mark.skipif(
    not _tk_available(),
    reason="No display available for GUI tests",
)
class TestGuiSmoke:
    """Smoke tests that do not require user interaction."""

    def test_thermo_app_creates_successfully(self):
        from natural_gas_main.ui.app import ThermoApp

        app = ThermoApp()
        try:
            assert app is not None
            assert app.title() != ""
            assert app.winfo_exists()
        finally:
            app.withdraw()
            app.destroy()

    def test_input_panel_creates_with_gas_list(self):
        from natural_gas_main.ui.input_panel import InputPanel
        import customtkinter as ctk

        root = ctk.CTk()
        try:
            panel = InputPanel(root, gas_list=["Methane", "Ethane", "Propane"])
            assert panel is not None
            assert len(panel.gas_list) == 3
        finally:
            root.destroy()

    def test_output_panel_creates_successfully(self):
        from natural_gas_main.ui.output_panel import OutputPanel
        import customtkinter as ctk

        root = ctk.CTk()
        try:
            panel = OutputPanel(root)
            assert panel is not None
            assert hasattr(panel, "results_tree")
            assert hasattr(panel, "kpis")
        finally:
            root.destroy()

    def test_app_has_required_widgets(self):
        from natural_gas_main.ui.app import ThermoApp

        app = ThermoApp()
        try:
            assert hasattr(app, "input_panel")
            assert hasattr(app, "output_panel")
            assert hasattr(app, "calc_button")
            assert hasattr(app, "status_var")
            assert app.calc_button.cget("text") == "Hesapla"
        finally:
            app.withdraw()
            app.destroy()
