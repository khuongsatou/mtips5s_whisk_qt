"""
Tests for LogPanel — collapsible log area with colored log levels.
"""
import pytest
import logging
from app.widgets.log_panel import LogPanel, LogSignalBridge, QtLogHandler, LEVEL_COLORS


class TestLogSignalBridge:
    """Test the signal bridge object."""

    def test_bridge_has_signal(self, qtbot):
        bridge = LogSignalBridge()
        qtbot.addWidget(bridge) if hasattr(bridge, 'show') else None
        assert hasattr(bridge, 'log_message')

    def test_bridge_emits_signal(self, qtbot):
        bridge = LogSignalBridge()
        with qtbot.waitSignal(bridge.log_message, timeout=500):
            bridge.log_message.emit("hello", "INFO")


class TestQtLogHandler:
    """Test the custom logging handler."""

    def test_handler_emits_via_bridge(self, qtbot):
        bridge = LogSignalBridge()
        handler = QtLogHandler(bridge)
        handler.setFormatter(logging.Formatter("%(message)s"))

        with qtbot.waitSignal(bridge.log_message, timeout=500) as blocker:
            record = logging.LogRecord(
                name="test", level=logging.INFO, pathname="",
                lineno=0, msg="test message", args=(), exc_info=None
            )
            handler.emit(record)
        assert "test message" in blocker.args[0]
        assert blocker.args[1] == "INFO"


class TestLevelColors:
    """Test level color constants."""

    def test_debug_color_exists(self):
        assert "DEBUG" in LEVEL_COLORS

    def test_info_color_exists(self):
        assert "INFO" in LEVEL_COLORS

    def test_warning_color_exists(self):
        assert "WARNING" in LEVEL_COLORS

    def test_error_color_exists(self):
        assert "ERROR" in LEVEL_COLORS

    def test_critical_color_exists(self):
        assert "CRITICAL" in LEVEL_COLORS

    def test_all_colors_are_hex(self):
        for color in LEVEL_COLORS.values():
            assert color.startswith("#")
            assert len(color) == 7


class TestLogPanel:
    """Test the LogPanel widget."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        self.panel = LogPanel()
        qtbot.addWidget(self.panel)

    def test_object_name(self):
        assert self.panel.objectName() == "log_panel"

    def test_log_area_is_readonly(self):
        assert self.panel._log_area.isReadOnly()

    def test_initial_not_collapsed(self):
        assert self.panel._collapsed is False

    def test_toggle_collapses(self):
        self.panel._on_toggle()
        assert self.panel._collapsed is True
        assert not self.panel._log_area.isVisible()
        assert self.panel._toggle_btn.text() == "▲"

    def test_toggle_expands(self):
        self.panel._on_toggle()  # collapse
        self.panel._on_toggle()  # expand
        assert self.panel._collapsed is False
        assert self.panel._toggle_btn.text() == "▼"

    def test_clear_log(self):
        self.panel._append_log("some log line", "INFO")
        self.panel._on_clear()
        assert self.panel._log_area.toPlainText() == ""

    def test_append_log_adds_text(self):
        self.panel._append_log("hello world", "DEBUG")
        assert "hello world" in self.panel._log_area.toHtml()
