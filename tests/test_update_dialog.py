"""Tests for app.widgets.update_dialog module."""
import pytest
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QCoreApplication


class TestUpdateSignals:
    """Tests for _UpdateSignals class."""

    def test_signal_exists(self, qapp):
        from app.widgets.update_dialog import _UpdateSignals
        signals = _UpdateSignals()
        assert hasattr(signals, "result")


class TestUpdateDialog:
    """Tests for UpdateDialog class."""

    @pytest.fixture
    def translator(self):
        t = MagicMock()
        t.t = MagicMock(side_effect=lambda k: k)
        return t

    @pytest.fixture
    def dialog(self, qapp, translator):
        with patch("app.widgets.update_dialog.check_for_update", return_value={}), \
             patch("threading.Thread") as mock_thread:
            mock_thread.return_value.start = MagicMock()
            from app.widgets.update_dialog import UpdateDialog
            d = UpdateDialog(translator)
            yield d
            d.close()

    def test_init(self, dialog):
        assert dialog.windowTitle() == "update.title"
        assert dialog._download_url == ""

    def test_on_result_error(self, dialog):
        dialog._on_result({"error": "Network error"})
        assert "❌" in dialog._status_label.text()

    def test_on_result_no_update(self, dialog):
        dialog._on_result({
            "latest_version": "1.0.0",
            "has_update": False,
        })
        assert "✅" in dialog._status_label.text()
        assert dialog._download_btn.isVisible() is False

    def test_on_result_has_update(self, dialog):
        dialog._on_result({
            "latest_version": "2.0.0",
            "has_update": True,
            "download_url": "https://example.com/v2.dmg",
            "file_name": "whisk-2.0.0.dmg",
            "changelog": [],
        })
        assert "🎉" in dialog._status_label.text()
        assert "whisk-2.0.0.dmg" in dialog._status_label.text()
        # Note: isVisible() is False when dialog is not shown, so we
        # just check the download_url was set and button intends to show
        assert dialog._download_url == "https://example.com/v2.dmg"

    def test_on_result_with_changelog(self, dialog):
        dialog._on_result({
            "latest_version": "2.0.0",
            "has_update": True,
            "download_url": "",
            "changelog": [
                {"version": "2.0.0", "date": "2026-01-01", "changes": ["New feature", "Bug fix"]},
            ],
        })
        text = dialog._changelog_text.toPlainText()
        assert "v2.0.0" in text
        assert "New feature" in text
        assert "Bug fix" in text

    def test_on_download_no_url(self, dialog):
        dialog._download_url = ""
        # Should not crash
        with patch("app.widgets.update_dialog.QDesktopServices.openUrl") as mock_open:
            dialog._on_download()
            mock_open.assert_not_called()

    def test_on_download_with_url(self, dialog):
        dialog._download_url = "https://example.com/download"
        with patch("app.widgets.update_dialog.QDesktopServices.openUrl") as mock_open:
            dialog._on_download()
            mock_open.assert_called_once()

    def test_version_card_static(self, qapp):
        from app.widgets.update_dialog import UpdateDialog
        card = UpdateDialog._version_card("Current", "1.0.0", "#6B7280")
        assert card is not None
