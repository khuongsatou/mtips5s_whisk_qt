"""
Shared pytest fixtures for Whisk Desktop tests.
"""
import os

import pytest
from unittest.mock import MagicMock

# Force headless Qt in CI/sandbox environments before importing any Qt-based modules.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from app.theme.theme_manager import ThemeManager
from app.i18n.translator import Translator
from app.api.mock_api import MockApi


@pytest.fixture
def theme_manager():
    """Provide a fresh ThemeManager instance."""
    return ThemeManager()


@pytest.fixture
def translator():
    """Provide a fresh Translator instance (English default)."""
    return Translator()


@pytest.fixture
def mock_api():
    """Provide a fresh MockApi instance with empty queue (ignoring any checkpoint)."""
    api = MockApi()
    api._queue.clear()  # Ensure tests start with empty queue regardless of checkpoint
    # Allow call assertions in dialog tests while preserving real behavior.
    api.delete_cookie = MagicMock(wraps=api.delete_cookie)
    return api
