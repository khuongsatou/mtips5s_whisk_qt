"""
Whisk Desktop — Animated Toggle Switch Widget.

A custom QCheckBox replacement with smooth sliding animation.
"""
from PySide6.QtWidgets import QCheckBox, QSizePolicy
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, Property, QSize, QRectF,
)
from PySide6.QtGui import QPainter, QColor, QPen


class ToggleSwitch(QCheckBox):
    """Animated toggle switch — a pill-shaped track with a sliding circle knob."""

    # Colors
    _TRACK_OFF = QColor("#C4C4C4")
    _TRACK_ON = QColor("#10B981")
    _KNOB_COLOR = QColor("#FFFFFF")

    # Dimensions
    _TRACK_W = 36
    _TRACK_H = 20
    _KNOB_R = 14  # knob diameter
    _KNOB_MARGIN = 3

    def __init__(self, label: str = "", parent=None):
        super().__init__(label, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)

        # Internal animated position  (0.0 = off, 1.0 = on)
        self._position = 0.0

        # Animation
        self._animation = QPropertyAnimation(self, b"switch_position")
        self._animation.setDuration(180)
        self._animation.setEasingCurve(QEasingCurve.InOutCubic)

        self.stateChanged.connect(self._on_state_changed)

    # ── Qt Property for animation ──
    def _get_position(self) -> float:
        return self._position

    def _set_position(self, pos: float):
        self._position = pos
        self.update()  # trigger repaint

    switch_position = Property(float, _get_position, _set_position)

    # ── Slots ──
    def _on_state_changed(self, state):
        self._animation.stop()
        self._animation.setStartValue(self._position)
        self._animation.setEndValue(1.0 if self.isChecked() else 0.0)
        self._animation.start()

    # ── Painting ──
    def sizeHint(self) -> QSize:
        text_width = self.fontMetrics().horizontalAdvance(self.text()) if self.text() else 0
        spacing = 6 if text_width else 0
        return QSize(self._TRACK_W + spacing + text_width + 4, max(self._TRACK_H + 4, 24))

    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # Track rect (vertically centered)
        y_offset = (self.height() - self._TRACK_H) / 2
        track_rect = QRectF(0, y_offset, self._TRACK_W, self._TRACK_H)

        # Interpolate track color
        off_r, off_g, off_b = self._TRACK_OFF.red(), self._TRACK_OFF.green(), self._TRACK_OFF.blue()
        on_r, on_g, on_b = self._TRACK_ON.red(), self._TRACK_ON.green(), self._TRACK_ON.blue()
        t = self._position
        track_color = QColor(
            int(off_r + (on_r - off_r) * t),
            int(off_g + (on_g - off_g) * t),
            int(off_b + (on_b - off_b) * t),
        )

        # Draw track
        p.setPen(Qt.NoPen)
        p.setBrush(track_color)
        p.drawRoundedRect(track_rect, self._TRACK_H / 2, self._TRACK_H / 2)

        # Knob position
        knob_x_min = self._KNOB_MARGIN
        knob_x_max = self._TRACK_W - self._KNOB_R - self._KNOB_MARGIN
        knob_x = knob_x_min + (knob_x_max - knob_x_min) * self._position
        knob_y = y_offset + (self._TRACK_H - self._KNOB_R) / 2

        # Draw knob shadow
        shadow_color = QColor(0, 0, 0, 30)
        p.setBrush(shadow_color)
        p.drawEllipse(QRectF(knob_x + 0.5, knob_y + 1, self._KNOB_R, self._KNOB_R))

        # Draw knob
        p.setBrush(self._KNOB_COLOR)
        p.drawEllipse(QRectF(knob_x, knob_y, self._KNOB_R, self._KNOB_R))

        # Draw text label (right of the track)
        if self.text():
            p.setPen(QPen(self.palette().text().color()))
            text_x = self._TRACK_W + 6
            text_rect = QRectF(text_x, 0, self.width() - text_x, self.height())
            p.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, self.text())

        p.end()

    def hitButton(self, pos):
        """Allow clicking anywhere on the widget."""
        return self.rect().contains(pos)

    def set_track_colors(self, off_color: str, on_color: str):
        """Override track colors (hex strings)."""
        self._TRACK_OFF = QColor(off_color)
        self._TRACK_ON = QColor(on_color)
        self.update()
