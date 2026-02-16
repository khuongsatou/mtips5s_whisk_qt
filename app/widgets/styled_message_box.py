"""
Whisk Desktop — Styled Message Box.

A modern, beautifully designed replacement for QMessageBox. Provides
confirm / info / warning / error dialogs with consistent styling.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget,
    QGraphicsDropShadowEffect,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


class StyledMessageBox(QDialog):
    """Modern styled message box with icon, title, message and action buttons."""

    # Dialog types
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    QUESTION = "question"

    # Icons per type
    _ICONS = {
        "info": "ℹ️",
        "warning": "⚠️",
        "error": "❌",
        "question": "❓",
    }

    # Accent colors per type
    _COLORS = {
        "info": "#7C3AED",       # Primary purple
        "warning": "#F59E0B",    # Amber
        "error": "#EF4444",      # Red
        "question": "#7C3AED",   # Primary purple
    }

    def __init__(self, dialog_type: str, title: str, message: str,
                 confirm_text: str = "OK", cancel_text: str = "",
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self._result = False

        accent = self._COLORS.get(dialog_type, "#7C3AED")
        icon_text = self._ICONS.get(dialog_type, "ℹ️")

        # Outer layout (for shadow spacing)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)

        # Card container
        card = QWidget()
        card.setObjectName("styled_msg_card")
        card.setStyleSheet(f"""
            QWidget#styled_msg_card {{
                background: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
            }}
        """)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 60))
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 28, 28, 24)
        card_layout.setSpacing(16)

        # Colored accent stripe at top
        stripe = QWidget()
        stripe.setFixedHeight(4)
        stripe.setStyleSheet(f"background: {accent}; border-radius: 2px;")
        card_layout.addWidget(stripe)

        # Icon + Title row
        header = QHBoxLayout()
        header.setSpacing(12)

        icon_label = QLabel(icon_text)
        icon_label.setStyleSheet("font-size: 28px; background: transparent;")
        icon_label.setFixedSize(40, 40)
        icon_label.setAlignment(Qt.AlignCenter)
        header.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 700;
            color: #1F2937;
            background: transparent;
        """)
        title_label.setWordWrap(True)
        header.addWidget(title_label, 1)
        card_layout.addLayout(header)

        # Message body
        msg_label = QLabel(message)
        msg_label.setStyleSheet("""
            font-size: 14px;
            color: #6B7280;
            line-height: 1.5;
            background: transparent;
            padding: 0 4px;
        """)
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        card_layout.addWidget(msg_label)

        # Spacer
        card_layout.addSpacing(8)

        # Button row
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        if cancel_text:
            cancel_btn = QPushButton(cancel_text)
            cancel_btn.setCursor(Qt.PointingHandCursor)
            cancel_btn.setFixedHeight(38)
            cancel_btn.setMinimumWidth(100)
            cancel_btn.setStyleSheet("""
                QPushButton {
                    background: #F3F4F6;
                    color: #374151;
                    border: 1px solid #D1D5DB;
                    border-radius: 10px;
                    font-size: 13px;
                    font-weight: 600;
                    padding: 0 20px;
                }
                QPushButton:hover {
                    background: #E5E7EB;
                    border-color: #9CA3AF;
                }
                QPushButton:pressed {
                    background: #D1D5DB;
                }
            """)
            cancel_btn.clicked.connect(self._on_cancel)
            btn_layout.addWidget(cancel_btn)

        confirm_btn = QPushButton(confirm_text)
        confirm_btn.setCursor(Qt.PointingHandCursor)
        confirm_btn.setFixedHeight(38)
        confirm_btn.setMinimumWidth(100)
        confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background: {accent};
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 600;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background: {self._darken(accent)};
            }}
            QPushButton:pressed {{
                background: {self._darken(accent, 40)};
            }}
        """)
        confirm_btn.clicked.connect(self._on_confirm)
        confirm_btn.setDefault(True)
        btn_layout.addWidget(confirm_btn)

        card_layout.addLayout(btn_layout)
        outer.addWidget(card)

        self.setMinimumWidth(380)
        self.setMaximumWidth(500)

    def _on_confirm(self):
        self._result = True
        self.accept()

    def _on_cancel(self):
        self._result = False
        self.reject()

    @property
    def confirmed(self) -> bool:
        return self._result

    @staticmethod
    def _darken(hex_color: str, amount: int = 25) -> str:
        """Darken a hex color by the given amount."""
        color = QColor(hex_color)
        return QColor(
            max(color.red() - amount, 0),
            max(color.green() - amount, 0),
            max(color.blue() - amount, 0),
        ).name()

    # --- Convenience static methods ---

    @staticmethod
    def information(parent, title: str, message: str):
        """Show an info dialog."""
        dlg = StyledMessageBox(
            StyledMessageBox.INFO, title, message,
            confirm_text="OK", parent=parent,
        )
        dlg.exec()

    @staticmethod
    def warning(parent, title: str, message: str):
        """Show a warning dialog."""
        dlg = StyledMessageBox(
            StyledMessageBox.WARNING, title, message,
            confirm_text="OK", parent=parent,
        )
        dlg.exec()

    @staticmethod
    def error(parent, title: str, message: str):
        """Show an error dialog."""
        dlg = StyledMessageBox(
            StyledMessageBox.ERROR, title, message,
            confirm_text="OK", parent=parent,
        )
        dlg.exec()

    @staticmethod
    def question(parent, title: str, message: str,
                 confirm_text: str = "Yes", cancel_text: str = "No") -> bool:
        """Show a question dialog. Returns True if confirmed."""
        dlg = StyledMessageBox(
            StyledMessageBox.QUESTION, title, message,
            confirm_text=confirm_text, cancel_text=cancel_text,
            parent=parent,
        )
        dlg.exec()
        return dlg.confirmed
