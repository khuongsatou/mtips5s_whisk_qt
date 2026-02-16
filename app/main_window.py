"""
Whisk Desktop — Main Window.

Central window: Sidebar | Header + TabBar + Content.
Each project is a tab with its own ImageCreatorPage running in parallel.
"""
import json
import logging
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget,
)
from PySide6.QtCore import Qt
from app.widgets.sidebar import Sidebar
from app.widgets.header import Header
from app.widgets.project_tab_bar import ProjectTabBar
from app.widgets.cookie_manager_dialog import CookieManagerDialog
from app.widgets.project_manager_dialog import ProjectManagerDialog
from app.widgets.token_manager_dialog import TokenManagerDialog
from app.pages.image_creator_page import ImageCreatorPage
from app.pages.settings_page import SettingsPage

logger = logging.getLogger("whisk")

TABS_FILE = os.path.join(os.path.expanduser("~"), ".whisk_open_tabs.json")


class MainWindow(QMainWindow):
    """Main application window with sidebar navigation and tabbed content."""

    PAGE_TITLES = {
        "image_creator": "nav.image_creator",
        "settings": "nav.settings",
    }

    def __init__(self, theme_manager, translator, api, auth_manager=None,
                 flow_api=None, cookie_api=None, workflow_api=None):
        super().__init__()
        self.theme_manager = theme_manager
        self.translator = translator
        self.api = api
        self.auth_manager = auth_manager
        self.flow_api = flow_api
        self.cookie_api = cookie_api
        self.workflow_api = workflow_api

        # Per-tab data: list of {flow_id, flow_name, page}
        self._project_tabs: list[dict] = []

        self.setWindowTitle(self.translator.t("app.title"))
        self.setMinimumSize(900, 600)

        self._setup_ui()
        self._connect_signals()
        self._apply_theme()
        self._sidebar._apply_collapse_state()

    def _setup_ui(self):
        """Build: Sidebar | (Header + TabBar + Content)."""
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self._sidebar = Sidebar(self.translator)
        main_layout.addWidget(self._sidebar)

        # Right panel
        right_panel = QVBoxLayout()
        right_panel.setContentsMargins(0, 0, 0, 0)
        right_panel.setSpacing(0)

        # Header
        self._header = Header(self.translator, self.theme_manager)
        right_panel.addWidget(self._header)

        # Tab bar (below header, only for image_creator page)
        self._tab_bar = ProjectTabBar()
        right_panel.addWidget(self._tab_bar)

        # Content stack — holds tab pages + settings
        self._tab_stack = QStackedWidget()
        self._tab_stack.setObjectName("tab_content_stack")

        # Settings page is always the LAST widget in the stack
        self._settings = SettingsPage(self.translator, self.theme_manager, self.auth_manager)
        self._settings_index = 0
        self._tab_stack.addWidget(self._settings)  # Will be re-indexed as tabs are added

        right_panel.addWidget(self._tab_stack, 1)
        main_layout.addLayout(right_panel, 1)

        # Start on image creator view (tabs)
        self._current_page = "image_creator"
        self._tab_bar.setVisible(True)

    def _connect_signals(self):
        """Wire up all signals."""
        self._sidebar.page_changed.connect(self._switch_page)
        self._header.theme_toggled.connect(self._on_theme_toggle)
        self._header.language_changed.connect(self._on_language_change)
        self._header.cookies_clicked.connect(self._on_cookies_clicked)
        self._header.projects_clicked.connect(self._on_projects_clicked)
        self._header.tokens_clicked.connect(self._on_tokens_clicked)
        self._sidebar.logout_clicked.connect(self._on_logout)
        self._settings.theme_change_requested.connect(self._on_theme_set)
        self._settings.language_change_requested.connect(self._on_language_change)
        self.theme_manager.theme_changed.connect(self._on_theme_applied)
        self.translator.language_changed.connect(self._on_language_applied)

        # Tab bar signals
        self._tab_bar.tab_changed.connect(self._on_tab_changed)
        self._tab_bar.tab_close_requested.connect(self._on_tab_close)
        self._tab_bar.new_tab_requested.connect(self._on_new_tab)

        # Load tabs from disk or server
        self._load_tabs()

        # Show logged-in user in header
        if self.auth_manager and self.auth_manager.is_logged_in:
            self._header.set_user_info(self.auth_manager.session.name)

        # Update header & cookie button for initial state
        self._update_header_for_current_tab()

    # ── Page switching ───────────────────────────────────────────────

    def _switch_page(self, page_key: str):
        """Switch between image_creator (tabs) and settings."""
        self._current_page = page_key
        title_key = self.PAGE_TITLES.get(page_key, page_key)
        self._header.set_page_title(self.translator.t(title_key))

        if page_key == "settings":
            self._tab_bar.setVisible(False)
            self._tab_stack.setCurrentWidget(self._settings)
        else:
            # Show tab bar and restore active tab
            self._tab_bar.setVisible(True)
            idx = self._tab_bar.active_index()
            if 0 <= idx < len(self._project_tabs):
                self._tab_stack.setCurrentWidget(self._project_tabs[idx]["page"])
                self._project_tabs[idx]["page"].refresh_data()

    # ── Tab management ───────────────────────────────────────────────

    def _add_project_tab(self, flow_id: str, flow_name: str, switch_to: bool = True) -> int:
        """Create a new tab with its own ImageCreatorPage."""
        # Check if tab already exists
        existing = self._tab_bar.find_tab_by_flow_id(flow_id)
        if existing >= 0:
            if switch_to:
                self._tab_bar.set_active_tab(existing)
            return existing

        # Create a per-project MockApi so each tab has its own queue/checkpoint
        from app.api.mock_api import MockApi
        tab_api = MockApi(flow_id=flow_id)

        # Create a new ImageCreatorPage for this tab
        page = ImageCreatorPage(
            self.translator, tab_api,
            workflow_api=self.workflow_api,
            cookie_api=self.cookie_api,
            active_flow_id=int(flow_id) if flow_id else None,
            flow_name=flow_name,
        )

        # Add to stack (before settings)
        stack_index = self._tab_stack.count() - 1  # Before settings
        self._tab_stack.insertWidget(stack_index, page)

        # Track tab data
        self._project_tabs.append({
            "flow_id": str(flow_id),
            "flow_name": flow_name,
            "page": page,
        })

        # Add to tab bar
        tab_index = self._tab_bar.add_tab(str(flow_id), flow_name)

        logger.info(f"📑 Added tab: {flow_name} (flow_id={flow_id})")

        # Persist
        self._save_tabs()

        return tab_index

    def _on_tab_changed(self, index: int):
        """Handle tab switch — show the corresponding page."""
        if 0 <= index < len(self._project_tabs):
            page = self._project_tabs[index]["page"]
            self._tab_stack.setCurrentWidget(page)
            page.refresh_data()
            self._update_header_for_current_tab()
            self._save_tabs()

    def _on_tab_close(self, index: int):
        """Handle tab close — remove page and tab."""
        if index < 0 or index >= len(self._project_tabs):
            return

        tab_data = self._project_tabs.pop(index)
        page = tab_data["page"]

        # Remove from stack
        self._tab_stack.removeWidget(page)
        page.deleteLater()

        # Remove from tab bar
        self._tab_bar.remove_tab(index)

        logger.info(f"❎ Closed tab: {tab_data['flow_name']} (flow_id={tab_data['flow_id']})")

        # Update header
        self._update_header_for_current_tab()

        # Persist
        self._save_tabs()

    def _on_new_tab(self):
        """Handle "+" button — open project picker dialog."""
        flow_id = self._get_active_flow_id()
        dialog = ProjectManagerDialog(
            self.api, self.translator, self,
            flow_api=self.flow_api,
            cookie_api=self.cookie_api,
            active_flow_id=flow_id,
        )
        dialog.project_activated_with_id.connect(self._on_project_selected_for_tab)
        dialog.exec()

    def _on_project_selected_for_tab(self, project_id: str, project_name: str):
        """Callback when a project is selected from the dialog → open as tab."""
        self._add_project_tab(project_id, project_name, switch_to=True)
        self._header.set_active_project_name(project_name)

    def _update_header_for_current_tab(self):
        """Update header based on the currently active tab."""
        idx = self._tab_bar.active_index()
        if 0 <= idx < len(self._project_tabs):
            tab = self._project_tabs[idx]
            self._header.set_active_project_name(tab["flow_name"])
            self._header.set_cookie_btn_visible(True)
        else:
            self._header.set_active_project_name("")
            self._header.set_cookie_btn_visible(False)

    def _get_active_flow_id(self) -> str | None:
        """Get flow_id of the currently active tab."""
        idx = self._tab_bar.active_index()
        if 0 <= idx < len(self._project_tabs):
            return self._project_tabs[idx]["flow_id"]
        return None

    # ── Persistence ──────────────────────────────────────────────────

    def _save_tabs(self):
        """Save open tabs and active index to disk."""
        try:
            data = {
                "tabs": self._tab_bar.all_tabs_data(),
                "active_index": self._tab_bar.active_index(),
            }
            with open(TABS_FILE, "w") as f:
                json.dump(data, f)
            logger.debug(f"💾 Saved {len(data['tabs'])} tabs to {TABS_FILE}")
        except IOError as e:
            logger.warning(f"⚠️ Failed to save tabs: {e}")

    def _load_tabs(self):
        """Load tabs from disk, or fetch from server if none saved."""
        loaded = False

        # Try loading from disk
        try:
            if os.path.exists(TABS_FILE):
                with open(TABS_FILE, "r") as f:
                    data = json.load(f)
                tabs = data.get("tabs", [])
                active_idx = data.get("active_index", 0)

                if tabs:
                    for t in tabs:
                        fid = t.get("flow_id", "")
                        fname = t.get("flow_name", "")
                        if fid:
                            self._add_project_tab(str(fid), fname, switch_to=False)
                    # Restore active tab
                    if 0 <= active_idx < len(self._project_tabs):
                        self._tab_bar.set_active_tab(active_idx)
                    elif self._project_tabs:
                        self._tab_bar.set_active_tab(0)
                    loaded = True
                    logger.info(f"📂 Restored {len(tabs)} tabs from disk")
        except (json.JSONDecodeError, IOError, KeyError) as e:
            logger.warning(f"⚠️ Failed to load tabs: {e}")

        # No saved tabs → fetch from server
        if not loaded and self.flow_api:
            try:
                resp = self.flow_api.get_flows(flow_type="WHISK")
                if resp.success and resp.data:
                    items = resp.data.get("items", [])
                    if items:
                        # Open first project as a tab
                        first = items[0]
                        self._add_project_tab(
                            str(first.get("id", "")),
                            first.get("name", ""),
                            switch_to=True,
                        )
                        loaded = True
            except Exception as e:
                logger.warning(f"⚠️ Failed to fetch projects: {e}")

        if not loaded:
            self._header.set_cookie_btn_visible(False)

    # ── Theme / Language / Dialogs ───────────────────────────────────

    def _on_theme_toggle(self):
        self.theme_manager.toggle_theme()

    def _on_theme_set(self, theme: str):
        self.theme_manager.set_theme(theme)

    def _on_theme_applied(self, theme: str):
        self._apply_theme()
        self._header.update_theme_button()
        self._settings.update_theme_state()
        self._sidebar._apply_collapse_state()

    def _on_language_change(self, lang_code: str):
        self.translator.set_language(lang_code)

    def _on_language_applied(self, lang_code: str):
        self.setWindowTitle(self.translator.t("app.title"))
        if self._current_page:
            title_key = self.PAGE_TITLES.get(self._current_page, self._current_page)
            self._header.set_page_title(self.translator.t(title_key))

    def _apply_theme(self):
        qss = self.theme_manager.get_stylesheet()
        self.setStyleSheet(qss)

    def _on_cookies_clicked(self):
        """Open cookie manager for the active tab's flow."""
        flow_id = self._get_active_flow_id()
        dialog = CookieManagerDialog(
            self.api, self.translator, self,
            cookie_api=self.cookie_api,
            active_flow_id=int(flow_id) if flow_id else None,
        )
        dialog.exec()

    def _on_projects_clicked(self):
        """Open project manager — selecting a project opens it as a tab."""
        flow_id = self._get_active_flow_id()
        dialog = ProjectManagerDialog(
            self.api, self.translator, self,
            flow_api=self.flow_api,
            cookie_api=self.cookie_api,
            active_flow_id=flow_id,
        )
        dialog.project_activated.connect(self._header.set_active_project_name)
        dialog.project_activated_with_id.connect(self._on_project_selected_for_tab)
        dialog.exec()

    def _on_tokens_clicked(self):
        dialog = TokenManagerDialog(self.api, self.translator, self)
        dialog.exec()

    def _on_logout(self):
        """Handle logout: clear session and restart app."""
        if self.auth_manager:
            self.auth_manager.logout()
        from PySide6.QtWidgets import QApplication
        QApplication.instance().exit(42)
