"""
Whisk Desktop — Items Page.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QDialog, QFormLayout, QTextEdit, QComboBox,
    QMessageBox,
)
from PySide6.QtCore import Qt
from app.widgets.data_table import DataTable


class ItemDialog(QDialog):
    """Dialog for creating or editing an item."""

    def __init__(self, translator, item_data=None, parent=None):
        super().__init__(parent)
        self.translator = translator
        self._item_data = item_data
        self._setup_ui()

    def _setup_ui(self):
        is_edit = self._item_data is not None
        title = self.translator.t("dialog.edit_item" if is_edit else "dialog.add_item")
        self.setWindowTitle(title)
        self.setMinimumWidth(420)

        layout = QFormLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Name
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText(self.translator.t("items.name"))
        if is_edit:
            self._name_input.setText(self._item_data.get("name", ""))
        layout.addRow(self.translator.t("items.name"), self._name_input)

        # Description
        self._desc_input = QTextEdit()
        self._desc_input.setPlaceholderText(self.translator.t("items.description"))
        self._desc_input.setMaximumHeight(100)
        if is_edit:
            self._desc_input.setPlainText(self._item_data.get("description", ""))
        layout.addRow(self.translator.t("items.description"), self._desc_input)

        # Status
        self._status_combo = QComboBox()
        self._status_combo.addItem(self.translator.t("status.pending"), "pending")
        self._status_combo.addItem(self.translator.t("status.in_progress"), "in_progress")
        self._status_combo.addItem(self.translator.t("status.completed"), "completed")
        if is_edit:
            status = self._item_data.get("status", "pending")
            statuses = ["pending", "in_progress", "completed"]
            if status in statuses:
                self._status_combo.setCurrentIndex(statuses.index(status))
        layout.addRow(self.translator.t("items.status"), self._status_combo)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton(self.translator.t("dialog.cancel"))
        cancel_btn.setObjectName("secondary_button")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton(self.translator.t("dialog.save"))
        save_btn.setObjectName("primary_button")
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)

        layout.addRow(btn_layout)

    def get_data(self) -> dict:
        """Return form data as a dictionary."""
        return {
            "name": self._name_input.text().strip(),
            "description": self._desc_input.toPlainText().strip(),
            "status": self._status_combo.currentData(),
        }


class ItemsPage(QWidget):
    """Items management page with search, table, and CRUD dialogs."""

    def __init__(self, translator, api, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.api = api
        self.translator.language_changed.connect(self.retranslate)
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Title
        self._title = QLabel(self.translator.t("items.title"))
        self._title.setObjectName("section_title")
        layout.addWidget(self._title)

        # Toolbar: search + add button
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText(self.translator.t("items.search"))
        self._search_input.textChanged.connect(self._on_search)
        toolbar.addWidget(self._search_input)

        self._add_btn = QPushButton(f"➕ {self.translator.t('items.add')}")
        self._add_btn.setObjectName("primary_button")
        self._add_btn.clicked.connect(self._on_add)
        toolbar.addWidget(self._add_btn)

        layout.addLayout(toolbar)

        # Data table
        self._table = DataTable(self.translator)
        self._table.edit_clicked.connect(self._on_edit)
        self._table.delete_clicked.connect(self._on_delete)
        layout.addWidget(self._table)

    def refresh_data(self):
        """Reload items from API."""
        response = self.api.get_items(page=1, per_page=100)
        if response.success:
            self._all_items = response.data or []
            self._table.load_data(self._all_items)

    def _on_search(self, text: str):
        """Filter table by search text."""
        if not text.strip():
            self._table.load_data(self._all_items)
            return
        query = text.lower()
        filtered = [
            item for item in self._all_items
            if query in item.get("name", "").lower()
            or query in item.get("description", "").lower()
        ]
        self._table.load_data(filtered)

    def _on_add(self):
        """Open dialog to create a new item."""
        dialog = ItemDialog(self.translator, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data["name"]:
                self.api.create_item(data)
                self.refresh_data()

    def _on_edit(self, item_id: str):
        """Open dialog to edit an existing item."""
        response = self.api.get_item(item_id)
        if not response.success:
            return
        dialog = ItemDialog(self.translator, item_data=response.data, parent=self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            self.api.update_item(item_id, data)
            self.refresh_data()

    def _on_delete(self, item_id: str):
        """Confirm and delete an item."""
        reply = QMessageBox.question(
            self,
            self.translator.t("dialog.confirm_title"),
            self.translator.t("items.confirm_delete"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.api.delete_item(item_id)
            self.refresh_data()

    def retranslate(self):
        """Update text when language changes."""
        self._title.setText(self.translator.t("items.title"))
        self._search_input.setPlaceholderText(self.translator.t("items.search"))
        self._add_btn.setText(f"➕ {self.translator.t('items.add')}")
        self.refresh_data()
