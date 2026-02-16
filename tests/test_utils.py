"""
Tests for utils.py — resource_path resolution in dev, PyInstaller, and .app modes.
"""
import os
import sys
import pytest
from unittest.mock import patch


class TestResourcePath:
    """Test resource_path() for all three resolution modes."""

    def test_dev_mode_returns_relative_path(self):
        from app.utils import resource_path
        result = resource_path("app/theme/light.qss")
        assert result.endswith("app/theme/light.qss")
        assert os.path.isabs(result)

    def test_pyinstaller_mode(self):
        with patch.object(sys, "_MEIPASS", "/tmp/pyinstaller_bundle", create=True):
            # Need to reimport to pick up the patched attribute
            from app.utils import resource_path
            result = resource_path("app/theme/light.qss")
        assert result == "/tmp/pyinstaller_bundle/app/theme/light.qss"

    def test_macos_app_bundle_mode(self):
        with patch.dict(os.environ, {"WHISK_RESOURCE_DIR": "/Applications/Whisk.app/Contents/Resources"}):
            # Ensure no _MEIPASS
            if hasattr(sys, "_MEIPASS"):
                delattr(sys, "_MEIPASS")
            from app.utils import resource_path
            result = resource_path("app/theme/dark.qss")
        assert result == "/Applications/Whisk.app/Contents/Resources/app/theme/dark.qss"
