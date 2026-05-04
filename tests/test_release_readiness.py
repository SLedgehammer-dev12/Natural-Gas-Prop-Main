import json

from natural_gas_g5 import __version__
from natural_gas_g5.config.settings import config


def test_release_version_is_v1_0():
    assert __version__ == "v1.0"
    assert config.APP_VERSION == "v1.0"
    assert "v1.0" in config.WINDOW_TITLE


def test_physical_constants_were_not_rewritten_by_versioning():
    assert config.P_STANDARD == 101325.0
    assert config.P_NORMAL == 101325.0
    assert config.STANDARD_CONDITIONS["ISO 13443 (15°C, 1 atm)"]["P"] == 101325.0
    assert config.M3_TO_SCF == 35.3147


def test_version_json_matches_release(tmp_path):
    version_data = json.loads(open("version.json", encoding="utf-8").read())
    assert version_data["product"] == "Natural Gas Prop Main"
    assert version_data["version"] == "v1.0"
    assert version_data["download_url"].endswith("/releases/tag/v1.0")
