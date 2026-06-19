"""Tests for natural_gas_main.main module."""

from unittest.mock import patch, MagicMock
import pytest


@pytest.fixture(autouse=True)
def mock_tkinter():
    """Prevent tkinter from being imported during tests."""
    with patch("natural_gas_main.ui.app.ThermoApp", MagicMock()):
        yield


def test_main_import_error():
    """main() should exit with code 1 on ImportError."""
    with patch("natural_gas_main.main.setup_logging", side_effect=ImportError("no module")):
        with pytest.raises(SystemExit) as exc:
            from natural_gas_main.main import main
            main()
        assert exc.value.code == 1


def test_main_general_error():
    """main() should exit with code 1 on general exception."""
    with patch("natural_gas_main.main.setup_logging", side_effect=RuntimeError("crash")):
        with pytest.raises(SystemExit) as exc:
            from natural_gas_main.main import main
            main()
        assert exc.value.code == 1


def test_main_success():
    """main() should complete without errors in normal flow."""
    mock_app = MagicMock()
    with patch("natural_gas_main.main.setup_logging"):
        with patch("natural_gas_main.ui.app.ThermoApp", return_value=mock_app):
            from natural_gas_main.main import main
            main()
            mock_app.mainloop.assert_called_once()
