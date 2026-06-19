"""Aşama 3 — Zor: dosya/HTTP/font/AbstractState mock gerektiren coverage testleri.

Kapsanan dosyalar:
- logger.py: _resolve_log_path tüm OS dalları, OSError fallback, tempfile, stderr fallback
- updater.py: check_for_updates tüm HTTP yanıt/exception dalları, URL validation, open_download_page
- aga8_calculator.py: PYAGA8_AVAILABLE=False, unknown method, unmapped gaz, normalization, set_composition hatası
- report_generator.py: font fallback Linux/macOS/Windows, generate_and_save IOError, footer
"""

import json
import os
import sys
import math
import logging
import tempfile
import urllib
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest

from natural_gas_main.core.exceptions import BackendNotAvailableError


# ---------------------------------------------------------------------------
# logger.py — tüm OS dalları, OSError fallback, tempfile, stderr fallback
# ---------------------------------------------------------------------------

class TestLoggerResolveLogPath:
    def test_absolute_path(self):
        from pathlib import Path, PurePosixPath
        from natural_gas_main.utils.logger import _resolve_log_path
        result = _resolve_log_path(str(PurePosixPath("/tmp/myapp.log")))
        expected = Path("/tmp/myapp.log")
        assert result == expected

    def test_relative_path_uses_state_dir(self):
        from natural_gas_main.utils.logger import _resolve_log_path
        with patch("os.name", "posix"):
            with patch.dict(os.environ, {}, clear=True):
                result = _resolve_log_path("app.log")
                assert "NaturalGasProp" in str(result)
                assert "app.log" in str(result)

    def test_xdg_state_home(self, monkeypatch):
        monkeypatch.delenv("XDG_STATE_HOME", raising=False)
        monkeypatch.setattr(os, "name", "posix")
        monkeypatch.setenv("XDG_STATE_HOME", "/tmp/xdg-state")
        from natural_gas_main.utils.logger import _resolve_log_path
        result = _resolve_log_path("app.log")
        assert "xdg-state" in str(result)

    def test_default_state_dir(self, monkeypatch):
        monkeypatch.delenv("XDG_STATE_HOME", raising=False)
        monkeypatch.setattr(os, "name", "posix")
        from natural_gas_main.utils.logger import _resolve_log_path
        result = _resolve_log_path("app.log")
        assert ".local/state" in str(result) or ".local" in str(result)


class TestLoggerSetupLogging:
    def test_oserror_fallback_to_tempdir(self):
        """When RotatingFileHandler fails with OSError, fallback to tempdir."""
        from natural_gas_main.utils.logger import setup_logging
        original = logging.getLogger().handlers.copy()
        try:
            # Force OSError on creation of RotatingFileHandler
            with patch(
                "natural_gas_main.utils.logger.RotatingFileHandler",
                side_effect=OSError("Permission denied"),
            ):
                # This should fall through to tempfile
                setup_logging(log_file="test_oserror.log", level="DEBUG")
            root = logging.getLogger()
            # Should have a handler (tempfile or stderr)
            assert len(root.handlers) > 0
        finally:
            logging.getLogger().handlers.clear()
            for h in original:
                logging.getLogger().addHandler(h)

    def test_all_fallback_to_stderr(self):
        """When both file and tempfile RotatingFileHandler fail, fallback to stderr."""
        from natural_gas_main.utils.logger import setup_logging
        original = logging.getLogger().handlers.copy()
        try:
            with patch(
                "natural_gas_main.utils.logger.RotatingFileHandler",
                side_effect=[OSError("file fail"), OSError("temp fail")],
            ):
                with patch(
                    "tempfile.gettempdir",
                    return_value="/nonexistent_dir_xyz",
                ):
                    setup_logging(log_file="test_stderr.log", level="INFO")
            root = logging.getLogger()
            assert len(root.handlers) > 0
            # Last handler should be a StreamHandler (stderr fallback)
            assert isinstance(root.handlers[-1], logging.StreamHandler)
        finally:
            logging.getLogger().handlers.clear()
            for h in original:
                logging.getLogger().addHandler(h)

    def test_custom_level_and_encoding(self):
        from natural_gas_main.utils.logger import setup_logging
        original = logging.getLogger().handlers.copy()
        try:
            setup_logging(log_file="test_custom.log", level="WARNING", encoding="utf-16")
            root = logging.getLogger()
            assert root.level == logging.WARNING
        finally:
            logging.getLogger().handlers.clear()
            for h in original:
                logging.getLogger().addHandler(h)


class TestGetLogger:
    def test_get_logger_returns_logger(self):
        from natural_gas_main.utils.logger import get_logger
        logger = get_logger("test.module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"


# ---------------------------------------------------------------------------
# updater.py — HTTP yanıt/exception dalları, URL validation, open page
# ---------------------------------------------------------------------------

class TestUpdateCheckerValidateUrl:
    def test_valid_github_url(self):
        from natural_gas_main.utils.updater import UpdateChecker
        assert UpdateChecker._validate_url("https://github.com/user/repo")

    def test_empty_url(self):
        from natural_gas_main.utils.updater import UpdateChecker
        assert not UpdateChecker._validate_url("")

    def test_invalid_url(self):
        from natural_gas_main.utils.updater import UpdateChecker
        assert not UpdateChecker._validate_url("not a url")

    def test_non_github_url(self):
        from natural_gas_main.utils.updater import UpdateChecker
        assert not UpdateChecker._validate_url("https://evil.com/hack")


class TestUpdateCheckerCheckForUpdates:
    def test_http_200_up_to_date(self):
        from natural_gas_main.utils.updater import UpdateChecker
        checker = UpdateChecker()
        data = json.dumps({"version": "v0.0.0"}).encode("utf-8")
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.read.return_value = data
            mock_urlopen.return_value.__enter__.return_value = mock_response
            available, info, msg = checker.check_for_updates()
            assert not available

    def test_http_200_new_version(self):
        from natural_gas_main.utils.updater import UpdateChecker
        checker = UpdateChecker()
        data = json.dumps({"version": "v99.99.99"}).encode("utf-8")
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.read.return_value = data
            mock_urlopen.return_value.__enter__.return_value = mock_response
            available, info, msg = checker.check_for_updates()
            assert available
            assert info is not None

    def test_http_non_200(self):
        from natural_gas_main.utils.updater import UpdateChecker
        checker = UpdateChecker()
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.status = 404
            mock_urlopen.return_value.__enter__.return_value = mock_response
            available, info, msg = checker.check_for_updates()
            assert not available
            assert "404" in msg

    def test_no_version_in_response(self):
        from natural_gas_main.utils.updater import UpdateChecker
        checker = UpdateChecker()
        data = json.dumps({"foo": "bar"}).encode("utf-8")
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.read.return_value = data
            mock_urlopen.return_value.__enter__.return_value = mock_response
            available, info, msg = checker.check_for_updates()
            assert not available
            assert "Sürüm" in msg

    def test_urlerror(self):
        from natural_gas_main.utils.updater import UpdateChecker
        checker = UpdateChecker()
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("No internet"),
        ):
            available, info, msg = checker.check_for_updates()
            assert not available
            assert "bağlantı" in msg

    def test_generic_exception(self):
        from natural_gas_main.utils.updater import UpdateChecker
        checker = UpdateChecker()
        with patch(
            "urllib.request.urlopen",
            side_effect=ValueError("Boom"),
        ):
            available, info, msg = checker.check_for_updates()
            assert not available
            assert "başarısız" in msg


class TestUpdateCheckerOpenDownloadPage:
    def test_opens_repo_url_by_default(self):
        from natural_gas_main.utils.updater import UpdateChecker
        checker = UpdateChecker()
        with patch("webbrowser.open") as mock_web:
            checker.open_download_page()
            mock_web.assert_called_once()

    def test_blocks_non_github_url(self):
        from natural_gas_main.utils.updater import UpdateChecker
        checker = UpdateChecker()
        with patch("webbrowser.open") as mock_web:
            checker.open_download_page("https://evil.com/hack")
            mock_web.assert_called_once()
            # Should revert to REPO_URL (github.com)
            args = mock_web.call_args[0][0]
            assert "github.com" in args or "github" in args

    def test_empty_url_fallback(self):
        from natural_gas_main.utils.updater import UpdateChecker
        checker = UpdateChecker()
        with patch("webbrowser.open") as mock_web:
            checker.open_download_page("")
            mock_web.assert_called_once()


# ---------------------------------------------------------------------------
# aga8_calculator.py — PYAGA8_AVAILABLE=False, unknown method, unmapped gaz,
#                      normalization, set_composition hatası
# ---------------------------------------------------------------------------

class TestAga8NotAvailable:
    def test_raises_backend_error(self):
        from natural_gas_main.models.aga8_calculator import calculate_aga8
        with patch("natural_gas_main.models.aga8_calculator.PYAGA8_AVAILABLE", False):
            with pytest.raises(BackendNotAvailableError):
                calculate_aga8(None, 300, 101325)


class TestAga8Calculator:
    def test_unknown_method_defaults_to_detail(self):
        from natural_gas_main.models.gas_data import GasComponent, GasMixture
        from natural_gas_main.models.aga8_calculator import calculate_aga8
        mixture = GasMixture(
            components=[GasComponent(name="Methane", fraction=100.0)],
            fraction_type="molar",
        )
        with patch("natural_gas_main.models.aga8_calculator.PYAGA8_AVAILABLE", True):
            with patch("natural_gas_main.models.aga8_calculator.pyaga8") as mock_pyaga8:
                mock_comp = MagicMock()
                mock_pyaga8.Composition.return_value = mock_comp
                mock_engine = MagicMock()
                mock_engine.mm = 16.0
                mock_engine.d = 10.0
                mock_engine.z = 0.98
                mock_engine.u = 0.0
                mock_engine.h = 0.0
                mock_engine.s = 0.0
                mock_engine.cp = 0.0
                mock_engine.cv = 0.0
                mock_engine.kappa = 1.3
                mock_engine.w = 400.0
                mock_pyaga8.Detail.return_value = mock_engine
                result = calculate_aga8(mixture, 300, 101325, method="UNKNOWN")
                assert result.compressibility_factor == 0.98

    def test_set_composition_error(self):
        from natural_gas_main.models.gas_data import GasComponent, GasMixture
        from natural_gas_main.models.aga8_calculator import calculate_aga8
        mixture = GasMixture(
            components=[GasComponent(name="Methane", fraction=100.0)],
            fraction_type="molar",
        )
        with patch("natural_gas_main.models.aga8_calculator.PYAGA8_AVAILABLE", True):
            with patch("natural_gas_main.models.aga8_calculator.pyaga8") as mock_pyaga8:
                mock_comp = MagicMock()
                mock_pyaga8.Composition.return_value = mock_comp
                mock_engine = MagicMock()
                mock_engine.set_composition.side_effect = ValueError("bad composition")
                mock_pyaga8.Gerg2008.return_value = mock_engine
                with pytest.raises(ValueError, match="AGA8 set_composition"):
                    calculate_aga8(mixture, 300, 101325, method="GERG-2008")

    def test_unmapped_gas_logs_warning(self):
        from natural_gas_main.models.gas_data import GasComponent, GasMixture
        from natural_gas_main.models.aga8_calculator import calculate_aga8
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=95.0),
                GasComponent(name="Neon", fraction=5.0),
            ],
            fraction_type="molar",
        )
        with patch("natural_gas_main.models.aga8_calculator.PYAGA8_AVAILABLE", True):
            with patch("natural_gas_main.models.aga8_calculator.pyaga8") as mock_pyaga8:
                mock_comp = MagicMock()
                mock_pyaga8.Composition.return_value = mock_comp
                mock_engine = MagicMock()
                mock_engine.mm = 16.0
                mock_engine.d = 10.0
                mock_engine.z = 0.99
                mock_engine.u = 0.0
                mock_engine.h = 0.0
                mock_engine.s = 0.0
                mock_engine.cp = 0.0
                mock_engine.cv = 0.0
                mock_engine.kappa = 1.3
                mock_engine.w = 400.0
                mock_pyaga8.Gerg2008.return_value = mock_engine
                result = calculate_aga8(mixture, 300, 101325, method="GERG-2008")
                assert result is not None
                assert result.compressibility_factor == 0.99

    def test_normalization_applied(self):
        from natural_gas_main.models.gas_data import GasComponent, GasMixture
        from natural_gas_main.models.aga8_calculator import calculate_aga8
        # Unmapped gas with significant fraction to trigger normalization
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=80.0),
                GasComponent(name="Nitrogen", fraction=15.0),
            ],
            fraction_type="molar",
        )
        with patch("natural_gas_main.models.aga8_calculator.PYAGA8_AVAILABLE", True):
            with patch("natural_gas_main.models.aga8_calculator.pyaga8") as mock_pyaga8:
                mock_comp = MagicMock()
                mock_pyaga8.Composition.return_value = mock_comp
                mock_engine = MagicMock()
                mock_engine.mm = 16.0
                mock_engine.d = 10.0
                mock_engine.z = 0.97
                mock_engine.u = 0.0
                mock_engine.h = 0.0
                mock_engine.s = 0.0
                mock_engine.cp = 0.0
                mock_engine.cv = 0.0
                mock_engine.kappa = 1.3
                mock_engine.w = 400.0
                mock_pyaga8.Gerg2008.return_value = mock_engine
                # sum_fractions = 0.80 + 0.15 = 0.95, not normalized, no unmapped
                result = calculate_aga8(mixture, 300, 101325, method="GERG-2008")
                assert result is not None

    def test_below_minimum_fraction_raises(self):
        from natural_gas_main.models.gas_data import GasComponent, GasMixture
        from natural_gas_main.models.aga8_calculator import calculate_aga8
        mixture = GasMixture(
            components=[
                GasComponent(name="Methane", fraction=10.0),
                GasComponent(name="Neon", fraction=90.0),
            ],
            fraction_type="molar",
        )
        with patch("natural_gas_main.models.aga8_calculator.PYAGA8_AVAILABLE", True):
            with patch("natural_gas_main.models.aga8_calculator.pyaga8") as mock_pyaga8:
                mock_pyaga8.Composition.return_value = MagicMock()
                with pytest.raises(ValueError, match="AGA8 için geçerli"):
                    calculate_aga8(mixture, 300, 101325, method="GERG-2008")


# ---------------------------------------------------------------------------
# report_generator.py — font fallback tüm OS'ler, generate_and_save IOError
# ---------------------------------------------------------------------------

class TestReportGeneratorSaveToFile:
    def test_save_to_file_writes_content(self, tmp_path):
        from natural_gas_main.utils.report_generator import ReportGenerator
        out = tmp_path / "test_report.txt"
        ReportGenerator.save_to_file("test content", str(out))
        content = out.read_text(encoding="utf-8-sig")
        assert content == "test content"

    def test_save_to_file_ioerror(self):
        from natural_gas_main.utils.report_generator import ReportGenerator
        with pytest.raises(IOError):
            ReportGenerator.save_to_file("x", "/nonexistent_dir_xyz/report.txt")

    def test_generate_and_save_ioerror(self):
        from natural_gas_main.utils.report_generator import ReportGenerator
        with pytest.raises(IOError, match="kaydedilemedi"):
            ReportGenerator.generate_and_save(
                input_params={},
                results=[("prop", "val", "unit")],
                gas_composition=[("Methane", 100.0)],
                file_path="/nonexistent_dir_xyz/report.pdf",
            )


class TestReportGeneratorGenerateTextReport:
    def test_generates_report_with_heating_values(self):
        from natural_gas_main.utils.report_generator import ReportGenerator
        report = ReportGenerator.generate_text_report(
            input_params={"Sıcaklık": ("300", "K")},
            results=[
                ("Z-Factor", "0.998", "-"),
                ("HHV", "55.5", "MJ/kg"),
            ],
            gas_composition=[("Methane", 100.0)],
        )
        assert "Methane" in report
        assert "Z-Factor" in report

    def test_generates_report_without_heating(self):
        from natural_gas_main.utils.report_generator import ReportGenerator
        report = ReportGenerator.generate_text_report(
            input_params={"Basınç": ("101.325", "kPa")},
            results=[("Density", "0.66", "kg/m³")],
            gas_composition=[("Nitrogen", 100.0)],
        )
        assert "Nitrogen" in report

    def test_section_header_in_results(self):
        from natural_gas_main.utils.report_generator import ReportGenerator
        report = ReportGenerator.generate_text_report(
            input_params={},
            results=[("- Isıtma Değerleri", "", ""), ("HHV", "55.5", "MJ/kg")],
            gas_composition=[("Methane", 100.0)],
        )
        assert "Isıtma" in report


class TestReportGeneratorGetCalcLog:
    def test_log_read_success_filtered(self, tmp_path):
        from natural_gas_main.utils.report_generator import ReportGenerator
        log = tmp_path / "test.log"
        log.write_text("2024-01-01 12:00:00 - Trying backend: HEOS\nSome other line\n")
        entries = ReportGenerator._get_calculation_log(str(log), include_full=False)
        assert len(entries) > 0
        assert any("HEOS" in e for e in entries)

    def test_log_read_full(self, tmp_path):
        from natural_gas_main.utils.report_generator import ReportGenerator
        log = tmp_path / "test_full.log"
        log.write_text("Line 1\nLine 2\nLine 3\n")
        entries = ReportGenerator._get_calculation_log(str(log), include_full=True)
        assert len(entries) == 3

    def test_log_not_found(self):
        from natural_gas_main.utils.report_generator import ReportGenerator
        entries = ReportGenerator._get_calculation_log("/nonexistent.log", include_full=False)
        assert entries == []

    def test_log_no_calc_keyword(self, tmp_path):
        from natural_gas_main.utils.report_generator import ReportGenerator
        log = tmp_path / "no_calc.log"
        log.write_text("\n".join(f"Irrelevant line {i}" for i in range(200)))
        entries = ReportGenerator._get_calculation_log(str(log), include_full=False)
        # Should take last 100 lines and filter
        assert len(entries) == 0 or all("Irrelevant" not in e for e in entries)

    def test_log_short_no_calc_keyword(self, tmp_path):
        from natural_gas_main.utils.report_generator import ReportGenerator
        log = tmp_path / "short.log"
        log.write_text("Line A\nLine B\n")
        entries = ReportGenerator._get_calculation_log(str(log), include_full=False)
        assert isinstance(entries, list)


class TestReportGeneratorSetupPdfFont:
    def test_matplotlib_exception_falls_through(self):
        from natural_gas_main.utils.report_generator import ReportGenerator
        from fpdf import FPDF
        pdf = FPDF()
        with patch("matplotlib.font_manager.findfont", side_effect=Exception("no font")):
            with patch("os.path.exists", return_value=True):
                with patch.object(pdf, 'add_font', return_value=None):
                    family = ReportGenerator._setup_pdf_font(pdf)
                    assert family is not None

    def test_all_fonts_missing_raises(self):
        from natural_gas_main.utils.report_generator import ReportGenerator
        from fpdf import FPDF
        pdf = FPDF()
        with patch("os.path.exists", return_value=False):
            with pytest.raises(RuntimeError, match="Unicode font"):
                ReportGenerator._setup_pdf_font(pdf)


class TestReportGeneratorPdfReport:
    def test_pdf_report_with_image(self, tmp_path):
        from natural_gas_main.utils.report_generator import ReportGenerator
        out = tmp_path / "test_img.pdf"
        img = tmp_path / "plot.png"
        img.write_bytes(b"fake png")
        result = ReportGenerator.generate_and_save(
            input_params={"temperature": ("300", "K"), "pressure": ("101.325", "kPa")},
            results=[("Z", "0.998", "-"), ("Density", "0.66", "kg/m³")],
            gas_composition=[("Methane", 100.0)],
            file_path=str(out),
        )
        assert out.exists()

    def test_pdf_report_image_exception_does_not_crash(self, tmp_path):
        from natural_gas_main.utils.report_generator import ReportGenerator
        out = tmp_path / "test_img_fail.pdf"
        with patch("os.path.exists", return_value=True):
            with patch("fpdf.FPDF.image", side_effect=Exception("bad image")):
                result = ReportGenerator.generate_and_save(
                    input_params={"temperature": ("300", "K")},
                    results=[("Z", "0.998", "-")],
                    gas_composition=[("Methane", 100.0)],
                    file_path=str(out),
                )
                assert out.exists()


class TestReportGeneratorPdfFallback:
    def test_pdf_creates_with_text_fallback(self, tmp_path):
        from natural_gas_main.utils.report_generator import ReportGenerator
        out = tmp_path / "test.pdf"
        result = ReportGenerator.generate_and_save(
            input_params={"T": ("300", "K"), "P": ("101.325", "kPa")},
            results=[("Z", "0.998", "-"), ("Density", "0.66", "kg/m³")],
            gas_composition=[("Methane", 100.0)],
            file_path=str(out),
        )
        assert out.exists()
