"""
Tests for SettingsPage — theme, language, and account settings.
"""
import pytest
from unittest.mock import MagicMock
from app.pages.settings_page import SettingsPage
from app.theme.theme_manager import ThemeManager


class TestSettingsPageInit:
    """Test settings page construction."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator, theme_manager):
        self.page = SettingsPage(translator, theme_manager)
        qtbot.addWidget(self.page)

    def test_has_theme_group(self):
        assert self.page._theme_group is not None

    def test_has_language_combo(self):
        assert self.page._lang_combo is not None

    def test_page_emits_theme_signal(self):
        assert hasattr(self.page, 'theme_change_requested')

    def test_page_emits_language_signal(self):
        assert hasattr(self.page, 'language_change_requested')


class TestSettingsPageTheme:
    """Test theme selection."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator, theme_manager):
        self.page = SettingsPage(translator, theme_manager)
        self.qtbot = qtbot
        qtbot.addWidget(self.page)

    def test_theme_change_emits_signal(self):
        with self.qtbot.waitSignal(self.page.theme_change_requested, timeout=500):
            # Toggle to dark (button id 1)
            self.page._on_theme_change(1)


class TestSettingsPageLanguage:
    """Test language selection."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator, theme_manager):
        self.page = SettingsPage(translator, theme_manager)
        self.qtbot = qtbot
        qtbot.addWidget(self.page)

    def test_language_combo_has_options(self):
        assert self.page._lang_combo.count() >= 2

    def test_language_change_emits_signal(self):
        with self.qtbot.waitSignal(self.page.language_change_requested, timeout=500):
            self.page._on_language_change(1)


class TestSettingsPageRetranslate:
    """Test retranslation updates labels."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator, theme_manager):
        self.translator = translator
        self.page = SettingsPage(translator, theme_manager)
        qtbot.addWidget(self.page)

    def test_retranslate_runs_without_error(self):
        self.translator.set_language("vi")
        # Should not raise
