"""
Whisk Desktop — Translator / i18n Manager.

Loads JSON translation files and provides translated strings via t(key).
Emits language_changed signal so widgets can refresh their text.
"""
import json
import os
from PySide6.QtCore import QObject, Signal
from app.utils import resource_path


class Translator(QObject):
    """Manages application internationalization (i18n)."""

    language_changed = Signal(str)  # Emits language code, e.g. "en" or "vi"

    SUPPORTED_LANGUAGES = ["en", "vi"]
    LANGUAGE_LABELS = {
        "en": "English",
        "vi": "Tiếng Việt",
    }

    def __init__(self, default_language: str = "en", parent=None):
        super().__init__(parent)
        self._current_language = default_language
        self._translations: dict[str, str] = {}
        self._load_translations(default_language)

    @property
    def current_language(self) -> str:
        """Return current language code."""
        return self._current_language

    @property
    def available_languages(self) -> list[str]:
        """Return list of supported language codes."""
        return list(self.SUPPORTED_LANGUAGES)

    def set_language(self, lang_code: str) -> None:
        """Switch to a different language.

        Args:
            lang_code: Language code (e.g. 'en', 'vi').

        Raises:
            ValueError: If lang_code is not in SUPPORTED_LANGUAGES.
        """
        if lang_code not in self.SUPPORTED_LANGUAGES:
            raise ValueError(
                f"Unsupported language: {lang_code}. "
                f"Supported: {self.SUPPORTED_LANGUAGES}"
            )
        if lang_code != self._current_language:
            self._current_language = lang_code
            self._load_translations(lang_code)
            self.language_changed.emit(lang_code)

    def t(self, key: str) -> str:
        """Translate a key to the current language.

        Args:
            key: Translation key (e.g. 'nav.dashboard').

        Returns:
            Translated string, or the key itself if not found.
        """
        return self._translations.get(key, key)

    def _load_translations(self, lang_code: str) -> None:
        """Load translation file for the given language.

        Args:
            lang_code: Language code to load.
        """
        json_path = resource_path(f"app/i18n/{lang_code}.json")
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                self._translations = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._translations = {}
