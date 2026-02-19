"""
Tests for ThemeManager — palette management, theme switching, QSS loading.
"""
import pytest
from unittest.mock import patch, mock_open, MagicMock
from app.theme.theme_manager import ThemeManager


class TestThemeManager:
    """Test suite for the ThemeManager class."""

    def test_default_theme_is_dark(self, theme_manager):
        assert theme_manager.current_theme == "dark"
        assert theme_manager.is_dark is True

    def test_set_theme_to_dark(self, theme_manager):
        theme_manager.set_theme("dark")
        assert theme_manager.current_theme == "dark"
        assert theme_manager.is_dark is True

    def test_set_theme_to_light(self, theme_manager):
        theme_manager.set_theme("dark")
        theme_manager.set_theme("light")
        assert theme_manager.current_theme == "light"
        assert theme_manager.is_dark is False

    def test_set_invalid_theme_raises(self, theme_manager):
        with pytest.raises(ValueError, match="Invalid theme"):
            theme_manager.set_theme("blue")

    def test_toggle_theme_switches_to_light(self, theme_manager):
        result = theme_manager.toggle_theme()
        assert result == "light"
        assert theme_manager.current_theme == "light"

    def test_toggle_theme_switches_back_to_dark(self, theme_manager):
        theme_manager.toggle_theme()
        result = theme_manager.toggle_theme()
        assert result == "dark"
        assert theme_manager.current_theme == "dark"

    def test_theme_changed_signal(self, theme_manager, qtbot):
        with qtbot.waitSignal(theme_manager.theme_changed, timeout=1000) as blocker:
            theme_manager.toggle_theme()
        assert blocker.args == ["light"]

    def test_set_same_theme_no_signal(self, theme_manager, qtbot):
        with qtbot.assertNotEmitted(theme_manager.theme_changed):
            theme_manager.set_theme("dark")

    def test_palette_contains_all_required_tokens(self, theme_manager):
        required_tokens = [
            "bg-primary", "bg-secondary", "text-primary", "text-secondary",
            "color-primary", "color-secondary", "color-accent", "border",
        ]
        for mode in ("light", "dark"):
            palette = ThemeManager.PALETTES[mode]
            for token in required_tokens:
                assert token in palette, f"Missing token '{token}' in {mode} palette"

    def test_palette_property_returns_current(self, theme_manager):
        dark_palette = theme_manager.palette
        assert dark_palette == ThemeManager.PALETTES["dark"]
        theme_manager.set_theme("light")
        light_palette = theme_manager.palette
        assert light_palette == ThemeManager.PALETTES["light"]


class TestThemeManagerStylesheet:
    """Test QSS stylesheet loading and token replacement."""

    def test_get_stylesheet_replaces_tokens(self):
        tm = ThemeManager()
        qss_template = "background: {{bg-primary}}; color: {{text-primary}};"
        m = mock_open(read_data=qss_template)
        with patch("builtins.open", m):
            with patch("app.theme.theme_manager.resource_path", return_value="/fake/dark.qss"):
                result = tm.get_stylesheet()
        assert "{{bg-primary}}" not in result
        assert "#1E1B2E" in result  # dark bg-primary
        assert "#F9FAFB" in result  # dark text-primary

    def test_get_stylesheet_dark_tokens(self):
        tm = ThemeManager()
        tm.set_theme("dark")
        qss_template = "background: {{bg-primary}};"
        m = mock_open(read_data=qss_template)
        with patch("builtins.open", m):
            with patch("app.theme.theme_manager.resource_path", return_value="/fake/dark.qss"):
                result = tm.get_stylesheet()
        assert "#1E1B2E" in result  # dark bg-primary

    def test_get_stylesheet_replaces_icons_path(self):
        tm = ThemeManager()
        qss_template = "url({{icons-path}}/arrow.svg);"
        m = mock_open(read_data=qss_template)
        with patch("builtins.open", m):
            with patch("app.theme.theme_manager.resource_path") as mock_rp:
                mock_rp.side_effect = lambda p: f"/resolved/{p}"
                result = tm.get_stylesheet()
        assert "{{icons-path}}" not in result
        assert "/resolved/" in result

    def test_get_stylesheet_file_not_found(self):
        tm = ThemeManager()
        with patch("builtins.open", side_effect=FileNotFoundError):
            with patch("app.theme.theme_manager.resource_path", return_value="/missing.qss"):
                result = tm.get_stylesheet()
        assert result == ""

    def test_get_stylesheet_all_palette_tokens_replaced(self):
        tm = ThemeManager()
        # Build a QSS with ALL palette tokens
        palette = ThemeManager.PALETTES["light"]
        qss_template = " ".join(f"{{{{{token}}}}}" for token in palette.keys())
        qss_template += " {{icons-path}}"
        m = mock_open(read_data=qss_template)
        with patch("builtins.open", m):
            with patch("app.theme.theme_manager.resource_path", return_value="/fake.qss"):
                result = tm.get_stylesheet()
        # No double-brace tokens should remain
        assert "{{" not in result
        assert "}}" not in result
