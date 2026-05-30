"""Edge case tests for preferences module (set-then-get, cache invalidation)."""

import json
import pytest
from natural_gas_main.config import preferences


@pytest.fixture(autouse=True)
def reset_cache():
    preferences._cache = None


class TestPreferencesCacheBehavior:
    def test_get_set_get_cycle(self, tmp_path, monkeypatch):
        """Set a value then get it back; no disk re-read."""
        d = tmp_path / "prefs"
        d.mkdir()
        monkeypatch.setattr(preferences, "_prefs_file", lambda: d / "prefs.json")
        monkeypatch.setattr(preferences, "_prefs_dir", lambda: d)

        preferences.set_preference("a", 1)
        assert preferences.get_preference("a") == 1
        preferences.set_preference("b", 2)
        assert preferences.get_preference("a") == 1
        assert preferences.get_preference("b") == 2

    def test_set_then_clear_cache(self, tmp_path, monkeypatch):
        """After cache reset, should re-read from disk."""
        d = tmp_path / "prefs"
        d.mkdir()
        f = d / "prefs.json"
        monkeypatch.setattr(preferences, "_prefs_file", lambda: f)
        monkeypatch.setattr(preferences, "_prefs_dir", lambda: d)

        preferences.set_preference("k", "v1")
        preferences._cache = None
        assert preferences.get_preference("k") == "v1"

    def test_set_overwrites_previous(self, tmp_path, monkeypatch):
        """Re-setting a key should overwrite the old value."""
        d = tmp_path / "prefs"
        d.mkdir()
        monkeypatch.setattr(preferences, "_prefs_file", lambda: d / "prefs.json")
        monkeypatch.setattr(preferences, "_prefs_dir", lambda: d)

        preferences.set_preference("x", "first")
        preferences.set_preference("x", "second")
        assert preferences.get_preference("x") == "second"

    def test_multiple_keys_independent(self, tmp_path, monkeypatch):
        """Multiple keys should not interfere."""
        d = tmp_path / "prefs"
        d.mkdir()
        monkeypatch.setattr(preferences, "_prefs_file", lambda: d / "prefs.json")
        monkeypatch.setattr(preferences, "_prefs_dir", lambda: d)

        for i in range(10):
            preferences.set_preference(f"key_{i}", i)

        for i in range(10):
            assert preferences.get_preference(f"key_{i}") == i

    def test_nonexistent_key_returns_none(self):
        assert preferences.get_preference("does_not_exist") is None

    def test_nonexistent_key_returns_custom_default(self):
        assert preferences.get_preference("nope", "fallback") == "fallback"

    def test_empty_file_returns_default(self, tmp_path, monkeypatch):
        """Empty JSON file ({})."""
        d = tmp_path / "prefs"
        d.mkdir()
        f = d / "prefs.json"
        f.write_text("{}")
        monkeypatch.setattr(preferences, "_prefs_file", lambda: f)
        monkeypatch.setattr(preferences, "_prefs_dir", lambda: d)
        preferences._cache = None

        assert preferences.get_preference("any", "default") == "default"

    def test_real_values_persist_after_reload(self, tmp_path, monkeypatch):
        """Values survive a cache clear."""
        d = tmp_path / "prefs"
        d.mkdir()
        monkeypatch.setattr(preferences, "_prefs_file", lambda: d / "prefs.json")
        monkeypatch.setattr(preferences, "_prefs_dir", lambda: d)

        preferences.set_preference("theme", "dark")
        preferences.set_preference("lang", "tr")

        preferences._cache = None
        assert preferences.get_preference("theme") == "dark"
        assert preferences.get_preference("lang") == "tr"
