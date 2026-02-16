"""
Whisk Desktop — Log Panel Widget.

A read-only text area that captures Python logging output and displays it
in the UI with color-coded log levels.
"""
import logging
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Signal, QObject, Qt
from PySide6.QtGui import QTextCursor, QColor


class LogSignalBridge(QObject):
    """Thread-safe bridge: logging handler emits signal → UI slot."""
    log_message = Signal(str, str)  # (formatted_message, level_name)


class QtLogHandler(logging.Handler):
    """Custom logging handler that emits to a Qt signal."""

    def __init__(self, bridge: LogSignalBridge):
        super().__init__()
        self._bridge = bridge

    def emit(self, record):
        try:
            msg = self.format(record)
            self._bridge.log_message.emit(msg, record.levelname)
        except Exception:
            self.handleError(record)


# Level → color mapping
LEVEL_COLORS = {
    "DEBUG": "#9CA3AF",     # gray
    "INFO": "#60A5FA",      # blue
    "WARNING": "#FBBF24",   # amber
    "ERROR": "#F87171",     # red
    "CRITICAL": "#EF4444",  # bright red
}


class LogPanel(QWidget):
    """Collapsible log panel showing real-time app logs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("log_panel")
        self._setup_ui()
        self._install_handler()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header bar
        header = QHBoxLayout()
        header.setContentsMargins(8, 4, 8, 4)
        header.setSpacing(6)

        self._title = QLabel("📋 Logs")
        self._title.setObjectName("log_panel_title")
        header.addWidget(self._title)

        header.addStretch()

        self._clear_btn = QPushButton("🗑️ Clear")
        self._clear_btn.setObjectName("log_clear_btn")
        self._clear_btn.setCursor(Qt.PointingHandCursor)
        self._clear_btn.clicked.connect(self._on_clear)
        header.addWidget(self._clear_btn)

        self._toggle_btn = QPushButton("▼")
        self._toggle_btn.setObjectName("log_toggle_btn")
        self._toggle_btn.setCursor(Qt.PointingHandCursor)
        self._toggle_btn.setFixedWidth(28)
        self._toggle_btn.clicked.connect(self._on_toggle)
        header.addWidget(self._toggle_btn)

        header_widget = QWidget()
        header_widget.setObjectName("log_panel_header")
        header_widget.setLayout(header)
        layout.addWidget(header_widget)

        # Log text area
        self._log_area = QTextEdit()
        self._log_area.setObjectName("log_text_area")
        self._log_area.setReadOnly(True)
        self._log_area.setMinimumHeight(80)
        self._log_area.setMaximumHeight(200)
        layout.addWidget(self._log_area)

        self._collapsed = False

    def _install_handler(self):
        """Install our custom handler into the root 'whisk' logger."""
        self._bridge = LogSignalBridge()
        self._bridge.log_message.connect(self._append_log)

        self._handler = QtLogHandler(self._bridge)
        self._handler.setFormatter(
            logging.Formatter("%(asctime)s  %(message)s", datefmt="%H:%M:%S")
        )

        # Attach to root whisk logger
        logger = logging.getLogger("whisk")
        logger.addHandler(self._handler)

    def _append_log(self, message: str, level: str):
        """Append a colored log line to the text area."""
        color = LEVEL_COLORS.get(level, "#D1D5DB")
        html = f'<span style="color:{color}; font-family: monospace; font-size:11px;">{message}</span>'
        self._log_area.append(html)
        # Auto-scroll to bottom
        cursor = self._log_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        self._log_area.setTextCursor(cursor)

    def _on_clear(self):
        self._log_area.clear()

    def _on_toggle(self):
        self._collapsed = not self._collapsed
        self._log_area.setVisible(not self._collapsed)
        self._toggle_btn.setText("▲" if self._collapsed else "▼")
