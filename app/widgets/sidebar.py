"""
Whisk Desktop — Sidebar Navigation Widget.

Supports expanded (icon + text) and collapsed (icon-only) modes.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap, QDesktopServices
import os


class Sidebar(QWidget):
    """Vertical sidebar with navigation buttons and collapse toggle."""

    page_changed = Signal(str)  # Emits page key, e.g. "image_creator"
    logout_clicked = Signal()

    NAV_ITEMS = [
        ("dashboard", "📊", "nav.dashboard"),
        ("image_creator", "🖼️", "nav.image_creator"),
        ("settings", "⚙️", "nav.settings"),
    ]

    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.translator.language_changed.connect(self.retranslate)
        self.setObjectName("sidebar")
        self._buttons: dict[str, QPushButton] = {}
        self._icons: dict[str, str] = {}
        self._active_page = "image_creator"
        self._collapsed = True
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo + Title row
        logo_row = QHBoxLayout()
        logo_row.setContentsMargins(12, 16, 12, 8)
        logo_row.setSpacing(10)
        logo_row.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # Logo with glow container
        logo_container = QWidget()
        logo_container.setObjectName("sidebar_logo_container")
        logo_container.setFixedSize(44, 44)
        logo_inner = QHBoxLayout(logo_container)
        logo_inner.setContentsMargins(2, 2, 2, 2)
        logo_inner.setAlignment(Qt.AlignCenter)

        self._logo = QLabel()
        self._logo.setObjectName("sidebar_logo")
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            self._logo.setPixmap(
                pixmap.scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        self._logo.setFixedSize(36, 36)
        logo_inner.addWidget(self._logo)
        logo_row.addWidget(logo_container)

        title_col = QVBoxLayout()
        title_col.setContentsMargins(0, 0, 0, 0)
        title_col.setSpacing(1)

        self._title = QLabel("Whisk")
        self._title.setObjectName("sidebar_title")
        title_col.addWidget(self._title)

        self._branding = QLabel("1 Nút Nhấn")
        self._branding.setObjectName("sidebar_branding")
        title_col.addWidget(self._branding)

        self._subtitle = QLabel(self.translator.t("app.version"))
        self._subtitle.setObjectName("sidebar_subtitle")
        title_col.addWidget(self._subtitle)

        logo_row.addLayout(title_col)
        layout.addLayout(logo_row)

        # Make logo area clickable
        from PySide6.QtCore import QUrl
        logo_container.setCursor(Qt.PointingHandCursor)
        logo_container.mousePressEvent = lambda ev: QDesktopServices.openUrl(
            QUrl("https://www.youtube.com/@KhuongDrama/videos")
        )

        # Navigation buttons
        for key, icon, label_key in self.NAV_ITEMS:
            btn = QPushButton(f"  {icon}  {self.translator.t(label_key)}")
            btn.setObjectName("nav_button")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self._on_nav_click(k))
            layout.addWidget(btn)
            self._buttons[key] = btn
            self._icons[key] = icon

        # Spacer
        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Collapse toggle button at bottom
        self._collapse_btn = QPushButton("« Thu gọn")
        self._collapse_btn.setObjectName("sidebar_collapse_btn")
        self._collapse_btn.setCursor(Qt.PointingHandCursor)
        self._collapse_btn.clicked.connect(self.toggle_collapse)
        layout.addWidget(self._collapse_btn)

        # Logout button at very bottom
        self._logout_btn = QPushButton(f"🚪 {self.translator.t('login.logout')}")
        self._logout_btn.setObjectName("sidebar_logout_btn")
        self._logout_btn.setCursor(Qt.PointingHandCursor)
        self._logout_btn.clicked.connect(self.logout_clicked.emit)
        layout.addWidget(self._logout_btn)

        # Set initial active
        self._update_active_state()
        self._apply_collapse_state()

    def toggle_collapse(self):
        """Toggle between expanded and collapsed states."""
        self._collapsed = not self._collapsed
        self._apply_collapse_state()

    def _apply_collapse_state(self):
        """Apply collapsed or expanded visual state."""
        if self._collapsed:
            # Remove min/max first, then set fixed
            self.setMinimumWidth(0)
            self.setMaximumWidth(16777215)
            self.setFixedWidth(64)

            self._title.setVisible(False)
            self._subtitle.setVisible(False)
            self._branding.setVisible(False)

            for key, icon, label_key in self.NAV_ITEMS:
                btn = self._buttons[key]
                btn.setText(icon)
                btn.setProperty("collapsed", True)
                btn.style().unpolish(btn)
                btn.style().polish(btn)

            self._collapse_btn.setText("»")
            self._collapse_btn.setProperty("collapsed", True)
            self._collapse_btn.style().unpolish(self._collapse_btn)
            self._collapse_btn.style().polish(self._collapse_btn)
            self._collapse_btn.setToolTip(self.translator.t("nav.expand_sidebar"))

            self._logout_btn.setText("🚪")
            self._logout_btn.setProperty("collapsed", True)
            self._logout_btn.style().unpolish(self._logout_btn)
            self._logout_btn.style().polish(self._logout_btn)
            self._logout_btn.setToolTip(self.translator.t('login.logout'))
        else:
            # Remove fixed first, then set min/max
            self.setMinimumWidth(200)
            self.setMaximumWidth(200)

            self._title.setVisible(True)
            self._title.setText("Whisk")
            self._title.setProperty("collapsed", False)
            self._title.style().unpolish(self._title)
            self._title.style().polish(self._title)

            self._subtitle.setVisible(True)
            self._branding.setVisible(True)

            for key, icon, label_key in self.NAV_ITEMS:
                btn = self._buttons[key]
                btn.setText(f"  {icon}  {self.translator.t(label_key)}")
                btn.setProperty("collapsed", False)
                btn.style().unpolish(btn)
                btn.style().polish(btn)

            self._collapse_btn.setText(f"« {self.translator.t('nav.collapse_sidebar')}")
            self._collapse_btn.setProperty("collapsed", False)
            self._collapse_btn.style().unpolish(self._collapse_btn)
            self._collapse_btn.style().polish(self._collapse_btn)
            self._collapse_btn.setToolTip("")

            self._logout_btn.setText(f"🚪 {self.translator.t('login.logout')}")
            self._logout_btn.setProperty("collapsed", False)
            self._logout_btn.style().unpolish(self._logout_btn)
            self._logout_btn.style().polish(self._logout_btn)
            self._logout_btn.setToolTip("")

    def _on_nav_click(self, page_key: str):
        """Handle navigation button click."""
        self._active_page = page_key
        self._update_active_state()
        self.page_changed.emit(page_key)

    def _update_active_state(self):
        """Update button active property for styling."""
        for key, btn in self._buttons.items():
            is_active = key == self._active_page
            btn.setProperty("active", is_active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def set_active_page(self, page_key: str):
        """Programmatically set the active page."""
        self._active_page = page_key
        self._update_active_state()

    def retranslate(self):
        """Update all text when language changes."""
        self._subtitle.setText(self.translator.t("app.version"))
        if not self._collapsed:
            for key, icon, label_key in self.NAV_ITEMS:
                self._buttons[key].setText(f"  {icon}  {self.translator.t(label_key)}")
            self._collapse_btn.setText(f"« {self.translator.t('nav.collapse_sidebar')}")
        else:
            self._collapse_btn.setToolTip(self.translator.t("nav.expand_sidebar"))
