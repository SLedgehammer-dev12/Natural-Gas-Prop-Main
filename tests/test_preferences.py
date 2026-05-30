"""Tests for preferences module (with in-memory cache)."""

import json
import tempfile
import os
from pathlib import Path

import pytest

from natural_gas_main.config import preferences


@pytest.fixture(autouse=True)
def reset_cache():
    """Reset the in-memory cache before each test."""
    preferences._cache = None


def test_default_on_missing_key():
    assert preferences.get_preference("nonexistent_key") is None
    assert preferences.get_preference("nonexistent_key", 42) == 42


def test_set_and_get(tmp_path, monkeypatch):
    prefs_dir = tmp_path / "NaturalGasPropMain"
    prefs_dir.mkdir()

    def fake_prefs_file():
        return prefs_dir / "user_preferences.json"

    monkeypatch.setattr(preferences, "_prefs_file", fake_prefs_file)
    monkeypatch.setattr(preferences, "_prefs_dir", lambda: prefs_dir)

    preferences.set_preference("theme", "dark")
    assert preferences.get_preference("theme") == "dark"

    preferences.set_preference("version", "v2.0")
    assert preferences.get_preference("version") == "v2.0"


def test_persistence_across_calls(tmp_path, monkeypatch):
    prefs_dir = tmp_path / "NaturalGasPropMain"
    prefs_dir.mkdir()

    def fake_prefs_file():
        return prefs_dir / "user_preferences.json"

    monkeypatch.setattr(preferences, "_prefs_file", fake_prefs_file)
    monkeypatch.setattr(preferences, "_prefs_dir", lambda: prefs_dir)

    preferences.set_preference("key", "value1")
    preferences._cache = None
    assert preferences.get_preference("key") == "value1"


def test_cache_avoids_disk_read(tmp_path, monkeypatch):
    prefs_dir = tmp_path / "NaturalGasPropMain"
    prefs_dir.mkdir()
    prefs_file = prefs_dir / "user_preferences.json"
    prefs_file.write_text(json.dumps({"cached": "from_disk"}))

    def fake_prefs_file():
        return prefs_file

    monkeypatch.setattr(preferences, "_prefs_file", fake_prefs_file)
    monkeypatch.setattr(preferences, "_prefs_dir", lambda: prefs_dir)

    first = preferences.get_preference("cached")
    assert first == "from_disk"

    prefs_file.write_text(json.dumps({"cached": "changed_on_disk"}))
    second = preferences.get_preference("cached")
    assert second == "from_disk", "Cache should not re-read disk"


def test_corrupted_json_does_not_crash(tmp_path, monkeypatch):
    prefs_dir = tmp_path / "NaturalGasPropMain"
    prefs_dir.mkdir()
    prefs_file = prefs_dir / "user_preferences.json"
    prefs_file.write_text("not valid json{{{")

    def fake_prefs_file():
        return prefs_file

    monkeypatch.setattr(preferences, "_prefs_file", fake_prefs_file)
    monkeypatch.setattr(preferences, "_prefs_dir", lambda: prefs_dir)
    preferences._cache = None

    result = preferences.get_preference("any", "fallback")
    assert result == "fallback"


def test_missing_file_returns_default(tmp_path, monkeypatch):
    prefs_dir = tmp_path / "NaturalGasPropMain"
    prefs_dir.mkdir()

    def fake_prefs_file():
        return prefs_dir / "nonexistent.json"

    monkeypatch.setattr(preferences, "_prefs_file", fake_prefs_file)
    monkeypatch.setattr(preferences, "_prefs_dir", lambda: prefs_dir)
    preferences._cache = None

    assert preferences.get_preference("key", "default") == "default"
