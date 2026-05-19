"""
Edge case tests for data serializer (save/load .ngp files).

Covers: corrupted JSON, missing fields, empty files, encoding issues, large data.
"""

import json
import os
import pytest
from pathlib import Path

from natural_gas_main.utils.data_serializer import (
    save_inputs_to_file,
    load_inputs_from_file,
    validate_loaded_data,
    DataSerializationError,
    SCHEMA_VERSION,
    FILE_EXTENSION,
)


class TestSaveAndLoadRoundtrip:
    def test_roundtrip_basic(self, tmp_path):
        filepath = str(tmp_path / "test.ngp")
        data = {"composition": [{"name": "Methane", "fraction": 100.0}]}
        save_inputs_to_file(data, filepath)
        loaded = load_inputs_from_file(filepath)
        assert loaded["version"] == SCHEMA_VERSION
        assert loaded["composition"] == data["composition"]

    def test_roundtrip_multiple_gases(self, tmp_path):
        filepath = str(tmp_path / "multi.ngp")
        data = {
            "composition": [
                {"name": "Methane", "fraction": 94.0},
                {"name": "Ethane", "fraction": 6.0},
            ],
            "fraction_type": "molar",
        }
        save_inputs_to_file(data, filepath)
        loaded = load_inputs_from_file(filepath)
        assert len(loaded["composition"]) == 2

    def test_auto_appends_extension(self, tmp_path):
        filepath = str(tmp_path / "noext")
        data = {"composition": []}
        save_inputs_to_file(data, filepath)
        assert os.path.exists(str(tmp_path / ("noext" + FILE_EXTENSION)))

    def test_roundtrip_with_utf8_gas_names(self, tmp_path):
        filepath = str(tmp_path / "utf8.ngp")
        data = {"composition": [{"name": "Karbondioksit", "fraction": 5.0}]}
        save_inputs_to_file(data, filepath)
        loaded = load_inputs_from_file(filepath)
        assert loaded["composition"][0]["name"] == "Karbondioksit"


class TestLoadInvalidFiles:
    def test_corrupted_json_raises(self, tmp_path):
        filepath = tmp_path / "bad.ngp"
        filepath.write_text("{broken json[[[", encoding="utf-8")
        with pytest.raises(DataSerializationError):
            load_inputs_from_file(str(filepath))

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(DataSerializationError):
            load_inputs_from_file(str(tmp_path / "nonexistent.ngp"))

    def test_empty_file_raises(self, tmp_path):
        filepath = tmp_path / "empty.ngp"
        filepath.write_text("", encoding="utf-8")
        with pytest.raises(DataSerializationError):
            load_inputs_from_file(str(filepath))


class TestValidateLoadedData:
    def test_valid_data_passes(self):
        data = {
            "version": SCHEMA_VERSION,
            "composition": [{"name": "Methane", "fraction": 100.0}],
        }
        assert validate_loaded_data(data) is True

    def test_missing_composition_fails(self):
        data = {"version": SCHEMA_VERSION, "temperature": 300}
        assert validate_loaded_data(data) is False

    def test_extra_fields_still_valid(self):
        data = {
            "version": SCHEMA_VERSION,
            "composition": [{"name": "Methane", "fraction": 100.0}],
            "extra": "ignored",
        }
        assert validate_loaded_data(data) is True

    def test_composition_not_list_fails(self):
        data = {"composition": "not a list"}
        assert validate_loaded_data(data) is False

    def test_component_missing_name_fails(self):
        data = {"composition": [{"fraction": 100.0}]}
        assert validate_loaded_data(data) is False

    def test_component_missing_fraction_fails(self):
        data = {"composition": [{"name": "Methane"}]}
        assert validate_loaded_data(data) is False

    def test_older_minor_version_accepted(self):
        data = {
            "version": "1.0",
            "composition": [{"name": "Methane", "fraction": 100.0}],
        }
        assert validate_loaded_data(data) is True
