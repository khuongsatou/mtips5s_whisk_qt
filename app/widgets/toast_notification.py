"""
Whisk Desktop — Toast Notification Widget.

Lightweight, auto-dismissing notification that slides in from the top-right
corner of the parent window. Fades out after a configurable duration.
"""
from PySide6.QtWidgets import QLabel, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont


class ToastNotification(QLabel):
    """Non-blocking toast notification that auto-dismisses."""

    def __init__(self, parent=None, duration_ms: int = 4000):
        super().__init__(parent)
        self._duration_ms = duration_ms

        # Styling
        self.setAlignment(Qt.AlignCenter)
        self.setWordWrap(True)
        self.setFont(QFont("Segoe UI", 12))
        self.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            "stop:0 #10B981, stop:1 #059669);"
            "color: white;"
            "border-radius: 10px;"
            "padding: 12px 20px;"
            "font-weight: 600;"
        )
        self.setMinimumWidth(280)
        self.setMaximumWidth(400)

        # Opacity effect for fade-out
        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity)

        self.hide()

    def show_message(self, message: str, icon: str = "✅",
                     bg_start: str = "#10B981", bg_end: str = "#059669"):
        """Display the toast with given message and auto-dismiss."""
        self.setText(f"{icon}  {message}")
        self.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            f"stop:0 {bg_start}, stop:1 {bg_end});"
            "color: white;"
            "border-radius: 10px;"
            "padding: 12px 20px;"
            "font-weight: 600;"
        )
        self.adjustSize()
        self._position_toast()
        self._opacity.setOpacity(1.0)
        self.raise_()
        self.show()

        # Start dismiss timer
        QTimer.singleShot(self._duration_ms, self._fade_out)

    def _position_toast(self):
        """Position at top-center of parent widget."""
        if self.parent():
            parent_rect = self.parent().rect()
            x = (parent_rect.width() - self.width()) // 2
            self.move(x, 16)

    def _fade_out(self):
        """Animate opacity to 0 then hide."""
        self._anim = QPropertyAnimation(self._opacity, b"opacity")
        self._anim.setDuration(500)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.finished.connect(self.hide)
        self._anim.start()
