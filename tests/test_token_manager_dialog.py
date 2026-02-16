"""
Tests for TokenManagerDialog — init, form, save, edit, delete, load.
"""
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta
from app.widgets.token_manager_dialog import TokenManagerDialog


class TestTokenManagerInit:
    """Test TokenManagerDialog initialization."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        self.api = MagicMock()
        self.api.get_tokens.return_value = MagicMock(
            success=True,
            data=[],
        )
        self.dialog = TokenManagerDialog(self.api, translator)
        qtbot.addWidget(self.dialog)

    def test_window_title(self):
        assert self.dialog.windowTitle()

    def test_modal(self):
        assert self.dialog.isModal()

    def test_has_table(self):
        assert self.dialog._table is not None
        assert self.dialog._table.columnCount() == 6

    def test_has_form_inputs(self):
        assert self.dialog._name_input is not None
        assert self.dialog._value_input is not None
        assert self.dialog._type_combo is not None
        assert self.dialog._expiry_spin is not None

    def test_has_action_buttons(self):
        assert self.dialog._save_btn is not None
        assert self.dialog._close_btn is not None
        assert self.dialog._cancel_edit_btn is not None

    def test_cancel_edit_btn_hidden(self):
        assert not self.dialog._cancel_edit_btn.isVisible()


class TestTokenManagerLoadTokens:
    """Test token table population."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        self.api = MagicMock()
        future_dt = (datetime.now() + timedelta(days=10)).isoformat()
        past_dt = (datetime.now() - timedelta(days=1)).isoformat()
        self.api.get_tokens.return_value = MagicMock(
            success=True,
            data=[
                {
                    "id": "t1", "name": "API Key", "value": "sk-12345678901234567890long",
                    "token_type": "bearer", "status": "active",
                    "expires_at": future_dt,
                },
                {
                    "id": "t2", "name": "OAuth", "value": "short",
                    "token_type": "oauth", "status": "expired",
                    "expires_at": past_dt,
                },
                {
                    "id": "t3", "name": "No Expiry", "value": "val",
                    "token_type": "api_key", "status": "revoked",
                    "expires_at": None,
                },
            ],
        )
        self.dialog = TokenManagerDialog(self.api, translator)
        qtbot.addWidget(self.dialog)

    def test_table_row_count(self):
        assert self.dialog._table.rowCount() == 3

    def test_count_label(self):
        assert "3" in self.dialog._count_label.text()

    def test_name_column(self):
        assert self.dialog._table.item(0, 0).text() == "API Key"

    def test_type_column(self):
        assert self.dialog._table.item(0, 1).text() == "Bearer"
        assert self.dialog._table.item(1, 1).text() == "OAuth"
        assert self.dialog._table.item(2, 1).text() == "API Key"

    def test_value_truncated(self):
        val_text = self.dialog._table.item(0, 2).text()
        assert val_text.endswith("...")
        assert len(val_text) <= 24

    def test_value_not_truncated_when_short(self):
        val_text = self.dialog._table.item(1, 2).text()
        assert val_text == "short"

    def test_status_badge_widgets(self):
        # Each status cell should have a cell widget
        for row in range(3):
            widget = self.dialog._table.cellWidget(row, 3)
            assert widget is not None

    def test_expires_column_future(self):
        exp_text = self.dialog._table.item(0, 4).text()
        assert "remaining" in exp_text

    def test_expires_column_past(self):
        exp_text = self.dialog._table.item(1, 4).text()
        # Should show date format for expired
        assert "-" in exp_text or "remaining" in exp_text

    def test_expires_column_none(self):
        exp_text = self.dialog._table.item(2, 4).text()
        # should show "no expiry" translation
        assert exp_text

    def test_action_widgets_present(self):
        for row in range(3):
            widget = self.dialog._table.cellWidget(row, 5)
            assert widget is not None


class TestTokenManagerSave:
    """Test save (create/update) operations."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        self.api = MagicMock()
        self.api.get_tokens.return_value = MagicMock(success=True, data=[])
        self.api.add_token.return_value = MagicMock(success=True, data={"id": "new"})
        self.api.update_token.return_value = MagicMock(success=True, data={"id": "x"})
        self.dialog = TokenManagerDialog(self.api, translator)
        qtbot.addWidget(self.dialog)

    def test_save_empty_name_does_nothing(self):
        self.dialog._name_input.setText("")
        self.dialog._on_save()
        self.api.add_token.assert_not_called()

    def test_save_creates_token(self):
        self.dialog._name_input.setText("New Token")
        self.dialog._value_input.setPlainText("secret-val")
        self.dialog._on_save()
        self.api.add_token.assert_called_once()
        call_data = self.api.add_token.call_args[0][0]
        assert call_data["name"] == "New Token"
        assert call_data["value"] == "secret-val"

    def test_save_clears_form_after_create(self):
        self.dialog._name_input.setText("Token")
        self.dialog._value_input.setPlainText("val")
        self.dialog._on_save()
        assert self.dialog._name_input.text() == ""
        assert self.dialog._value_input.toPlainText() == ""

    def test_save_with_expiry_days(self):
        self.dialog._name_input.setText("Token")
        self.dialog._expiry_spin.setValue(30)
        self.dialog._on_save()
        call_data = self.api.add_token.call_args[0][0]
        assert call_data["expires_at"] == 30

    def test_save_with_no_expiry(self):
        self.dialog._name_input.setText("Token")
        self.dialog._expiry_spin.setValue(0)
        self.dialog._on_save()
        call_data = self.api.add_token.call_args[0][0]
        assert call_data["expires_at"] is None

    def test_save_in_edit_mode(self):
        self.dialog._editing_id = "existing-id"
        self.dialog._name_input.setText("Updated")
        self.dialog._value_input.setPlainText("new-val")
        self.dialog._on_save()
        self.api.update_token.assert_called_once()
        assert self.api.update_token.call_args[0][0] == "existing-id"

    def test_save_emits_tokens_changed(self):
        signals = []
        self.dialog.tokens_changed.connect(lambda: signals.append(True))
        self.dialog._name_input.setText("T")
        self.dialog._on_save()
        assert len(signals) == 1


class TestTokenManagerEditAndDelete:
    """Test edit and delete operations."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        self.api = MagicMock()
        self.api.get_tokens.return_value = MagicMock(success=True, data=[])
        self.api.delete_token.return_value = MagicMock(success=True)
        self.dialog = TokenManagerDialog(self.api, translator)
        qtbot.addWidget(self.dialog)

    def test_on_edit_populates_form(self):
        tok = {
            "name": "Edit Me", "value": "secret",
            "token_type": "api_key", "expires_at": None,
        }
        self.dialog._on_edit("tok-1", tok)
        assert self.dialog._editing_id == "tok-1"
        assert self.dialog._name_input.text() == "Edit Me"
        assert self.dialog._value_input.toPlainText() == "secret"
        # cancel_edit_btn was set visible by _on_edit
        assert not self.dialog._cancel_edit_btn.isHidden()

    def test_on_edit_with_expiry(self):
        future_dt = (datetime.now() + timedelta(days=15)).isoformat()
        tok = {"name": "Exp", "value": "v", "token_type": "bearer", "expires_at": future_dt}
        self.dialog._on_edit("tok-2", tok)
        assert self.dialog._expiry_spin.value() > 0

    def test_on_edit_with_invalid_expiry(self):
        tok = {"name": "Bad", "value": "v", "token_type": "bearer", "expires_at": "invalid"}
        self.dialog._on_edit("tok-3", tok)
        assert self.dialog._expiry_spin.value() == 30  # fallback

    def test_on_cancel_edit_resets_form(self):
        self.dialog._editing_id = "x"
        self.dialog._name_input.setText("something")
        self.dialog._on_cancel_edit()
        assert self.dialog._editing_id is None
        assert self.dialog._name_input.text() == ""
        assert not self.dialog._cancel_edit_btn.isVisible()

    def test_on_delete(self):
        signals = []
        self.dialog.tokens_changed.connect(lambda: signals.append(True))
        self.dialog._on_delete("tok-1")
        self.api.delete_token.assert_called_once_with("tok-1")
        assert len(signals) == 1

    def test_on_delete_while_editing_same(self):
        self.dialog._editing_id = "tok-1"
        self.dialog._on_delete("tok-1")
        assert self.dialog._editing_id is None  # cancel edit called
