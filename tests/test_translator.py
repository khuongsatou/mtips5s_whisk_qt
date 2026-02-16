"""
Tests for Translator (i18n system).
"""
import pytest
from app.i18n.translator import Translator


class TestTranslator:
    """Test suite for the Translator class."""

    def test_default_language_is_en(self, translator):
        """Initial language should be English."""
        assert translator.current_language == "en"

    def test_available_languages(self, translator):
        """Should support both English and Vietnamese."""
        assert "en" in translator.available_languages
        assert "vi" in translator.available_languages

    def test_translate_key_returns_correct_value(self, translator):
        """t() should return the English string for a known key."""
        result = translator.t("app.title")
        assert result == "Whisk Desktop"

    def test_translate_nav_key(self, translator):
        """Navigation keys should translate correctly."""
        assert translator.t("nav.image_creator") == "Image Creator"
        assert translator.t("nav.settings") == "Settings"

    def test_translate_config_key(self, translator):
        """Config panel keys should translate correctly."""
        assert translator.t("config.title") == "Config & Prompts"
        assert translator.t("config.model") == "Model"

    def test_missing_key_returns_key(self, translator):
        """t() with unknown key should return the key itself."""
        result = translator.t("nonexistent.key")
        assert result == "nonexistent.key"

    def test_set_language_to_vi(self, translator):
        """Switching to Vietnamese should update translations."""
        translator.set_language("vi")
        assert translator.current_language == "vi"
        assert translator.t("nav.image_creator") == "Tạo Ảnh"

    def test_set_language_back_to_en(self, translator):
        """Switching back to English should restore translations."""
        translator.set_language("vi")
        translator.set_language("en")
        assert translator.current_language == "en"
        assert translator.t("nav.image_creator") == "Image Creator"

    def test_set_invalid_language_raises(self, translator):
        """Setting unsupported language should raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported language"):
            translator.set_language("fr")

    def test_language_changed_signal(self, translator, qtbot):
        """language_changed signal should emit with new lang code."""
        with qtbot.waitSignal(translator.language_changed, timeout=1000) as blocker:
            translator.set_language("vi")
        assert blocker.args == ["vi"]

    def test_set_same_language_no_signal(self, translator, qtbot):
        """Setting the same language should not emit signal."""
        with qtbot.assertNotEmitted(translator.language_changed):
            translator.set_language("en")

    def test_vietnamese_translations_exist(self):
        """Vietnamese translations should load and have content."""
        tr = Translator(default_language="vi")
        assert tr.current_language == "vi"
        assert tr.t("nav.image_creator") == "Tạo Ảnh"
        assert tr.t("nav.settings") == "Cài đặt"
        assert tr.t("config.add_to_queue") == "Thêm vào hàng chờ"
