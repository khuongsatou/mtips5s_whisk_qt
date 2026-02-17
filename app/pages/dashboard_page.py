"""
Whisk Desktop — Dashboard Statistics Page.

Real-time queue statistics with stat cards, completion rate bar,
recent completed tasks, and error summary.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QProgressBar,
)
from PySide6.QtCore import Qt


class DashboardPage(QWidget):
    """Dashboard with queue statistics, completion rate, and recent activity."""

    def __init__(self, translator, api, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.api = api
        self.setObjectName("dashboard_page")
        self.translator.language_changed.connect(self.retranslate)
        self._setup_ui()

    # ── UI Setup ─────────────────────────────────────────────────────

    def _setup_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        self._layout = QVBoxLayout(container)
        self._layout.setContentsMargins(24, 24, 24, 24)
        self._layout.setSpacing(20)

        # ── Welcome Header ───────────────────────────────────────────
        self._welcome_title = QLabel(self.translator.t("dashboard.welcome"))
        self._welcome_title.setObjectName("page_title")
        self._layout.addWidget(self._welcome_title)

        self._welcome_desc = QLabel(self.translator.t("dashboard.title"))
        self._welcome_desc.setObjectName("welcome_desc")
        self._welcome_desc.setWordWrap(True)
        self._layout.addWidget(self._welcome_desc)

        # ── Stat Cards Row ───────────────────────────────────────────
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)

        self._card_total = self._create_card(
            "0", self.translator.t("dashboard.total_tasks"),
            "📊", "card_primary",
        )
        cards_row.addWidget(self._card_total["frame"])

        self._card_completed = self._create_card(
            "0", self.translator.t("dashboard.completed"),
            "✅", "card_secondary",
        )
        cards_row.addWidget(self._card_completed["frame"])

        self._card_pending = self._create_card(
            "0", self.translator.t("dashboard.pending"),
            "⏳", "card_accent",
        )
        cards_row.addWidget(self._card_pending["frame"])

        self._card_errors = self._create_card(
            "0", self.translator.t("dashboard.errors"),
            "❌", "card_danger",
        )
        cards_row.addWidget(self._card_errors["frame"])

        self._layout.addLayout(cards_row)

        # ── Completion Rate Bar ──────────────────────────────────────
        rate_section = QFrame()
        rate_section.setObjectName("dashboard_section")
        rate_layout = QVBoxLayout(rate_section)
        rate_layout.setContentsMargins(16, 16, 16, 16)
        rate_layout.setSpacing(8)

        rate_header = QHBoxLayout()
        self._rate_title = QLabel(
            f"📈 {self.translator.t('dashboard.completion_rate')}"
        )
        self._rate_title.setObjectName("section_title")
        rate_header.addWidget(self._rate_title)

        self._rate_percent = QLabel("0%")
        self._rate_percent.setObjectName("rate_percent")
        self._rate_percent.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        rate_header.addWidget(self._rate_percent)

        rate_layout.addLayout(rate_header)

        self._completion_bar = QProgressBar()
        self._completion_bar.setObjectName("completion_bar")
        self._completion_bar.setRange(0, 100)
        self._completion_bar.setValue(0)
        self._completion_bar.setTextVisible(False)
        self._completion_bar.setFixedHeight(12)
        rate_layout.addWidget(self._completion_bar)

        self._layout.addWidget(rate_section)

        # ── Recent Completed ─────────────────────────────────────────
        recent_section = QFrame()
        recent_section.setObjectName("dashboard_section")
        recent_layout = QVBoxLayout(recent_section)
        recent_layout.setContentsMargins(16, 16, 16, 16)
        recent_layout.setSpacing(8)

        self._recent_title = QLabel(
            f"🕐 {self.translator.t('dashboard.recent_completed')}"
        )
        self._recent_title.setObjectName("section_title")
        recent_layout.addWidget(self._recent_title)

        self._recent_container = QVBoxLayout()
        self._recent_container.setSpacing(6)
        recent_layout.addLayout(self._recent_container)

        self._no_recent_label = QLabel(self.translator.t("dashboard.no_tasks"))
        self._no_recent_label.setObjectName("empty_state")
        self._no_recent_label.setAlignment(Qt.AlignCenter)
        self._recent_container.addWidget(self._no_recent_label)

        self._layout.addWidget(recent_section)

        # ── Error Summary ────────────────────────────────────────────
        error_section = QFrame()
        error_section.setObjectName("dashboard_section")
        error_layout = QVBoxLayout(error_section)
        error_layout.setContentsMargins(16, 16, 16, 16)
        error_layout.setSpacing(8)

        self._error_title = QLabel(
            f"⚠️ {self.translator.t('dashboard.error_summary')}"
        )
        self._error_title.setObjectName("section_title")
        error_layout.addWidget(self._error_title)

        self._error_container = QVBoxLayout()
        self._error_container.setSpacing(6)
        error_layout.addLayout(self._error_container)

        self._no_errors_label = QLabel("✨ " + self.translator.t("dashboard.no_errors"))
        self._no_errors_label.setObjectName("empty_state")
        self._no_errors_label.setAlignment(Qt.AlignCenter)
        self._error_container.addWidget(self._no_errors_label)

        self._layout.addWidget(error_section)

        # ── Stretch + Scroll ─────────────────────────────────────────
        self._layout.addStretch()
        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    # ── Card Factory ──────────────────────────────────────────────────

    def _create_card(self, value: str, label: str, icon: str, style_id: str) -> dict:
        """Create a stat card widget with icon, value, and label."""
        frame = QFrame()
        frame.setObjectName(style_id)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(4)

        icon_label = QLabel(icon)
        icon_label.setObjectName("card_icon")
        layout.addWidget(icon_label)

        value_label = QLabel(value)
        value_label.setObjectName("card_value")
        layout.addWidget(value_label)

        text_label = QLabel(label)
        text_label.setObjectName("card_label")
        layout.addWidget(text_label)

        return {
            "frame": frame,
            "value_label": value_label,
            "text_label": text_label,
        }

    # ── Data Refresh ──────────────────────────────────────────────────

    def refresh_data(self):
        """Fetch queue data and update all stat displays."""
        response = self.api.get_queue()
        if not response.success:
            return
        self.update_stats(response.data or [])

    def update_stats(self, tasks: list):
        """Update all dashboard displays from a list of task dicts."""
        # Count by status
        total = len(tasks)
        completed = sum(1 for t in tasks if t.get("status") == "completed")
        pending = sum(
            1 for t in tasks
            if t.get("status") in ("pending", "running")
        )
        errors = sum(1 for t in tasks if t.get("status") == "error")

        # Update stat cards
        self._card_total["value_label"].setText(str(total))
        self._card_completed["value_label"].setText(str(completed))
        self._card_pending["value_label"].setText(str(pending))
        self._card_errors["value_label"].setText(str(errors))

        # Update completion rate
        rate = round(completed / total * 100) if total > 0 else 0
        self._completion_bar.setValue(rate)
        self._rate_percent.setText(f"{rate}%")

        # Recent completed (up to 5, newest first)
        completed_tasks = sorted(
            [t for t in tasks if t.get("status") == "completed"],
            key=lambda t: t.get("completed_at", ""),
            reverse=True,
        )[:5]
        self._populate_recent(completed_tasks)

        # Error summary (up to 3)
        error_tasks = [t for t in tasks if t.get("status") == "error"][:3]
        self._populate_errors(error_tasks)

    def _populate_recent(self, tasks: list):
        """Populate recent completed tasks list."""
        self._clear_layout(self._recent_container)

        if not tasks:
            label = QLabel(self.translator.t("dashboard.no_tasks"))
            label.setObjectName("empty_state")
            label.setAlignment(Qt.AlignCenter)
            self._recent_container.addWidget(label)
            return

        for task in tasks:
            row = QFrame()
            row.setObjectName("recent_item")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(12, 8, 12, 8)
            row_layout.setSpacing(8)

            # Prompt preview (truncated)
            prompt = task.get("prompt", "")[:60]
            if len(task.get("prompt", "")) > 60:
                prompt += "…"
            prompt_lbl = QLabel(prompt or "—")
            prompt_lbl.setObjectName("recent_prompt")
            row_layout.addWidget(prompt_lbl, 1)

            # Completed timestamp
            completed_at = task.get("completed_at", "")
            if completed_at:
                # Show just HH:MM part
                time_part = completed_at.split(" ")[-1][:5] if " " in completed_at else completed_at[:5]
                time_lbl = QLabel(f"✅ {time_part}")
            else:
                time_lbl = QLabel("✅")
            time_lbl.setObjectName("recent_time")
            time_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row_layout.addWidget(time_lbl)

            self._recent_container.addWidget(row)

    def _populate_errors(self, tasks: list):
        """Populate error summary list."""
        self._clear_layout(self._error_container)

        if not tasks:
            label = QLabel("✨ " + self.translator.t("dashboard.no_errors"))
            label.setObjectName("empty_state")
            label.setAlignment(Qt.AlignCenter)
            self._error_container.addWidget(label)
            return

        for task in tasks:
            row = QFrame()
            row.setObjectName("error_item")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(12, 8, 12, 8)
            row_layout.setSpacing(8)

            # Prompt preview
            prompt = task.get("prompt", "")[:40]
            if len(task.get("prompt", "")) > 40:
                prompt += "…"
            prompt_lbl = QLabel(prompt or "—")
            prompt_lbl.setObjectName("error_prompt")
            row_layout.addWidget(prompt_lbl, 1)

            # Error message
            error_msg = task.get("error_message", "Unknown error")[:50]
            error_lbl = QLabel(f"❌ {error_msg}")
            error_lbl.setObjectName("error_msg")
            error_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row_layout.addWidget(error_lbl, 1)

            self._error_container.addWidget(row)

    @staticmethod
    def _clear_layout(layout):
        """Remove all widgets from a layout."""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    # ── Retranslation ─────────────────────────────────────────────────

    def retranslate(self):
        """Update all text when language changes."""
        self._welcome_title.setText(self.translator.t("dashboard.welcome"))
        self._welcome_desc.setText(self.translator.t("dashboard.title"))
        self._card_total["text_label"].setText(
            self.translator.t("dashboard.total_tasks")
        )
        self._card_completed["text_label"].setText(
            self.translator.t("dashboard.completed")
        )
        self._card_pending["text_label"].setText(
            self.translator.t("dashboard.pending")
        )
        self._card_errors["text_label"].setText(
            self.translator.t("dashboard.errors")
        )
        self._rate_title.setText(
            f"📈 {self.translator.t('dashboard.completion_rate')}"
        )
        self._recent_title.setText(
            f"🕐 {self.translator.t('dashboard.recent_completed')}"
        )
        self._error_title.setText(
            f"⚠️ {self.translator.t('dashboard.error_summary')}"
        )
