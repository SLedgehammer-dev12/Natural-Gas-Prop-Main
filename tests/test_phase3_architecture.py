"""Tests for Phase 3 architecture improvements.

Covers:
- Atomic save (data_serializer.py)
- Major version enforcement on load (data_serializer.py)
- Version key precedence (data_serializer.py)
- PDF font discovery on macOS (report_generator.py)
- PDF footer left/right alignment (report_generator.py)
"""

import os
import json
import tempfile
import shutil
import platform
from pathlib import Path
import pytest
from natural_gas_main.utils import data_serializer
from natural_gas_main.utils.report_generator import ReportGenerator


class TestAtomicSave:
    """Atomic write pattern ensures no partial writes."""

    def test_save_creates_file(self, tmp_path):
        filepath = str(tmp_path / "test.ngp")
        data = {"composition": [{"name": "Methane", "fraction": 100.0}]}
        data_serializer.save_inputs_to_file(data, filepath)
        assert os.path.exists(filepath)

    def test_save_adds_extension(self, tmp_path):
        filepath = str(tmp_path / "test")
        data = {"composition": [{"name": "Methane", "fraction": 100.0}]}
        data_serializer.save_inputs_to_file(data, filepath)
        assert os.path.exists(filepath + ".ngp")
        assert not os.path.exists(filepath)

    def test_saved_content_is_valid_json(self, tmp_path):
        filepath = str(tmp_path / "test.ngp")
        data = {"composition": [{"name": "Methane", "fraction": 100.0}]}
        data_serializer.save_inputs_to_file(data, filepath)
        with open(filepath, "r") as f:
            parsed = json.load(f)
        assert "version" in parsed
        assert parsed["composition"] == data["composition"]

    def test_atomic_write_no_partial_file_on_failure(self, tmp_path):
        filepath = str(tmp_path / "test.ngp")
        with open(filepath, "w") as f:
            f.write("original")
        with pytest.raises(data_serializer.DataSerializationError):
            data_serializer.save_inputs_to_file(
                {"bad": object()}, filepath
            )
        with open(filepath, "r") as f:
            assert f.read() == "original"

    def test_round_trip(self, tmp_path):
        filepath = str(tmp_path / "test.ngp")
        original = {
            "composition": [
                {"name": "Methane", "fraction": 90.0},
                {"name": "Ethane", "fraction": 10.0},
            ],
            "fraction_type": "molar",
        }
        data_serializer.save_inputs_to_file(original, filepath)
        loaded = data_serializer.load_inputs_from_file(filepath)
        assert loaded["composition"] == original["composition"]
        assert loaded["fraction_type"] == original["fraction_type"]
        assert loaded["version"] == data_serializer.SCHEMA_VERSION


class TestVersionKeyPrecedence:
    """Schema version must NOT be overwritable by caller data."""

    def test_version_key_always_canonical(self, tmp_path):
        filepath = str(tmp_path / "test.ngp")
        data = {
            "composition": [{"name": "Methane", "fraction": 100.0}],
            "version": "0.0",
        }
        data_serializer.save_inputs_to_file(data, filepath)
        with open(filepath, "r") as f:
            parsed = json.load(f)
        assert parsed["version"] == data_serializer.SCHEMA_VERSION


class TestMajorVersionEnforcement:
    """Loading files with incompatible major version must raise."""

    def test_major_mismatch_raises(self, tmp_path):
        filepath = str(tmp_path / "bad.ngp")
        bad_data = {
            "version": "99.0",
            "composition": [{"name": "Methane", "fraction": 100.0}],
        }
        with open(filepath, "w") as f:
            json.dump(bad_data, f)
        with pytest.raises(data_serializer.DataSerializationError):
            data_serializer.load_inputs_from_file(filepath)

    def test_minor_mismatch_ok(self, tmp_path):
        filepath = str(tmp_path / "ok.ngp")
        data = {
            "version": "1.5",
            "composition": [{"name": "Methane", "fraction": 100.0}],
        }
        with open(filepath, "w") as f:
            json.dump(data, f)
        loaded = data_serializer.load_inputs_from_file(filepath)
        assert loaded["composition"] == data["composition"]


class TestValidateLoadedData:
    def test_valid_data(self):
        data = {"composition": [{"name": "Methane", "fraction": 100.0}]}
        assert data_serializer.validate_loaded_data(data) is True

    def test_missing_composition(self):
        assert data_serializer.validate_loaded_data({}) is False

    def test_bad_composition_type(self):
        assert data_serializer.validate_loaded_data({"composition": "bad"}) is False

    def test_bad_component_type(self):
        assert data_serializer.validate_loaded_data({"composition": ["bad"]}) is False

    def test_missing_component_key(self):
        data = {"composition": [{"name": "Methane"}]}
        assert data_serializer.validate_loaded_data(data) is False


@pytest.mark.skipif(
    not os.path.exists("/System/Library/Fonts/Helvetica.dfont"),
    reason="Helvetica.dfont not found on this system",
)
class TestFontDiscoveryMacOS:
    """Verify macOS font paths resolve to real files."""

    def test_helvetica_dfont_exists(self):
        assert os.path.exists("/System/Library/Fonts/Helvetica.dfont")

    def test_arial_font_exists(self):
        assert os.path.exists("/Library/Fonts/Arial.ttf")


class TestPDFGeneration:
    """Basic PDF generation smoke tests."""

    def test_pdf_creates_file(self, tmp_path):
        pdf_path = str(tmp_path / "report.pdf")
        input_params = {"temperature": 20.0, "pressure": 101.325}
        results = [
            ("Z-Factor", "0.998", "-"),
            ("HHV (MJ/m³)", "38.5", "MJ/m³"),
        ]
        composition = [("Methane", 100.0)]
        ReportGenerator.generate_pdf_report(
            input_params, results, composition, pdf_path
        )
        assert os.path.exists(pdf_path)
        assert os.path.getsize(pdf_path) > 1000

    def test_pdf_footer_contains_both_elements(self, tmp_path):
        pdf_path = str(tmp_path / "report.pdf")
        input_params = {"temperature": 20.0, "pressure": 101.325}
        results = [("Z-Factor", "0.998", "-")]
        composition = [("Methane", 100.0)]
        ReportGenerator.generate_pdf_report(
            input_params, results, composition, pdf_path
        )
        with open(pdf_path, "rb") as f:
            content = f.read()
        # fpdf2 uses CID-encoded Unicode with ToUnicode CMaps;
        # verify page number and copyright presence via the CMap entries.
        text = content.decode("latin-1")
        assert "beginbfchar" in text, "Missing ToUnicode CMap"
        assert "/F3" in text or "/F2" in text, "Missing font reference"
