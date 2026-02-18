"""Tests for app.preferences module."""
import json
import os
import pytest
from unittest.mock import patch


# ── load_preferences ────────────────────────────────────────────


class TestLoadPreferences:
    """Tests for load_preferences()."""

    def test_returns_defaults_when_no_file(self, tmp_path):
        fake_path = str(tmp_path / "nonexistent.json")
        with patch("app.preferences.PREFS_FILE", fake_path):
            from app.preferences import load_preferences
            prefs = load_preferences()
        assert prefs["theme"] == "dark"
        assert prefs["language"] == "vi"
        assert prefs["captcha_mode"] == "extension"

    def test_loads_existing_file(self, tmp_path):
        fake_path = str(tmp_path / "prefs.json")
        with open(fake_path, "w") as f:
            json.dump({"theme": "light", "language": "en"}, f)
        with patch("app.preferences.PREFS_FILE", fake_path):
            from app.preferences import load_preferences
            prefs = load_preferences()
        assert prefs["theme"] == "light"
        assert prefs["language"] == "en"
        # Defaults filled in for missing keys
        assert prefs["captcha_mode"] == "extension"

    def test_returns_defaults_on_corrupt_json(self, tmp_path):
        fake_path = str(tmp_path / "corrupt.json")
        with open(fake_path, "w") as f:
            f.write("{{{invalid json")
        with patch("app.preferences.PREFS_FILE", fake_path):
            from app.preferences import load_preferences
            prefs = load_preferences()
        assert prefs == {"theme": "dark", "language": "vi", "captcha_mode": "extension"}

    def test_returns_copy_not_reference(self, tmp_path):
        fake_path = str(tmp_path / "nonexistent.json")
        with patch("app.preferences.PREFS_FILE", fake_path):
            from app.preferences import load_preferences
            p1 = load_preferences()
            p2 = load_preferences()
        assert p1 is not p2


# ── save_preferences ────────────────────────────────────────────


class TestSavePreferences:
    """Tests for save_preferences()."""

    def test_saves_to_file(self, tmp_path):
        fake_path = str(tmp_path / "prefs.json")
        with patch("app.preferences.PREFS_FILE", fake_path):
            from app.preferences import save_preferences
            save_preferences({"theme": "light", "language": "en"})
        with open(fake_path, "r") as f:
            data = json.load(f)
        assert data["theme"] == "light"
        assert data["language"] == "en"

    def test_handles_write_error(self, tmp_path):
        fake_path = str(tmp_path / "nonexistent_dir" / "prefs.json")
        with patch("app.preferences.PREFS_FILE", fake_path):
            from app.preferences import save_preferences
            # Should not raise, just log warning
            save_preferences({"theme": "dark"})


# ── save_preference ────────────────────────────────────────────


class TestSavePreference:
    """Tests for save_preference()."""

    def test_saves_single_key(self, tmp_path):
        fake_path = str(tmp_path / "prefs.json")
        with open(fake_path, "w") as f:
            json.dump({"theme": "dark", "language": "vi", "captcha_mode": "extension"}, f)
        with patch("app.preferences.PREFS_FILE", fake_path):
            from app.preferences import save_preference
            save_preference("theme", "light")
        with open(fake_path, "r") as f:
            data = json.load(f)
        assert data["theme"] == "light"
        assert data["language"] == "vi"
