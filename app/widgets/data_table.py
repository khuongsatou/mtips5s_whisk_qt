"""
Whisk Desktop — Data Table Widget.
"""
from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QWidget,
    QHBoxLayout, QPushButton,
)
from PySide6.QtCore import Signal, Qt
from app.widgets.status_badge import StatusBadge


class DataTable(QTableWidget):
    """Reusable data table with status badges and action buttons."""

    edit_clicked = Signal(str)    # Emits item ID
    delete_clicked = Signal(str)  # Emits item ID

    COLUMNS = ["name", "description", "status", "created_at", "actions"]

    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.translator.language_changed.connect(self.retranslate)
        self._item_ids: list[str] = []
        self._setup_table()

    def _setup_table(self):
        """Initialize table structure."""
        self.setColumnCount(len(self.COLUMNS))
        self._update_headers()
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)

        # Column sizing
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)       # Name
        header.setSectionResizeMode(1, QHeaderView.Stretch)       # Description
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Status
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Created At
        header.setSectionResizeMode(4, QHeaderView.Fixed)         # Actions
        self.setColumnWidth(4, 160)

    def _update_headers(self):
        """Set column headers using translator."""
        header_keys = [
            "items.name", "items.description", "items.status",
            "items.created_at", "items.actions",
        ]
        headers = [self.translator.t(k) for k in header_keys]
        self.setHorizontalHeaderLabels(headers)

    def load_data(self, items: list[dict]):
        """Populate the table with item data.

        Args:
            items: List of item dictionaries from the API.
        """
        self.setRowCount(0)
        self._item_ids.clear()

        for row, item in enumerate(items):
            self.insertRow(row)
            self._item_ids.append(item["id"])

            # Name
            name_item = QTableWidgetItem(item.get("name", ""))
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.setItem(row, 0, name_item)

            # Description
            desc_item = QTableWidgetItem(item.get("description", ""))
            desc_item.setFlags(desc_item.flags() & ~Qt.ItemIsEditable)
            self.setItem(row, 1, desc_item)

            # Status badge
            badge = StatusBadge(item.get("status", "pending"), self.translator)
            self.setCellWidget(row, 2, badge)

            # Created at
            created = item.get("created_at", "")
            if isinstance(created, str) and "T" in created:
                created = created.split("T")[0]  # Show date only
            date_item = QTableWidgetItem(str(created))
            date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)
            self.setItem(row, 3, date_item)

            # Action buttons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(4)

            edit_btn = QPushButton(self.translator.t("items.edit"))
            edit_btn.setObjectName("action_edit")
            edit_btn.clicked.connect(
                lambda checked, item_id=item["id"]: self.edit_clicked.emit(item_id)
            )
            actions_layout.addWidget(edit_btn)

            delete_btn = QPushButton(self.translator.t("items.delete"))
            delete_btn.setObjectName("danger_button")
            delete_btn.clicked.connect(
                lambda checked, item_id=item["id"]: self.delete_clicked.emit(item_id)
            )
            actions_layout.addWidget(delete_btn)

            self.setCellWidget(row, 4, actions_widget)

        self.resizeRowsToContents()

    def retranslate(self):
        """Update headers when language changes."""
        self._update_headers()
