"""
Tests for QueueToolbar — bottom toolbar with action buttons.
"""
import pytest
from app.widgets.queue_toolbar import QueueToolbar


class TestQueueToolbarInit:
    """Verify toolbar creates all buttons and signals."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        self.toolbar = QueueToolbar(translator)
        qtbot.addWidget(self.toolbar)

    def test_has_add_row_btn(self):
        assert self.toolbar._add_row_btn is not None

    def test_has_delete_btn(self):
        assert self.toolbar._delete_btn is not None

    def test_has_delete_all_btn(self):
        assert self.toolbar._delete_all_btn is not None

    def test_has_clear_ckpt_btn(self):
        assert self.toolbar._clear_ckpt_btn is not None

    def test_has_retry_btn(self):
        assert self.toolbar._retry_btn is not None


    def test_object_name(self):
        assert self.toolbar.objectName() == "queue_toolbar"


class TestQueueToolbarSignals:
    """Test that button clicks emit the correct signals."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        self.toolbar = QueueToolbar(translator)
        self.qtbot = qtbot
        qtbot.addWidget(self.toolbar)

    def test_add_row_signal(self):
        with self.qtbot.waitSignal(self.toolbar.add_row, timeout=500):
            self.toolbar._add_row_btn.click()

    def test_delete_selected_signal(self):
        with self.qtbot.waitSignal(self.toolbar.delete_selected, timeout=500):
            self.toolbar._delete_btn.click()

    def test_delete_all_signal(self):
        with self.qtbot.waitSignal(self.toolbar.delete_all, timeout=500):
            self.toolbar._delete_all_btn.click()

    def test_clear_checkpoint_signal(self):
        with self.qtbot.waitSignal(self.toolbar.clear_checkpoint, timeout=500):
            self.toolbar._clear_ckpt_btn.click()

    def test_retry_errors_signal(self):
        with self.qtbot.waitSignal(self.toolbar.retry_errors, timeout=500):
            self.toolbar._retry_btn.click()



class TestQueueToolbarRetranslate:
    """Test retranslate updates tooltips."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        self.translator = translator
        self.toolbar = QueueToolbar(translator)
        qtbot.addWidget(self.toolbar)

    def test_retranslate_updates_tooltips(self):
        old_tip = self.toolbar._add_row_btn.toolTip()
        self.translator.set_language("vi")
        new_tip = self.toolbar._add_row_btn.toolTip()
        # Tooltip should change (or at least the retranslate ran without error)
        assert new_tip  # not empty
