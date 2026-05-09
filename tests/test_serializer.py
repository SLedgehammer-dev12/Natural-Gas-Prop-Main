import pytest

from natural_gas_main.utils.data_serializer import (
    DataSerializationError,
    load_inputs_from_file,
    save_inputs_to_file,
    validate_loaded_data,
)


def test_save_load_round_trip_adds_ngp_extension(tmp_path):
    target = tmp_path / "composition"
    data = {
        "composition": [
            {"name": "Methane", "fraction": 90.0},
            {"name": "Propane", "fraction": 10.0},
        ],
        "fraction_type": "molar",
    }

    save_inputs_to_file(data, str(target))
    loaded = load_inputs_from_file(str(target) + ".ngp")

    assert loaded["version"] == "1.0"
    assert loaded["composition"] == data["composition"]
    assert validate_loaded_data(loaded)


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"composition": "Methane"},
        {"composition": [{"name": "Methane"}]},
        {"composition": [{"fraction": 100.0}]},
    ],
)
def test_validate_loaded_data_rejects_bad_shapes(payload):
    assert not validate_loaded_data(payload)


def test_load_missing_file_raises_data_serialization_error(tmp_path):
    with pytest.raises(DataSerializationError):
        load_inputs_from_file(str(tmp_path / "missing.ngp"))
