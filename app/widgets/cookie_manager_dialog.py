"""
Whisk Desktop — Cookie Manager Dialog.

Modal dialog for managing browser cookies used for API authentication.
Flow: Paste session-token → Test → Save (if valid) → List / Delete.
"""
import logging
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QWidget,
    QAbstractItemView, QTextEdit, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor

logger = logging.getLogger("whisk.cookie_dialog")

PROVIDER = "WHISK"


class CookieManagerDialog(QDialog):
    """Modal dialog for cookie management."""

    cookies_changed = Signal()  # Emitted when cookies are added/deleted

    def __init__(self, api, translator, parent=None, cookie_api=None, active_flow_id=None):
        super().__init__(parent)
        self.api = api
        self.translator = translator
        self.cookie_api = cookie_api
        self._active_flow_id = int(active_flow_id) if active_flow_id else None
        self.setObjectName("cookie_manager_dialog")
        self.setWindowTitle(self.translator.t("cookie.title"))
        self.setMinimumSize(700, 500)
        self.setModal(True)
        self._setup_ui()
        self._load_cookies()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # --- Title ---
        title = QLabel(self.translator.t("cookie.title"))
        title.setObjectName("cookie_dialog_title")
        layout.addWidget(title)

        # --- Add cookie section ---
        add_section = QWidget()
        add_section.setObjectName("cookie_add_section")
        add_layout = QVBoxLayout(add_section)
        add_layout.setContentsMargins(12, 12, 12, 12)
        add_layout.setSpacing(8)

        add_label = QLabel(self.translator.t("cookie.add"))
        add_label.setObjectName("cookie_add_label")
        add_layout.addWidget(add_label)

        # Session token input
        self._value_input = QTextEdit()
        self._value_input.setObjectName("cookie_value_input")
        self._value_input.setPlaceholderText(
            "Paste __Secure-next-auth.session-token value here..."
        )
        self._value_input.setFixedHeight(60)
        add_layout.addWidget(self._value_input)

        # Status label for test results
        self._status_label = QLabel("")
        self._status_label.setObjectName("cookie_status_label")
        self._status_label.setWordWrap(True)
        self._status_label.setVisible(False)
        add_layout.addWidget(self._status_label)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._add_btn = QPushButton(f"➕ {self.translator.t('cookie.add_btn')}")
        self._add_btn.setObjectName("cookie_add_btn")
        self._add_btn.clicked.connect(self._on_add_cookie)
        btn_row.addWidget(self._add_btn)

        add_layout.addLayout(btn_row)
        layout.addWidget(add_section)

        # --- Cookie table ---
        self._table = QTableWidget()
        self._table.setObjectName("cookie_table")
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels([
            self.translator.t("cookie.name"),
            self.translator.t("cookie.status"),
            self.translator.t("cookie.expires"),
            "Provider",
            self.translator.t("cookie.actions"),
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
        self._table.setColumnWidth(2, 150)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        self._table.setColumnWidth(3, 90)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        self._table.setColumnWidth(4, 120)

        layout.addWidget(self._table, 1)

        # --- Bottom bar ---
        bottom = QHBoxLayout()
        bottom.setSpacing(8)

        self._count_label = QLabel("")
        self._count_label.setObjectName("cookie_count_label")
        bottom.addWidget(self._count_label)

        bottom.addStretch()

        self._refresh_btn = QPushButton(f"🔄 {self.translator.t('cookie.refresh_all')}")
        self._refresh_btn.setObjectName("cookie_refresh_btn")
        self._refresh_btn.clicked.connect(self._load_cookies)
        bottom.addWidget(self._refresh_btn)

        self._close_btn = QPushButton(self.translator.t("cookie.close"))
        self._close_btn.setObjectName("cookie_close_btn")
        self._close_btn.clicked.connect(self.accept)
        bottom.addWidget(self._close_btn)

        layout.addLayout(bottom)

    # ── Load cookies from server ──────────────────────────────────────

    def _load_cookies(self):
        """Load cookies/api-keys from server and populate table."""
        cookies = []
        if self.cookie_api and self._active_flow_id:
            resp = self.cookie_api.get_api_keys(
                flow_id=self._active_flow_id,
                provider=PROVIDER,
            )
            if resp.success and resp.data:
                items = resp.data.get("items", [])
                for item in items:
                    # Extract user info from metadata
                    meta = item.get("metadata", {})
                    user_email = meta.get("user_email", "")
                    label = item.get("label", "")

                    cookies.append({
                        "id": str(item.get("id", "")),
                        "name": label or user_email or f"api-key-{item.get('id', '')}",
                        "status": item.get("status", "unknown"),
                        "expires_at": item.get("expired"),
                        "provider": item.get("provider", PROVIDER),
                        "error": item.get("error", False),
                        "msg_error": item.get("msg_error", ""),
                    })
                logger.info(f"Loaded {len(cookies)} api-keys from server")
            else:
                logger.warning(f"Cookie API failed: {resp.message}, falling back to mock")
                resp = self.api.get_cookies()
                if resp.success:
                    cookies = resp.data or []
        else:
            if not self._active_flow_id:
                logger.warning("No active flow ID, cannot load cookies from server")
            resp = self.api.get_cookies()
            if resp.success:
                cookies = resp.data or []

        self._table.setRowCount(0)

        for row, cookie in enumerate(cookies):
            self._table.insertRow(row)
            self._table.setRowHeight(row, 40)

            # Name / Label
            name = cookie.get("name", "")
            name_item = QTableWidgetItem(name)
            name_item.setToolTip(name)
            self._table.setItem(row, 0, name_item)

            # Status badge
            status = cookie.get("status", "unknown")
            error = cookie.get("error", False)
            status_widget = QWidget()
            status_layout = QHBoxLayout(status_widget)
            status_layout.setContentsMargins(4, 4, 4, 4)
            status_layout.setAlignment(Qt.AlignCenter)
            badge = QLabel()
            badge.setAlignment(Qt.AlignCenter)

            if error:
                badge.setText("❌")
                badge.setObjectName("cookie_badge_error")
                badge.setToolTip(cookie.get("msg_error", "Error"))
            elif status == "active":
                badge.setText("✅")
                badge.setObjectName("cookie_badge_valid")
                badge.setToolTip("Active")
            elif status == "expired":
                badge.setText("⏰")
                badge.setObjectName("cookie_badge_expired")
                badge.setToolTip("Expired")
            else:
                badge.setText("❓")
                badge.setObjectName("cookie_badge_unknown")
                badge.setToolTip(status)

            status_layout.addWidget(badge)
            self._table.setCellWidget(row, 1, status_widget)

            # Expires
            expires_at = cookie.get("expires_at")
            if expires_at:
                try:
                    dt = datetime.fromisoformat(expires_at)
                    exp_text = dt.strftime("%Y-%m-%d %H:%M")
                except (ValueError, TypeError):
                    exp_text = str(expires_at)
            else:
                exp_text = "—"
            exp_item = QTableWidgetItem(exp_text)
            exp_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, 2, exp_item)

            # Provider
            provider_item = QTableWidgetItem(cookie.get("provider", ""))
            provider_item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, 3, provider_item)

            # Actions: refresh + delete
            cookie_id = cookie.get("id", "")
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)
            action_layout.setSpacing(4)
            action_layout.setAlignment(Qt.AlignCenter)

            refresh_btn = QPushButton("🔄")
            refresh_btn.setObjectName("cookie_action_btn")
            refresh_btn.setFixedSize(28, 28)
            refresh_btn.setCursor(QCursor(Qt.PointingHandCursor))
            refresh_btn.setToolTip("Check if cookie is still alive")
            refresh_btn.clicked.connect(
                lambda checked, cid=cookie_id, btn=refresh_btn: self._on_refresh_cookie(cid, btn)
            )
            action_layout.addWidget(refresh_btn)

            del_btn = QPushButton("🗑️")
            del_btn.setObjectName("cookie_action_btn")
            del_btn.setFixedSize(28, 28)
            del_btn.setCursor(QCursor(Qt.PointingHandCursor))
            del_btn.setToolTip(self.translator.t("cookie.delete"))
            del_btn.clicked.connect(
                lambda checked, cid=cookie_id: self._on_delete_cookie(cid)
            )
            action_layout.addWidget(del_btn)

            self._table.setCellWidget(row, 4, action_widget)

        # Update count
        self._count_label.setText(
            f"{self.translator.t('cookie.count')}: {len(cookies)}"
        )

    # ── Add cookie (test + save) ─────────────────────────────────────

    def _on_add_cookie(self):
        """Test and save cookie: POST /api-keys/test → POST /tools/token/frame/run."""
        value = self._value_input.toPlainText().strip()
        if not value:
            return

        if not self.cookie_api or not self._active_flow_id:
            self._show_status("⚠️ No active project selected or API not available", error=True)
            return

        self._show_status("🔄 Testing cookie before saving...", error=False)
        self._add_btn.setEnabled(False)
        self._add_btn.setText("⏳ Adding...")

        try:
            # Step 1: Test the cookie
            test_label = f"Test Cookie - {int(datetime.now().timestamp() * 1000)}"
            test_resp = self.cookie_api.test_cookie({
                "cookies": {
                    "__Secure-next-auth.session-token": value,
                    "__Host-next-auth.csrf-token": "dummy-csrf-token",
                },
                "label": test_label,
                "create_new": False,
                "timeout": 10,
                "flow_id": self._active_flow_id,
                "provider": PROVIDER,
            })

            if not test_resp.success:
                self._show_status(f"❌ Cookie test failed: {test_resp.message}", error=True)
                return

            # Extract user info for label
            info = test_resp.data.get("provider_info", {})
            user_email = info.get("user_email", "unknown")
            now_str = datetime.now().strftime("%-m/%-d/%Y, %I:%M:%S %p")
            save_label = f"{PROVIDER} - {user_email} - {now_str}"

            # Step 2: Save the cookie
            save_resp = self.cookie_api.save_cookie({
                "cookies": {
                    "__Secure-next-auth.session-token": value,
                    "__Host-next-auth.csrf-token": "dummy-csrf-token",
                },
                "label": save_label,
                "create_new": True,
                "flow_id": self._active_flow_id,
                "provider": PROVIDER,
            })

            if save_resp.success:
                # Step 3: Assign the api-key to the active flow
                api_key_data = save_resp.data.get("api_key", {})
                api_key_id = api_key_data.get("id")
                if api_key_id and self._active_flow_id:
                    assign_resp = self.cookie_api.assign_api_key_to_flow(
                        api_key_id=api_key_id,
                        flow_id=self._active_flow_id,
                    )
                    if not assign_resp.success:
                        logger.warning(f"assign_api_key_to_flow failed: {assign_resp.message}")

                self._show_status(
                    f"✅ Cookie saved! {save_label}",
                    error=False,
                )
                logger.info(f"save_cookie OK: {save_resp.message}")
                self._value_input.clear()
                self._load_cookies()
                self.cookies_changed.emit()
            else:
                self._show_status(f"❌ Save failed: {save_resp.message}", error=True)
                logger.warning(f"save_cookie failed: {save_resp.message}")

        except Exception as e:
            self._show_status(f"❌ Error: {e}", error=True)
            logger.error(f"add_cookie exception: {e}")
        finally:
            self._add_btn.setEnabled(True)
            self._add_btn.setText(f"➕ {self.translator.t('cookie.add_btn')}")

    # ── Refresh individual cookie ─────────────────────────────────────

    def _on_refresh_cookie(self, cookie_id: str, btn: QPushButton):
        """Re-test a single cookie to check if it's still alive."""
        if not self.cookie_api:
            return

        btn.setEnabled(False)
        btn.setText("⏳")
        btn.setToolTip("Checking...")

        try:
            # Call the server-side refresh/check endpoint
            resp = self.cookie_api.refresh_api_key(int(cookie_id))
            if resp.success:
                logger.info(f"refresh cookie {cookie_id}: alive")
            else:
                logger.warning(f"refresh cookie {cookie_id}: {resp.message}")
        except Exception as e:
            logger.error(f"refresh cookie {cookie_id} error: {e}")
        finally:
            btn.setEnabled(True)
            btn.setText("🔄")
            btn.setToolTip("Check if cookie is still alive")

        # Reload table to reflect updated status
        self._load_cookies()

    # ── Delete cookie ────────────────────────────────────────────────

    def _on_delete_cookie(self, cookie_id: str):
        """Delete a cookie via DELETE /api-keys/{id}."""
        if self.cookie_api:
            try:
                cid = int(cookie_id)
                resp = self.cookie_api.delete_api_key(cid)
                logger.info(f"delete_api_key({cid}) result: success={resp.success}")
            except (ValueError, TypeError):
                logger.warning(f"Invalid api-key ID for delete: {cookie_id}")
        else:
            self.api.delete_cookie(cookie_id)
        self._load_cookies()
        self.cookies_changed.emit()

    # ── Helpers ───────────────────────────────────────────────────────

    def _show_status(self, text: str, error: bool = False):
        """Show a status message below the input area."""
        self._status_label.setText(text)
        self._status_label.setStyleSheet(
            "color: #e74c3c; padding: 4px;" if error
            else "color: #27ae60; padding: 4px;"
        )
        self._status_label.setVisible(True)
