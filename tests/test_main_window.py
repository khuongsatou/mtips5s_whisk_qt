"""Tests for app.main_window module — unit tests with mocked dependencies."""
import json
import pytest
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QMainWindow


def _make_deps():
    """Create standard mocked dependencies for MainWindow."""
    theme_manager = MagicMock()
    theme_manager.current_theme = "dark"
    theme_manager.get_stylesheet.return_value = ""
    theme_manager.theme_changed = MagicMock()
    theme_manager.theme_changed.connect = MagicMock()

    translator = MagicMock()
    translator.t = MagicMock(side_effect=lambda k: k)
    translator.language_changed = MagicMock()
    translator.language_changed.connect = MagicMock()

    return {
        "theme_manager": theme_manager,
        "translator": translator,
        "api": MagicMock(),
        "auth_manager": MagicMock(),
        "flow_api": MagicMock(),
        "cookie_api": MagicMock(),
        "workflow_api": MagicMock(),
    }


def _patched_init(self, **kwargs):
    """Minimal __init__ that skips UI setup for testing."""
    QMainWindow.__init__(self)
    self.theme_manager = kwargs.get("theme_manager")
    self.translator = kwargs.get("translator")
    self.api = kwargs.get("api")
    self.auth_manager = kwargs.get("auth_manager")
    self.flow_api = kwargs.get("flow_api")
    self.cookie_api = kwargs.get("cookie_api")
    self.workflow_api = kwargs.get("workflow_api")
    self._captcha_bridge = None
    self._captcha_sidecar = None
    self._project_tabs = []
    self._current_page = "dashboard"
    # Mock UI components
    self._sidebar = MagicMock()
    self._header = MagicMock()
    self._tab_bar = MagicMock()
    self._tab_bar.active_index.return_value = -1
    self._tab_bar.all_tabs_data.return_value = []
    self._tab_stack = MagicMock()
    self._content_stack = MagicMock()
    self._dashboard = MagicMock()
    self._settings = MagicMock()
    self._settings_page = MagicMock()


class TestMainWindow:
    """Tests for MainWindow state management."""

    @pytest.fixture
    def window(self, qapp):
        with patch("app.main_window.MainWindow.__init__", _patched_init):
            from app.main_window import MainWindow
            w = MainWindow(**_make_deps())
            yield w
            w.close()

    def test_init_creates_window(self, window):
        assert window is not None
        assert window._project_tabs == []

    def test_page_titles(self, window):
        from app.main_window import MainWindow
        assert "dashboard" in MainWindow.PAGE_TITLES
        assert "image_creator" in MainWindow.PAGE_TITLES
        assert "settings" in MainWindow.PAGE_TITLES

    def test_get_active_flow_id_empty(self, window):
        result = window._get_active_flow_id()
        assert result is None

    def test_get_active_flow_id_with_tabs(self, window):
        window._project_tabs = [
            {"flow_id": "f1", "flow_name": "Flow 1"},
            {"flow_id": "f2", "flow_name": "Flow 2"},
        ]
        window._tab_bar.active_index.return_value = 1
        result = window._get_active_flow_id()
        assert result == "f2"

    def test_switch_page_dashboard(self, window):
        window._switch_page("dashboard")
        window._header.set_page_title.assert_called()
        window._tab_bar.setVisible.assert_called_with(False)
        window._tab_stack.setCurrentWidget.assert_called_with(window._dashboard)

    def test_switch_page_settings(self, window):
        window._switch_page("settings")
        window._header.set_page_title.assert_called()
        window._tab_stack.setCurrentWidget.assert_called_with(window._settings)

    def test_refresh_dashboard_no_tabs(self, window):
        window._project_tabs = []
        window._refresh_dashboard()
        window._dashboard.update_stats.assert_called_once_with([])

    def test_on_tab_close_empty(self, window):
        window._project_tabs = []
        window._on_tab_close(0)  # Should not crash

    def test_on_theme_toggle(self, window):
        with patch("app.preferences.save_preference"):
            window._on_theme_toggle()
            window.theme_manager.toggle_theme.assert_called_once()

    def test_on_theme_set(self, window):
        window._on_theme_set("light")
        window.theme_manager.set_theme.assert_called_with("light")

    def test_on_language_change(self, window):
        with patch("app.preferences.save_preference"):
            window._on_language_change("en")
            window.translator.set_language.assert_called_with("en")


class TestMainWindowSaveTabs:
    """Tests for tab save/load logic."""

    def test_save_tabs(self, qapp, tmp_path):
        tabs_file = str(tmp_path / "tabs.json")

        with patch("app.main_window.MainWindow.__init__", _patched_init), \
             patch("app.main_window.TABS_FILE", tabs_file):

            from app.main_window import MainWindow
            w = MainWindow(**_make_deps())

            w._tab_bar.active_index.return_value = 0
            w._tab_bar.all_tabs_data.return_value = [
                {"flow_id": "f1", "flow_name": "Flow 1"},
            ]
            w._save_tabs()

            with open(tabs_file, "r") as f:
                data = json.load(f)
            assert len(data["tabs"]) == 1
            assert data["tabs"][0]["flow_id"] == "f1"
            w.close()

    def test_save_tabs_multiple(self, qapp, tmp_path):
        tabs_file = str(tmp_path / "tabs.json")

        with patch("app.main_window.MainWindow.__init__", _patched_init), \
             patch("app.main_window.TABS_FILE", tabs_file):

            from app.main_window import MainWindow
            w = MainWindow(**_make_deps())

            w._tab_bar.active_index.return_value = 1
            w._tab_bar.all_tabs_data.return_value = [
                {"flow_id": "f1", "flow_name": "Flow 1"},
                {"flow_id": "f2", "flow_name": "Flow 2"},
            ]
            w._save_tabs()

            with open(tabs_file, "r") as f:
                data = json.load(f)
            assert len(data["tabs"]) == 2
            assert data["active_index"] == 1
            w.close()


class TestMainWindowCaptchaMode:
    """Tests for captcha mode switching logic."""

    def test_on_captcha_mode_change_extension(self, qapp):
        with patch("app.main_window.MainWindow.__init__", _patched_init):
            from app.main_window import MainWindow
            w = MainWindow(**_make_deps())

            w._start_captcha_bridge = MagicMock()
            w._stop_captcha_bridge = MagicMock()
            w._start_captcha_sidecar = MagicMock()
            w._stop_captcha_sidecar = MagicMock()

            w._on_captcha_mode_change("extension")
            w._stop_captcha_sidecar.assert_called_once()
            w._start_captcha_bridge.assert_called_once()
            w.close()

    def test_on_captcha_mode_change_puppeteer(self, qapp):
        with patch("app.main_window.MainWindow.__init__", _patched_init):
            from app.main_window import MainWindow
            w = MainWindow(**_make_deps())

            w._start_captcha_bridge = MagicMock()
            w._stop_captcha_bridge = MagicMock()
            w._start_captcha_sidecar = MagicMock()
            w._stop_captcha_sidecar = MagicMock()

            w._on_captcha_mode_change("puppeteer")
            w._stop_captcha_bridge.assert_called_once()
            w._start_captcha_sidecar.assert_called_once()
            w.close()
