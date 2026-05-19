"""
User preferences management.

Handles loading and saving of user preferences such as 'Don't show again' flags.
"""

import json
import os
import logging
from pathlib import Path


def _prefs_dir() -> Path:
    """Return platform-appropriate preferences directory."""
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "NaturalGasPropMain"


def _prefs_file() -> Path:
    path = _prefs_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path / "user_preferences.json"

def load_preferences() -> dict:
    """
    Load user preferences from file.
    
    Returns:
        Dictionary of preferences.
    """
    prefs_path = _prefs_file()
    if not prefs_path.exists():
        return {}
    
    try:
        with open(prefs_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to load preferences: {e}")
        return {}


def save_preferences(prefs: dict) -> None:
    """
    Save user preferences to file.
    
    Args:
        prefs: Dictionary of preferences to save.
    """
    try:
        prefs_path = _prefs_file()
        current = load_preferences()
        current.update(prefs)
        
        with open(prefs_path, 'w', encoding='utf-8') as f:
            json.dump(current, f, indent=4)
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to save preferences: {e}")

def get_preference(key: str, default=None):
    """Get a specific preference value."""
    prefs = load_preferences()
    return prefs.get(key, default)

def set_preference(key: str, value) -> None:
    """Set a specific preference value."""
    save_preferences({key: value})
