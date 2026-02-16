"""
Whisk Desktop — Token Manager Dialog.

Modal dialog for managing API tokens with CRUD operations and expiration tracking.
"""
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QWidget,
    QAbstractItemView, QLineEdit, QTextEdit, QComboBox, QSpinBox,
)
from PySide6.QtCore import Qt, Signal


class TokenManagerDialog(QDialog):
    """Modal dialog for token management."""

    tokens_changed = Signal()

    def __init__(self, api, translator, parent=None):
        super().__init__(parent)
        self.api = api
        self.translator = translator
        self.setObjectName("token_manager_dialog")
        self.setWindowTitle(self.translator.t("token.title"))
        self.setMinimumSize(800, 540)
        self.setModal(True)
        self._editing_id = None
        self._setup_ui()
        self._load_tokens()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # --- Title ---
        title = QLabel(self.translator.t("token.title"))
        title.setObjectName("token_dialog_title")
        layout.addWidget(title)

        # --- Add/Edit section ---
        form_section = QWidget()
        form_section.setObjectName("token_form_section")
        form_layout = QVBoxLayout(form_section)
        form_layout.setContentsMargins(12, 12, 12, 12)
        form_layout.setSpacing(8)

        self._form_label = QLabel(self.translator.t("token.new"))
        self._form_label.setObjectName("token_form_label")
        form_layout.addWidget(self._form_label)

        # Name input
        self._name_input = QLineEdit()
        self._name_input.setObjectName("token_input")
        self._name_input.setPlaceholderText(
            self.translator.t("token.name_placeholder")
        )
        form_layout.addWidget(self._name_input)

        # Value input
        self._value_input = QTextEdit()
        self._value_input.setObjectName("token_value_input")
        self._value_input.setPlaceholderText(
            self.translator.t("token.value_placeholder")
        )
        self._value_input.setFixedHeight(55)
        form_layout.addWidget(self._value_input)

        # Type + Expiry row
        type_row = QHBoxLayout()
        type_row.setSpacing(8)

        # Token type combo
        type_label = QLabel(self.translator.t("token.type"))
        type_label.setObjectName("token_field_label")
        type_row.addWidget(type_label)

        self._type_combo = QComboBox()
        self._type_combo.setObjectName("token_type_combo")
        self._type_combo.addItem("Bearer", "bearer")
        self._type_combo.addItem("API Key", "api_key")
        self._type_combo.addItem("OAuth", "oauth")
        type_row.addWidget(self._type_combo)

        type_row.addSpacing(16)

        # Expiry days
        exp_label = QLabel(self.translator.t("token.expires_in"))
        exp_label.setObjectName("token_field_label")
        type_row.addWidget(exp_label)

        self._expiry_spin = QSpinBox()
        self._expiry_spin.setObjectName("token_expiry_spin")
        self._expiry_spin.setRange(0, 365)
        self._expiry_spin.setValue(30)
        self._expiry_spin.setSuffix(f" {self.translator.t('token.days')}")
        self._expiry_spin.setSpecialValueText(self.translator.t("token.no_expiry"))
        type_row.addWidget(self._expiry_spin)

        type_row.addStretch()
        form_layout.addLayout(type_row)

        # Form buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._cancel_edit_btn = QPushButton(self.translator.t("token.cancel"))
        self._cancel_edit_btn.setObjectName("token_cancel_btn")
        self._cancel_edit_btn.clicked.connect(self._on_cancel_edit)
        self._cancel_edit_btn.setVisible(False)
        btn_row.addWidget(self._cancel_edit_btn)

        self._save_btn = QPushButton(
            f"➕ {self.translator.t('token.create')}"
        )
        self._save_btn.setObjectName("token_save_btn")
        self._save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(self._save_btn)

        form_layout.addLayout(btn_row)
        layout.addWidget(form_section)

        # --- Token table ---
        self._table = QTableWidget()
        self._table.setObjectName("token_table")
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            self.translator.t("token.name"),
            self.translator.t("token.type"),
            self.translator.t("token.value_short"),
            self.translator.t("token.status"),
            self.translator.t("token.expires"),
            self.translator.t("token.actions"),
        ])
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.NoSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

        # Column sizing
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        self._table.setColumnWidth(0, 160)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        self._table.setColumnWidth(1, 80)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        self._table.setColumnWidth(3, 80)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        self._table.setColumnWidth(4, 140)
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        self._table.setColumnWidth(5, 100)

        layout.addWidget(self._table, 1)

        # --- Bottom bar ---
        bottom = QHBoxLayout()
        bottom.setSpacing(8)

        self._count_label = QLabel("")
        self._count_label.setObjectName("token_count_label")
        bottom.addWidget(self._count_label)

        bottom.addStretch()

        self._close_btn = QPushButton(self.translator.t("token.close"))
        self._close_btn.setObjectName("token_close_btn")
        self._close_btn.clicked.connect(self.accept)
        bottom.addWidget(self._close_btn)

        layout.addLayout(bottom)

    def _load_tokens(self):
        """Load tokens from API and populate table."""
        resp = self.api.get_tokens()
        if not resp.success:
            return
        tokens = resp.data or []
        self._table.setRowCount(0)

        for row, tok in enumerate(tokens):
            self._table.insertRow(row)
            self._table.setRowHeight(row, 44)

            # Name
            name_item = QTableWidgetItem(tok.get("name", ""))
            name_item.setToolTip(tok.get("name", ""))
            self._table.setItem(row, 0, name_item)

            # Type
            ttype = tok.get("token_type", "bearer")
            type_labels = {"bearer": "Bearer", "api_key": "API Key", "oauth": "OAuth"}
            type_item = QTableWidgetItem(type_labels.get(ttype, ttype))
            type_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, 1, type_item)

            # Value (truncated)
            value = tok.get("value", "")
            display_val = value[:20] + "..." if len(value) > 20 else value
            val_item = QTableWidgetItem(display_val)
            val_item.setToolTip(value)
            self._table.setItem(row, 2, val_item)

            # Status badge
            status = tok.get("status", "active")
            status_widget = QWidget()
            status_layout = QHBoxLayout(status_widget)
            status_layout.setContentsMargins(4, 4, 4, 4)
            status_layout.setAlignment(Qt.AlignCenter)
            badge = QLabel()
            badge.setAlignment(Qt.AlignCenter)
            if status == "active":
                badge.setText("✅")
                badge.setObjectName("token_badge_active")
            elif status == "expired":
                badge.setText("❌")
                badge.setObjectName("token_badge_expired")
            else:
                badge.setText("🚫")
                badge.setObjectName("token_badge_revoked")
            badge.setToolTip(self.translator.t(f"token.{status}"))
            status_layout.addWidget(badge)
            self._table.setCellWidget(row, 3, status_widget)

            # Expires
            expires_at = tok.get("expires_at")
            if expires_at:
                try:
                    dt = datetime.fromisoformat(expires_at)
                    now = datetime.now()
                    if dt > now:
                        delta = dt - now
                        days = delta.days
                        if days > 0:
                            exp_text = f"{days}d remaining"
                        else:
                            hours = delta.seconds // 3600
                            exp_text = f"{hours}h remaining"
                    else:
                        exp_text = dt.strftime("%Y-%m-%d %H:%M")
                except (ValueError, TypeError):
                    exp_text = str(expires_at)
            else:
                exp_text = self.translator.t("token.no_expiry")
            exp_item = QTableWidgetItem(exp_text)
            exp_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, 4, exp_item)

            # Actions: edit + delete
            token_id = tok.get("id", "")
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)
            action_layout.setSpacing(4)
            action_layout.setAlignment(Qt.AlignCenter)

            edit_btn = QPushButton("✏️")
            edit_btn.setObjectName("token_action_btn")
            edit_btn.setFixedSize(28, 28)
            edit_btn.setToolTip(self.translator.t("token.edit"))
            edit_btn.clicked.connect(
                lambda checked, tid=token_id, t=tok: self._on_edit(tid, t)
            )
            action_layout.addWidget(edit_btn)

            del_btn = QPushButton("🗑️")
            del_btn.setObjectName("token_action_btn")
            del_btn.setFixedSize(28, 28)
            del_btn.setToolTip(self.translator.t("token.delete"))
            del_btn.clicked.connect(
                lambda checked, tid=token_id: self._on_delete(tid)
            )
            action_layout.addWidget(del_btn)

            self._table.setCellWidget(row, 5, action_widget)

        self._count_label.setText(
            f"{self.translator.t('token.count')}: {len(tokens)}"
        )

    def _on_save(self):
        """Create or update a token."""
        name = self._name_input.text().strip()
        value = self._value_input.toPlainText().strip()

        if not name:
            return

        token_type = self._type_combo.currentData()
        expiry_days = self._expiry_spin.value()

        data = {
            "name": name,
            "value": value,
            "token_type": token_type,
        }
        if expiry_days > 0:
            data["expires_at"] = expiry_days
        else:
            data["expires_at"] = None

        if self._editing_id:
            self.api.update_token(self._editing_id, data)
            self._on_cancel_edit()
        else:
            self.api.add_token(data)
            self._name_input.clear()
            self._value_input.clear()
            self._type_combo.setCurrentIndex(0)
            self._expiry_spin.setValue(30)

        self._load_tokens()
        self.tokens_changed.emit()

    def _on_edit(self, token_id: str, tok: dict):
        """Populate form for editing."""
        self._editing_id = token_id
        self._name_input.setText(tok.get("name", ""))
        self._value_input.setPlainText(tok.get("value", ""))
        # Set type combo
        ttype = tok.get("token_type", "bearer")
        for i in range(self._type_combo.count()):
            if self._type_combo.itemData(i) == ttype:
                self._type_combo.setCurrentIndex(i)
                break
        # Set expiry
        expires_at = tok.get("expires_at")
        if expires_at:
            try:
                dt = datetime.fromisoformat(expires_at)
                days_left = max(0, (dt - datetime.now()).days)
                self._expiry_spin.setValue(days_left if days_left > 0 else 1)
            except (ValueError, TypeError):
                self._expiry_spin.setValue(30)
        else:
            self._expiry_spin.setValue(0)

        self._form_label.setText(self.translator.t("token.editing"))
        self._save_btn.setText(f"💾 {self.translator.t('token.save')}")
        self._cancel_edit_btn.setVisible(True)

    def _on_cancel_edit(self):
        """Cancel editing and reset form."""
        self._editing_id = None
        self._name_input.clear()
        self._value_input.clear()
        self._type_combo.setCurrentIndex(0)
        self._expiry_spin.setValue(30)
        self._form_label.setText(self.translator.t("token.new"))
        self._save_btn.setText(f"➕ {self.translator.t('token.create')}")
        self._cancel_edit_btn.setVisible(False)

    def _on_delete(self, token_id: str):
        """Delete a token."""
        self.api.delete_token(token_id)
        if self._editing_id == token_id:
            self._on_cancel_edit()
        self._load_tokens()
        self.tokens_changed.emit()
