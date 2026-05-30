"""
User preferences management.

Handles loading and saving of user preferences such as 'Don't show again' flags.
Uses an in-memory cache to avoid reading the file on every get_preference call.
"""

import json
import os
import logging
from pathlib import Path

_cache: dict | None = None


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
    global _cache
    if _cache is not None:
        return _cache.copy()
    
    prefs_path = _prefs_file()
    if not prefs_path.exists():
        _cache = {}
        return {}
    
    try:
        with open(prefs_path, 'r', encoding='utf-8') as f:
            _cache = json.load(f)
        return _cache.copy()
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to load preferences: {e}")
        _cache = {}
        return {}


def save_preferences(prefs: dict) -> None:
    """
    Save user preferences to file.
    
    Args:
        prefs: Dictionary of preferences to save.
    """
    global _cache
    try:
        current = load_preferences()
        current.update(prefs)
        _cache = current
        
        prefs_path = _prefs_file()
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
