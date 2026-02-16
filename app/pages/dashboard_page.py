"""
Whisk Desktop — Dashboard Page.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea,
)
from PySide6.QtCore import Qt


class DashboardPage(QWidget):
    """Dashboard with welcome message and summary stat cards."""

    def __init__(self, translator, api, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.api = api
        self.translator.language_changed.connect(self.retranslate)
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        self._layout = QVBoxLayout(container)
        self._layout.setContentsMargins(24, 24, 24, 24)
        self._layout.setSpacing(20)

        # Welcome section
        self._welcome_title = QLabel(self.translator.t("dashboard.welcome"))
        self._welcome_title.setObjectName("welcome_title")
        self._layout.addWidget(self._welcome_title)

        self._welcome_desc = QLabel(self.translator.t("dashboard.welcome_desc"))
        self._welcome_desc.setObjectName("welcome_desc")
        self._welcome_desc.setWordWrap(True)
        self._layout.addWidget(self._welcome_desc)

        # Stat cards row
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)

        self._card_total = self._create_card(
            "0", self.translator.t("dashboard.total_items"), "card_primary"
        )
        cards_row.addWidget(self._card_total["frame"])

        self._card_completed = self._create_card(
            "0", self.translator.t("dashboard.completed"), "card_secondary"
        )
        cards_row.addWidget(self._card_completed["frame"])

        self._card_progress = self._create_card(
            "0", self.translator.t("dashboard.in_progress"), "card_accent"
        )
        cards_row.addWidget(self._card_progress["frame"])

        self._card_pending = self._create_card(
            "0", self.translator.t("dashboard.pending"), "card_danger"
        )
        cards_row.addWidget(self._card_pending["frame"])

        self._layout.addLayout(cards_row)

        # Recent activity section
        self._recent_title = QLabel(self.translator.t("dashboard.recent_activity"))
        self._recent_title.setObjectName("section_title")
        self._layout.addWidget(self._recent_title)

        # Recent items list
        self._recent_container = QVBoxLayout()
        self._recent_container.setSpacing(8)
        self._layout.addLayout(self._recent_container)

        self._layout.addStretch()

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _create_card(self, value: str, label: str, style_id: str) -> dict:
        """Create a stat card widget.

        Returns:
            Dict with 'frame', 'value_label', and 'text_label' references.
        """
        frame = QFrame()
        frame.setObjectName("stat_card")
        frame.setProperty("class", style_id)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(4)

        value_label = QLabel(value)
        value_label.setObjectName("card_value")
        layout.addWidget(value_label)

        text_label = QLabel(label)
        text_label.setObjectName("card_label")
        layout.addWidget(text_label)

        # Apply the specific card style via additional object name
        frame.setObjectName(style_id)

        return {"frame": frame, "value_label": value_label, "text_label": text_label}

    def refresh_data(self):
        """Fetch fresh data from API and update display."""
        response = self.api.get_items(page=1, per_page=100)
        if not response.success:
            return

        items = response.data or []
        total = len(items)
        completed = sum(1 for i in items if i.get("status") == "completed")
        in_progress = sum(1 for i in items if i.get("status") == "in_progress")
        pending = sum(1 for i in items if i.get("status") == "pending")

        self._card_total["value_label"].setText(str(total))
        self._card_completed["value_label"].setText(str(completed))
        self._card_progress["value_label"].setText(str(in_progress))
        self._card_pending["value_label"].setText(str(pending))

        # Clear and populate recent items
        while self._recent_container.count():
            child = self._recent_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for item in items[:5]:
            row = QFrame()
            row.setObjectName("stat_card")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(12, 8, 12, 8)

            name_lbl = QLabel(item.get("name", ""))
            name_lbl.setStyleSheet("font-weight: bold;")
            row_layout.addWidget(name_lbl)

            row_layout.addStretch()

            status = item.get("status", "pending")
            from app.widgets.status_badge import StatusBadge
            badge = StatusBadge(status, self.translator)
            row_layout.addWidget(badge)

            self._recent_container.addWidget(row)

    def retranslate(self):
        """Update all text when language changes."""
        self._welcome_title.setText(self.translator.t("dashboard.welcome"))
        self._welcome_desc.setText(self.translator.t("dashboard.welcome_desc"))
        self._card_total["text_label"].setText(self.translator.t("dashboard.total_items"))
        self._card_completed["text_label"].setText(self.translator.t("dashboard.completed"))
        self._card_progress["text_label"].setText(self.translator.t("dashboard.in_progress"))
        self._card_pending["text_label"].setText(self.translator.t("dashboard.pending"))
        self._recent_title.setText(self.translator.t("dashboard.recent_activity"))
