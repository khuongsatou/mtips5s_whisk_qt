"""
Whisk Desktop — Header Widget.

Responsive header bar with page title, user info, navigation buttons,
theme toggle, and language switcher. Wraps content to prevent overflow.
"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QSizePolicy,
)
from PySide6.QtCore import Signal, Qt


class Header(QWidget):
    """Header bar with page title, theme toggle, and language switcher."""

    theme_toggled = Signal()
    language_changed = Signal(str)
    cookies_clicked = Signal()
    projects_clicked = Signal()
    tokens_clicked = Signal()

    def __init__(self, translator, theme_manager, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.theme_manager = theme_manager
        self.translator.language_changed.connect(self.retranslate)
        self.setObjectName("header")
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(6)

        # Page title (set dynamically)
        self._page_title = QLabel("")
        self._page_title.setObjectName("header_title")
        self._page_title.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        layout.addWidget(self._page_title)

        layout.addStretch()

        # Active project label
        self._active_project_label = QLabel("")
        self._active_project_label.setObjectName("active_project_label")
        self._active_project_label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        layout.addWidget(self._active_project_label)

        # Projects button
        self._projects_btn = QPushButton("📂")
        self._projects_btn.setObjectName("project_header_btn")
        self._projects_btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self._projects_btn.setCursor(Qt.PointingHandCursor)
        self._projects_btn.setToolTip(self.translator.t('project.header_btn'))
        self._projects_btn.clicked.connect(self.projects_clicked.emit)
        layout.addWidget(self._projects_btn)

        # Cookies button (hidden until a project is activated)
        self._cookies_btn = QPushButton("🍪")
        self._cookies_btn.setObjectName("cookie_header_btn")
        self._cookies_btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self._cookies_btn.setCursor(Qt.PointingHandCursor)
        self._cookies_btn.setToolTip(self.translator.t('cookie.header_btn'))
        self._cookies_btn.clicked.connect(self.cookies_clicked.emit)
        self._cookies_btn.setVisible(False)
        layout.addWidget(self._cookies_btn)

        # Tokens button
        self._tokens_btn = QPushButton("🔑")
        self._tokens_btn.setObjectName("token_header_btn")
        self._tokens_btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self._tokens_btn.setCursor(Qt.PointingHandCursor)
        self._tokens_btn.setToolTip(self.translator.t('token.header_btn'))
        self._tokens_btn.clicked.connect(self.tokens_clicked.emit)
        self._tokens_btn.setVisible(False)  # Hidden for now, re-enable later
        layout.addWidget(self._tokens_btn)

        # Separator
        layout.addSpacing(8)

        # User info label
        self._user_label = QLabel("")
        self._user_label.setObjectName("header_user_label")
        self._user_label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        layout.addWidget(self._user_label)


        # Theme toggle button
        self._theme_btn = QPushButton(self._theme_label())
        self._theme_btn.setObjectName("theme_toggle")
        self._theme_btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self._theme_btn.clicked.connect(self._on_theme_toggle)
        layout.addWidget(self._theme_btn)

        # Language combo
        self._lang_combo = QComboBox()
        self._lang_combo.setObjectName("language_combo")
        self._lang_combo.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        for lang_code in self.translator.available_languages:
            flag = {"en": "🇺🇸", "vi": "🇻🇳"}.get(lang_code, lang_code)
            self._lang_combo.addItem(flag, lang_code)
        # Set current index
        idx = self.translator.available_languages.index(self.translator.current_language)
        self._lang_combo.setCurrentIndex(idx)
        self._lang_combo.currentIndexChanged.connect(self._on_language_change)
        layout.addWidget(self._lang_combo)

    def _theme_label(self) -> str:
        """Get the theme toggle button label."""
        if self.theme_manager.is_dark:
            return "☀️"
        return "🌙"

    def _on_theme_toggle(self):
        """Handle theme toggle click."""
        self.theme_toggled.emit()
        self._theme_btn.setText(self._theme_label())

    def _on_language_change(self, index: int):
        """Handle language dropdown change."""
        lang_code = self._lang_combo.itemData(index)
        if lang_code and lang_code != self.translator.current_language:
            self.language_changed.emit(lang_code)

    def set_page_title(self, title: str):
        """Update the page title in the header."""
        self._page_title.setText(title)

    def update_theme_button(self):
        """Update theme button text after theme change."""
        self._theme_btn.setText(self._theme_label())

    def retranslate(self):
        """Update text when language changes."""
        self._theme_btn.setText(self._theme_label())
        self._cookies_btn.setToolTip(self.translator.t('cookie.header_btn'))
        self._projects_btn.setToolTip(self.translator.t('project.header_btn'))
        self._tokens_btn.setToolTip(self.translator.t('token.header_btn'))

    def set_active_project_name(self, name: str):
        """Update the active project label in the header."""
        if name:
            self._active_project_label.setText(f"⭐ {name}")
        else:
            self._active_project_label.setText("")

    def set_user_info(self, name: str):
        """Set the logged-in user display name."""
        if name:
            self._user_label.setText(f"👤 {name}")
        else:
            self._user_label.setText("")

    def set_cookie_btn_visible(self, visible: bool):
        """Show/hide the cookie button."""
        self._cookies_btn.setVisible(visible)
