import json

from natural_gas_main import __version__
from natural_gas_main.config.settings import config


def test_release_version_is_v1_4_1():
    assert __version__ == "v1.4.1"
    assert config.APP_VERSION == "v1.4.1"
    assert "v1.4.1" in config.WINDOW_TITLE


def test_physical_constants_were_not_rewritten_by_versioning():
    assert config.P_STANDARD == 101325.0
    assert config.P_NORMAL == 101325.0
    assert config.STANDARD_CONDITIONS["ISO 13443 (15°C, 1 atm)"]["P"] == 101325.0
    assert config.M3_TO_SCF == 35.3147


def test_version_json_matches_release():
    """version.json reads the correct version from the file."""
    version_data = json.loads(open("version.json", encoding="utf-8").read())
    assert version_data["product"] == "Natural Gas Prop Main"
    assert version_data["version"] == "v1.4.1"
    assert version_data["download_url"].endswith("/releases/tag/v1.4.1")
