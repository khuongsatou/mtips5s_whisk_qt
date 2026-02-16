"""
Whisk Desktop — Status Badge Widget.
"""
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt


class StatusBadge(QLabel):
    """Colored badge for displaying status values."""

    STATUS_OBJECT_NAMES = {
        "completed": "badge_completed",
        "in_progress": "badge_in_progress",
        "pending": "badge_pending",
    }

    def __init__(self, status: str, translator=None, parent=None):
        super().__init__(parent)
        self.translator = translator
        self._status = status
        self.setAlignment(Qt.AlignCenter)
        self._update_display()

    def _update_display(self):
        """Update badge text and object name based on status."""
        obj_name = self.STATUS_OBJECT_NAMES.get(self._status, "badge_pending")
        self.setObjectName(obj_name)

        if self.translator:
            text = self.translator.t(f"status.{self._status}")
        else:
            text = self._status.replace("_", " ").title()
        self.setText(text)

    def set_status(self, status: str):
        """Change the status displayed."""
        self._status = status
        self._update_display()
        self.style().unpolish(self)
        self.style().polish(self)
