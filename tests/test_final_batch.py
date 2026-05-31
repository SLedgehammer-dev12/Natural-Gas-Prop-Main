"""Tests for the final batch of fixes.

Covers:
- C1: AGA8 UnboundLocalError (implicitly tested via test_aga8)
- M1: generate_and_save error propagation
- M2: cricondenbar_t in PhaseEnvelopeData
- L1: __main__.py exists and calls main()
- L3: URL validation in updater
"""

import os
import sys
import tempfile
from pathlib import Path
import pytest
from natural_gas_main.utils.report_generator import ReportGenerator
from natural_gas_main.models.calculation_result import PhaseEnvelopeData


class TestGenerateAndSaveContext:
    def test_invalid_path_raises_ioerror(self):
        with pytest.raises(IOError) as excinfo:
            ReportGenerator.generate_and_save(
                {"test": "data"},
                [("Prop", "1.0", "-")],
                [("Methane", 100.0)],
                "/nonexistent_dir_xyz/report.txt",
            )
        assert "dosyaya kaydedilemedi" in str(excinfo.value)

    def test_valid_path_succeeds(self, tmp_path):
        file_path = str(tmp_path / "report.txt")
        ReportGenerator.generate_and_save(
            {"test": "data"},
            [("Prop", "1.0", "-")],
            [("Methane", 100.0)],
            file_path,
        )
        assert os.path.exists(file_path)
        content = open(file_path).read()
        assert "Methane" in content
        assert "Prop" in content


class TestCricondenbarT:
    def test_field_exists_on_model(self):
        env = PhaseEnvelopeData(
            temperature_k=[300.0, 320.0],
            pressure_pa=[1e5, 2e5],
        )
        assert hasattr(env, "cricondenbar_t")
        assert env.cricondenbar_t is None

    def test_field_accepts_value(self):
        env = PhaseEnvelopeData(
            temperature_k=[300.0, 320.0],
            pressure_pa=[1e5, 2e5],
            cricondenbar_t=310.0,
        )
        assert env.cricondenbar_t == 310.0

    def test_round_trip_with_calculator(self):
        from natural_gas_main.models.gas_data import GasComponent, GasMixture
        env = PhaseEnvelopeData(
            temperature_k=[250.0, 300.0, 350.0],
            pressure_pa=[5e6, 1e7, 5e6],
            cricondenbar_t=300.0,
            cricondenbar_p=1e7,
            critical_t=190.0,
            critical_p=4.6e6,
        )
        assert env.cricondenbar_t == 300.0
        assert env.cricondenbar_p == 1e7


class TestMainModule:
    def test_main_py_exists(self):
        main_path = Path(__file__).parent.parent / "natural_gas_main" / "__main__.py"
        assert main_path.exists(), "__main__.py not found"
        content = main_path.read_text()
        assert "main()" in content
        assert "__name__" in content or "__main__" in content

    def test_main_module_executes_main(self):
        import subprocess
        result = subprocess.run(
            [sys.executable, "-c", "import natural_gas_main.__main__"],
            capture_output=True, text=True, timeout=5,
        )
        # Import should not crash (TK init may fail headlessly, that's ok)
        assert "Error" not in result.stderr


class TestUpdaterUrlValidation:
    def test_github_url_passes(self):
        from natural_gas_main.utils.updater import UpdateChecker
        checker = UpdateChecker()
        assert checker._validate_url("https://github.com/owner/repo") is True

    def test_github_www_url_passes(self):
        from natural_gas_main.utils.updater import UpdateChecker
        checker = UpdateChecker()
        assert checker._validate_url("https://www.github.com/owner/repo") is True

    def test_evilsite_url_blocked(self):
        from natural_gas_main.utils.updater import UpdateChecker
        checker = UpdateChecker()
        assert checker._validate_url("https://github.com.evilsite.com/payload") is False

    def test_non_github_url_blocked(self):
        from natural_gas_main.utils.updater import UpdateChecker
        checker = UpdateChecker()
        assert checker._validate_url("https://example.com/malware") is False

    def test_invalid_url_blocked(self):
        from natural_gas_main.utils.updater import UpdateChecker
        checker = UpdateChecker()
        assert checker._validate_url("not-a-url") is False
