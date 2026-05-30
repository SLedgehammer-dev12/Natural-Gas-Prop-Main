import json
from pathlib import Path

from natural_gas_main import __version__
from natural_gas_main.config.settings import config

ROOT = Path(__file__).parent.parent


def test_config_version_consistent():
    """Config constants reference the same version string."""
    assert __version__ == config.APP_VERSION
    assert config.APP_VERSION in config.WINDOW_TITLE


def test_physical_constants_not_rewritten():
    assert config.P_STANDARD == 101325.0
    assert config.P_NORMAL == 101325.0
    assert config.STANDARD_CONDITIONS["ISO 13443 (15°C, 1 atm)"]["P"] == 101325.0
    assert config.M3_TO_SCF == 35.3147


def test_version_json_matches_code():
    """version.json version matches the codebase."""
    with open(ROOT / "version.json", encoding="utf-8") as f:
        version_data = json.load(f)

    assert version_data["product"] == "Natural Gas Prop Main"
    assert version_data["version"] == config.APP_VERSION
    assert version_data["download_url"].endswith(f"/releases/tag/{config.APP_VERSION}")


def test_pyproject_version_matches_code():
    """pyproject.toml version matches config."""
    import tomllib
    with open(ROOT / "pyproject.toml", "rb") as f:
        pyproject = tomllib.load(f)

    py_version = pyproject["project"]["version"]
    assert config.APP_VERSION.lstrip("v") == py_version
