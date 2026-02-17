"""
Tests for CookieManagerDialog — init, load, add, refresh, delete, status display.
"""
import pytest
from unittest.mock import MagicMock, patch
from app.widgets.cookie_manager_dialog import CookieManagerDialog


@pytest.fixture
def cookie_api():
    api = MagicMock()
    api.get_api_keys.return_value = MagicMock(
        success=True,
        data={
            "items": [
                {
                    "id": 101,
                    "label": "Cookie A",
                    "status": "active",
                    "expired": "2026-12-31T23:59:59",
                    "requests": 5,
                    "metadata": {"user_email": "a@test.com"},
                    "provider": "whisk",
                    "error": False,
                    "msg_error": "",
                },
                {
                    "id": 102,
                    "label": "",
                    "status": "expired",
                    "expired": "2024-01-01T00:00:00",
                    "requests": 0,
                    "metadata": {"user_email": "b@test.com"},
                    "provider": "whisk",
                    "error": False,
                    "msg_error": "",
                },
                {
                    "id": 103,
                    "label": "",
                    "status": "unknown",
                    "expired": None,
                    "requests": 0,
                    "metadata": {},
                    "provider": "whisk",
                    "error": True,
                    "msg_error": "Token revoked",
                },
            ],
            "total": 3,
        },
    )
    api.test_cookie.return_value = MagicMock(
        success=True, data={"provider_info": {"user_email": "new@test.com"}}
    )
    api.save_cookie.return_value = MagicMock(
        success=True,
        data={"api_key": {"id": 999}},
        message="saved",
    )
    api.assign_api_key_to_flow.return_value = MagicMock(success=True)
    api.refresh_api_key.return_value = MagicMock(success=True)
    api.delete_api_key.return_value = MagicMock(success=True)
    return api


class TestCookieManagerDialogInit:
    """Test dialog construction."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator, mock_api, cookie_api):
        self.dialog = CookieManagerDialog(
            mock_api, translator, cookie_api=cookie_api, active_flow_id=135
        )
        qtbot.addWidget(self.dialog)

    def test_window_title(self):
        assert self.dialog.windowTitle()

    def test_modal(self):
        assert self.dialog.isModal()

    def test_has_value_input(self):
        assert self.dialog._value_input is not None

    def test_has_add_button(self):
        assert self.dialog._add_btn is not None

    def test_has_table(self):
        assert self.dialog._table is not None

    def test_has_close_btn(self):
        assert self.dialog._close_btn is not None


class TestCookieManagerDialogLoad:
    """Test cookie loading and table population."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator, mock_api, cookie_api):
        self.cookie_api = cookie_api
        self.dialog = CookieManagerDialog(
            mock_api, translator, cookie_api=cookie_api, active_flow_id=135
        )
        qtbot.addWidget(self.dialog)

    def test_table_row_count(self):
        assert self.dialog._table.rowCount() == 3

    def test_count_label(self):
        assert "3" in self.dialog._count_label.text()

    def test_name_column_with_label(self):
        # Cookie A has a label
        assert self.dialog._table.item(0, 0).text() == "Cookie A"

    def test_name_column_fallback_to_email(self):
        # Cookie B has no label but has email
        assert "b@test.com" in self.dialog._table.item(1, 0).text()

    def test_status_badge_active(self):
        widget = self.dialog._table.cellWidget(0, 1)
        assert widget is not None

    def test_status_badge_error(self):
        widget = self.dialog._table.cellWidget(2, 1)
        assert widget is not None

    def test_expires_column_with_date(self):
        exp_text = self.dialog._table.item(0, 2).text()
        assert "2026" in exp_text

    def test_expires_column_none(self):
        exp_text = self.dialog._table.item(2, 2).text()
        assert exp_text == "—"

    def test_action_widgets_present(self):
        for row in range(3):
            widget = self.dialog._table.cellWidget(row, 5)
            assert widget is not None


class TestCookieManagerDialogLoadFallback:
    """Test cookie loading fallback scenarios."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator, mock_api):
        self.mock_api = mock_api
        self.translator = translator
        self.qtbot = qtbot

    def test_load_from_mock_when_no_cookie_api(self):
        """Falls back to mock api when no cookie_api provided."""
        dialog = CookieManagerDialog(self.mock_api, self.translator)
        self.qtbot.addWidget(dialog)
        # Should not crash, loads from mock_api.get_cookies()

    def test_load_from_mock_when_no_flow_id(self):
        """Falls back to mock api when no active_flow_id."""
        cookie_api = MagicMock()
        dialog = CookieManagerDialog(
            self.mock_api, self.translator, cookie_api=cookie_api, active_flow_id=None
        )
        self.qtbot.addWidget(dialog)

    def test_load_fallback_when_api_fails(self):
        """Falls back to mock when cookie API returns failure."""
        cookie_api = MagicMock()
        cookie_api.get_api_keys.return_value = MagicMock(
            success=False, data=None, message="API error"
        )
        dialog = CookieManagerDialog(
            self.mock_api, self.translator, cookie_api=cookie_api, active_flow_id=1
        )
        self.qtbot.addWidget(dialog)


class TestCookieManagerDialogAdd:
    """Test add cookie flow."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator, mock_api, cookie_api):
        self.cookie_api = cookie_api
        self.dialog = CookieManagerDialog(
            mock_api, translator, cookie_api=cookie_api, active_flow_id=135
        )
        qtbot.addWidget(self.dialog)

    def test_add_empty_value_does_nothing(self):
        self.dialog._value_input.setPlainText("")
        self.dialog._on_add_cookie()
        self.cookie_api.test_cookie.assert_not_called()

    def test_add_no_api_shows_error(self):
        self.dialog.cookie_api = None
        self.dialog._value_input.setPlainText("some-cookie-value")
        self.dialog._on_add_cookie()
        assert "⚠️" in self.dialog._status_label.text()

    def test_add_no_flow_id_shows_error(self):
        self.dialog._active_flow_id = None
        self.dialog._value_input.setPlainText("some-cookie-value")
        self.dialog._on_add_cookie()
        assert "⚠️" in self.dialog._status_label.text()

    def test_add_cookie_success(self):
        signals = []
        self.dialog.cookies_changed.connect(lambda: signals.append(True))
        self.dialog._value_input.setPlainText("valid-cookie-token")
        self.dialog._on_add_cookie()
        self.cookie_api.test_cookie.assert_called_once()
        self.cookie_api.save_cookie.assert_called_once()
        self.cookie_api.assign_api_key_to_flow.assert_called_once()
        assert "✅" in self.dialog._status_label.text()
        assert self.dialog._value_input.toPlainText() == ""  # cleared
        assert len(signals) == 1

    def test_add_cookie_test_fails(self):
        self.cookie_api.test_cookie.return_value = MagicMock(
            success=False, message="Cookie invalid"
        )
        self.dialog._value_input.setPlainText("bad-cookie")
        self.dialog._on_add_cookie()
        assert "❌" in self.dialog._status_label.text()
        self.cookie_api.save_cookie.assert_not_called()

    def test_add_cookie_save_fails(self):
        self.cookie_api.save_cookie.return_value = MagicMock(
            success=False, message="Save error"
        )
        self.dialog._value_input.setPlainText("cookie-val")
        self.dialog._on_add_cookie()
        assert "❌" in self.dialog._status_label.text()

    def test_add_cookie_exception(self):
        self.cookie_api.test_cookie.side_effect = RuntimeError("network")
        self.dialog._value_input.setPlainText("cookie-val")
        self.dialog._on_add_cookie()
        assert "❌" in self.dialog._status_label.text()
        # Button should be re-enabled
        assert self.dialog._add_btn.isEnabled()


class TestCookieManagerDialogRefresh:
    """Test refresh individual cookie."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator, mock_api, cookie_api):
        self.cookie_api = cookie_api
        self.dialog = CookieManagerDialog(
            mock_api, translator, cookie_api=cookie_api, active_flow_id=135
        )
        qtbot.addWidget(self.dialog)

    def test_refresh_cookie_calls_api(self):
        from PySide6.QtWidgets import QPushButton
        btn = QPushButton("🔄")
        self.dialog._on_refresh_cookie("101", btn)
        self.cookie_api.refresh_api_key.assert_called_once_with(101)
        assert btn.isEnabled()

    def test_refresh_cookie_no_api(self):
        from PySide6.QtWidgets import QPushButton
        self.dialog.cookie_api = None
        btn = QPushButton("🔄")
        self.dialog._on_refresh_cookie("101", btn)
        # Should not crash

    def test_refresh_cookie_api_failure(self):
        from PySide6.QtWidgets import QPushButton
        self.cookie_api.refresh_api_key.return_value = MagicMock(
            success=False, message="fail"
        )
        btn = QPushButton("🔄")
        self.dialog._on_refresh_cookie("101", btn)
        assert btn.isEnabled()

    def test_refresh_cookie_exception(self):
        from PySide6.QtWidgets import QPushButton
        self.cookie_api.refresh_api_key.side_effect = RuntimeError("error")
        btn = QPushButton("🔄")
        self.dialog._on_refresh_cookie("101", btn)
        assert btn.isEnabled()


class TestCookieManagerDialogDelete:
    """Test delete cookie."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator, mock_api, cookie_api):
        self.cookie_api = cookie_api
        self.mock_api = mock_api
        self.dialog = CookieManagerDialog(
            mock_api, translator, cookie_api=cookie_api, active_flow_id=135
        )
        qtbot.addWidget(self.dialog)

    def test_delete_cookie_calls_api(self):
        signals = []
        self.dialog.cookies_changed.connect(lambda: signals.append(True))
        self.dialog._on_delete_cookie("101")
        self.cookie_api.delete_api_key.assert_called_once_with(101)
        assert len(signals) == 1

    def test_delete_cookie_invalid_id(self):
        self.dialog._on_delete_cookie("not-a-number")
        # Should handle gracefully, fall through to warning

    def test_delete_cookie_no_api_uses_mock(self, qtbot, translator, cookie_api):
        mock_fallback = MagicMock()
        mock_fallback.get_cookies.return_value = MagicMock(success=True, data=[])
        dialog = CookieManagerDialog(mock_fallback, translator, cookie_api=cookie_api, active_flow_id=135)
        qtbot.addWidget(dialog)
        dialog.cookie_api = None
        dialog._on_delete_cookie("some-id")
        mock_fallback.delete_cookie.assert_called_once_with("some-id")


class TestCookieManagerDialogStatus:
    """Test status message display."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator, mock_api, cookie_api):
        self.dialog = CookieManagerDialog(
            mock_api, translator, cookie_api=cookie_api
        )
        qtbot.addWidget(self.dialog)

    def test_show_status_info(self):
        self.dialog._show_status("OK")
        assert self.dialog._status_label.text() == "OK"

    def test_show_status_error(self):
        self.dialog._show_status("Error!", error=True)
        assert "Error!" in self.dialog._status_label.text()
