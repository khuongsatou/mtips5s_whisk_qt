"""
Whisk Desktop — Project Manager Dialog.

Modal dialog for managing projects with CRUD operations.
"""
import logging
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QWidget,
    QAbstractItemView, QLineEdit, QMessageBox,
)
from PySide6.QtCore import Qt, Signal

from PySide6.QtGui import QCursor

logger = logging.getLogger("whisk.project_dialog")


class ProjectManagerDialog(QDialog):
    """Modal dialog for project management."""

    projects_changed = Signal()
    project_activated = Signal(str)  # Emits the active project name
    project_activated_with_id = Signal(str, str)  # Emits (project_id, project_name)

    def __init__(self, api, translator, parent=None, flow_api=None, cookie_api=None, active_flow_id=None):
        super().__init__(parent)
        self.api = api
        self.translator = translator
        self.flow_api = flow_api
        self.cookie_api = cookie_api
        self.active_flow_id = active_flow_id
        self.setObjectName("project_manager_dialog")
        self.setWindowTitle(self.translator.t("project.title"))
        self.setMinimumSize(750, 520)
        self.setModal(True)
        self._editing_id = None  # Track which project is being edited
        self._setup_ui()
        self._load_projects()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # --- Title ---
        title = QLabel(self.translator.t("project.title"))
        title.setObjectName("project_dialog_title")
        layout.addWidget(title)

        # --- Add/Edit section ---
        form_section = QWidget()
        form_section.setObjectName("project_form_section")
        form_layout = QVBoxLayout(form_section)
        form_layout.setContentsMargins(12, 12, 12, 12)
        form_layout.setSpacing(8)

        self._form_label = QLabel(self.translator.t("project.new"))
        self._form_label.setObjectName("project_form_label")
        form_layout.addWidget(self._form_label)

        # Name input
        self._name_input = QLineEdit()
        self._name_input.setObjectName("project_input")
        self._name_input.setPlaceholderText(
            self.translator.t("project.name_placeholder")
        )
        form_layout.addWidget(self._name_input)



        # Form buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._cancel_edit_btn = QPushButton(self.translator.t("project.cancel"))
        self._cancel_edit_btn.setObjectName("project_cancel_btn")
        self._cancel_edit_btn.clicked.connect(self._on_cancel_edit)
        self._cancel_edit_btn.setVisible(False)
        btn_row.addWidget(self._cancel_edit_btn)

        self._save_btn = QPushButton(
            f"➕ {self.translator.t('project.create')}"
        )
        self._save_btn.setObjectName("project_save_btn")
        self._save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(self._save_btn)

        form_layout.addLayout(btn_row)
        layout.addWidget(form_section)

        # --- Project table ---
        self._table = QTableWidget()
        self._table.setObjectName("project_table")
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels([
            self.translator.t("project.name"),
            self.translator.t("project.status"),
            self.translator.t("project.updated"),
            self.translator.t("project.actions"),
        ])
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.NoSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

        # Column sizing
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        self._table.setColumnWidth(1, 80)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        self._table.setColumnWidth(2, 130)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        self._table.setColumnWidth(3, 130)

        layout.addWidget(self._table, 1)

        # --- Bottom bar ---
        bottom = QHBoxLayout()
        bottom.setSpacing(8)

        self._count_label = QLabel("")
        self._count_label.setObjectName("project_count_label")
        bottom.addWidget(self._count_label)

        bottom.addStretch()

        self._close_btn = QPushButton(self.translator.t("project.close"))
        self._close_btn.setObjectName("project_close_btn")
        self._close_btn.clicked.connect(self.accept)
        bottom.addWidget(self._close_btn)

        # Cookie button
        self._cookie_btn = QPushButton("🍪 Cookie")
        self._cookie_btn.setObjectName("project_save_btn")
        self._cookie_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self._cookie_btn.clicked.connect(self._on_open_cookies)
        bottom.addWidget(self._cookie_btn)

        layout.addLayout(bottom)

    def _on_open_cookies(self):
        """Open cookie manager dialog."""
        from app.widgets.cookie_manager_dialog import CookieManagerDialog
        dialog = CookieManagerDialog(
            self.api, self.translator, self,
            cookie_api=self.cookie_api,
            active_flow_id=int(self.active_flow_id) if self.active_flow_id else None,
        )
        dialog.exec()

    def _load_projects(self):
        """Load projects from API and populate table."""
        # Try real API first, then fall back to mock
        projects = []
        if self.flow_api:
            resp = self.flow_api.get_flows(flow_type="WHISK")
            if resp.success and resp.data:
                items = resp.data.get("items", [])
                # Map server flow fields to project fields for UI
                for item in items:
                    projects.append({
                        "id": str(item.get("id", "")),
                        "name": item.get("name", ""),
                        "description": item.get("description", ""),
                        "status": item.get("status", "active"),
                        "updated_at": item.get("updated_at", item.get("created_at", "")),
                    })
                logger.info(f"Loaded {len(projects)} projects from server")
            else:
                logger.warning(f"Flow API failed: {resp.message}, falling back to mock")
                resp = self.api.get_projects()
                if resp.success:
                    projects = resp.data or []
        else:
            resp = self.api.get_projects()
            if resp.success:
                projects = resp.data or []

        # Get active project id
        active_resp = self.api.get_active_project()
        active_id = active_resp.data.get("id", "") if active_resp.success and active_resp.data else ""
        self._table.setRowCount(0)

        for row, proj in enumerate(projects):
            self._table.insertRow(row)
            self._table.setRowHeight(row, 44)

            # Name
            name_item = QTableWidgetItem(proj.get("name", ""))
            name_item.setToolTip(proj.get("name", ""))
            self._table.setItem(row, 0, name_item)

            # Status badge
            status = proj.get("status", "active")
            is_active_project = proj.get("id", "") == active_id
            status_widget = QWidget()
            status_layout = QHBoxLayout(status_widget)
            status_layout.setContentsMargins(4, 4, 4, 4)
            status_layout.setAlignment(Qt.AlignCenter)
            badge = QLabel()
            badge.setAlignment(Qt.AlignCenter)
            if is_active_project:
                badge.setText("⭐")
                badge.setObjectName("project_badge_active")
                badge.setToolTip(self.translator.t("project.current"))
            else:
                status_map = {
                    "pending":   ("⏳", "project_badge_pending"),
                    "active":    ("🟢", "project_badge_active"),
                    "completed": ("✅", "project_badge_completed"),
                    "paused":    ("⏸️", "project_badge_paused"),
                    "error":     ("❌", "project_badge_error"),
                    "archived":  ("📁", "project_badge_archived"),
                }
                icon, obj_name = status_map.get(status, ("❓", "project_badge_unknown"))
                badge.setText(icon)
                badge.setObjectName(obj_name)
                badge.setToolTip(status)
            status_layout.addWidget(badge)
            self._table.setCellWidget(row, 1, status_widget)

            # Updated at
            updated = proj.get("updated_at", "")
            if updated:
                try:
                    dt = datetime.fromisoformat(updated)
                    upd_text = dt.strftime("%Y-%m-%d %H:%M")
                except (ValueError, TypeError):
                    upd_text = str(updated)
            else:
                upd_text = "—"
            upd_item = QTableWidgetItem(upd_text)
            upd_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, 2, upd_item)

            # Actions: activate + edit + delete
            project_id = proj.get("id", "")
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)
            action_layout.setSpacing(4)
            action_layout.setAlignment(Qt.AlignCenter)

            activate_btn = QPushButton("☐" if not is_active_project else "☑️")
            activate_btn.setObjectName("project_action_btn")
            activate_btn.setFixedSize(28, 28)
            activate_btn.setToolTip(self.translator.t("project.activate"))
            activate_btn.setEnabled(not is_active_project)
            activate_btn.clicked.connect(
                lambda checked, pid=project_id, pname=proj.get("name", ""): self._on_activate(pid, pname)
            )
            action_layout.addWidget(activate_btn)

            edit_btn = QPushButton("✏️")
            edit_btn.setObjectName("project_action_btn")
            edit_btn.setFixedSize(28, 28)
            edit_btn.setToolTip(self.translator.t("project.edit"))
            edit_btn.clicked.connect(
                lambda checked, pid=project_id, p=proj: self._on_edit(pid, p)
            )
            action_layout.addWidget(edit_btn)

            del_btn = QPushButton("🗑️")
            del_btn.setObjectName("project_action_btn")
            del_btn.setFixedSize(28, 28)
            del_btn.setToolTip(self.translator.t("project.delete"))
            del_btn.clicked.connect(
                lambda checked, pid=project_id: self._on_delete(pid)
            )
            action_layout.addWidget(del_btn)

            self._table.setCellWidget(row, 3, action_widget)

        self._count_label.setText(
            f"{self.translator.t('project.count')}: {len(projects)}"
        )

    def _on_save(self):
        """Create or update a project."""
        name = self._name_input.text().strip()

        if not name:
            return

        if len(name) < 3:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Invalid Name",
                "Project name must be at least 3 characters.",
            )
            return

        if self._editing_id:
            # Update existing (mock only for now)
            self.api.update_project(self._editing_id, {
                "name": name,
            })
            self._on_cancel_edit()
        else:
            # Create new — call real API first
            if self.flow_api:
                resp = self.flow_api.create_flow({
                    "name": name,
                    "type": "WHISK",
                    "status": "pending",
                    "config": {},
                })
                logger.info(f"create_flow result: success={resp.success}, message={resp.message}")
            else:
                self.api.add_project({
                    "name": name,
                })
            self._name_input.clear()

        self._load_projects()
        self.projects_changed.emit()

    def _on_activate(self, project_id: str, project_name: str):
        """Set a project as active and close the dialog."""
        self.api.set_active_project(project_id)
        self.project_activated.emit(project_name)
        self.project_activated_with_id.emit(project_id, project_name)
        self.accept()

    def _on_edit(self, project_id: str, proj: dict):
        """Populate form for editing."""
        self._editing_id = project_id
        self._name_input.setText(proj.get("name", ""))
        self._form_label.setText(self.translator.t("project.editing"))
        self._save_btn.setText(f"💾 {self.translator.t('project.save')}")
        self._cancel_edit_btn.setVisible(True)

    def _on_cancel_edit(self):
        """Cancel editing and reset form."""
        self._editing_id = None
        self._name_input.clear()
        self._form_label.setText(self.translator.t("project.new"))
        self._save_btn.setText(f"➕ {self.translator.t('project.create')}")
        self._cancel_edit_btn.setVisible(False)

    def _on_delete(self, project_id: str):
        """Delete a project."""
        # Call real API if available
        if self.flow_api:
            try:
                fid = int(project_id)
                resp = self.flow_api.delete_flow(fid)
                logger.info(f"delete_flow({fid}) result: success={resp.success}")
            except (ValueError, TypeError):
                logger.warning(f"Invalid flow ID for delete: {project_id}")
        else:
            self.api.delete_project(project_id)
        if self._editing_id == project_id:
            self._on_cancel_edit()
        self._load_projects()
        self.projects_changed.emit()
