"""
Tests for StyledMessageBox — custom dialog replacement for QMessageBox.
"""
import pytest
from PySide6.QtCore import Qt
from app.widgets.styled_message_box import StyledMessageBox


class TestStyledMessageBoxInit:
    """Test construction for each dialog type."""

    def test_info_type(self, qtbot):
        dlg = StyledMessageBox(StyledMessageBox.INFO, "Title", "Msg")
        qtbot.addWidget(dlg)
        assert dlg.windowTitle() == "Title"
        assert dlg._result is False

    def test_warning_type(self, qtbot):
        dlg = StyledMessageBox(StyledMessageBox.WARNING, "Warn", "Oops")
        qtbot.addWidget(dlg)
        assert dlg.windowTitle() == "Warn"

    def test_error_type(self, qtbot):
        dlg = StyledMessageBox(StyledMessageBox.ERROR, "Err", "Bad")
        qtbot.addWidget(dlg)
        assert dlg.windowTitle() == "Err"

    def test_question_type(self, qtbot):
        dlg = StyledMessageBox(StyledMessageBox.QUESTION, "Q?", "Sure?",
                               confirm_text="Yes", cancel_text="No")
        qtbot.addWidget(dlg)
        assert dlg.windowTitle() == "Q?"

    def test_minimum_width(self, qtbot):
        dlg = StyledMessageBox(StyledMessageBox.INFO, "T", "M")
        qtbot.addWidget(dlg)
        assert dlg.minimumWidth() >= 380

    def test_maximum_width(self, qtbot):
        dlg = StyledMessageBox(StyledMessageBox.INFO, "T", "M")
        qtbot.addWidget(dlg)
        assert dlg.maximumWidth() <= 500

    def test_modal(self, qtbot):
        dlg = StyledMessageBox(StyledMessageBox.INFO, "T", "M")
        qtbot.addWidget(dlg)
        assert dlg.isModal()


class TestStyledMessageBoxActions:
    """Test confirm/cancel behavior."""

    def test_confirm_sets_result_true(self, qtbot):
        dlg = StyledMessageBox(StyledMessageBox.INFO, "T", "M")
        qtbot.addWidget(dlg)
        dlg._on_confirm()
        assert dlg.confirmed is True

    def test_cancel_sets_result_false(self, qtbot):
        dlg = StyledMessageBox(StyledMessageBox.QUESTION, "T", "M",
                               cancel_text="No")
        qtbot.addWidget(dlg)
        dlg._on_cancel()
        assert dlg.confirmed is False

    def test_default_result_is_false(self, qtbot):
        dlg = StyledMessageBox(StyledMessageBox.INFO, "T", "M")
        qtbot.addWidget(dlg)
        assert dlg.confirmed is False


class TestStyledMessageBoxDarken:
    """Test the _darken static method."""

    def test_darken_white(self):
        result = StyledMessageBox._darken("#ffffff", 25)
        assert result == "#e6e6e6"

    def test_darken_black_stays_black(self):
        result = StyledMessageBox._darken("#000000", 25)
        assert result == "#000000"

    def test_darken_custom_amount(self):
        result = StyledMessageBox._darken("#646464", 100)
        assert result == "#000000"

    def test_darken_partial(self):
        result = StyledMessageBox._darken("#323232", 10)
        # 50-10=40 = 0x28
        assert result == "#282828"
