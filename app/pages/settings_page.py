"""
Whisk Desktop — Settings Page.

Polished settings with card-based sections, emoji labels, and
dynamic user profile data from the /auth/me API.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QRadioButton, QButtonGroup, QComboBox, QScrollArea,
    QGridLayout,
)
from PySide6.QtCore import Signal, Qt
from app.widgets.toggle_switch import ToggleSwitch


class SettingsPage(QWidget):
    """Settings page for theme, language, and account preferences."""

    theme_change_requested = Signal(str)   # "light" or "dark"
    language_change_requested = Signal(str)  # "en" or "vi"

    # ── Init ──────────────────────────────────────────────────────────
    def __init__(self, translator, theme_manager, auth_manager=None, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.theme_manager = theme_manager
        self.auth_manager = auth_manager
        self.translator.language_changed.connect(self.retranslate)
        self._user_value_labels = {}       # idx → QLabel for user info rows
        self._setup_ui()

        if self.auth_manager and self.auth_manager.is_logged_in:
            self.refresh_user_info()

    # ── UI Setup ──────────────────────────────────────────────────────
    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setObjectName("settings_scroll")

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(28, 28, 28, 28)
        cl.setSpacing(24)

        # Page title
        self._title = QLabel(self.translator.t("settings.title"))
        self._title.setObjectName("settings_page_title")
        cl.addWidget(self._title)

        # ── 🎨 Appearance Card ────────────────────────────────────────
        cl.addWidget(self._build_appearance_card())

        # ── 📋 About Card ─────────────────────────────────────────────
        cl.addWidget(self._build_about_card())

        # ── 👤 Account Card ───────────────────────────────────────────
        cl.addWidget(self._build_account_card())

        cl.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll)

    # ══════════════════════════════════════════════════════════════════
    #  Card builders
    # ══════════════════════════════════════════════════════════════════

    def _build_appearance_card(self) -> QFrame:
        card = self._card()
        layout = card.layout()

        # Card header
        self._appearance_header = QLabel(f"🎨  {self.translator.t('settings.appearance')}")
        self._appearance_header.setObjectName("settings_card_header")
        layout.addWidget(self._appearance_header)

        # Grid for theme + language
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(14)

        # ── Theme row ─────────────────
        self._theme_label = QLabel(f"🌗  {self.translator.t('settings.theme')}")
        self._theme_label.setObjectName("settings_row_label")
        grid.addWidget(self._theme_label, 0, 0)

        theme_box = QHBoxLayout()
        theme_box.setSpacing(12)
        self._theme_group = QButtonGroup(self)
        self._light_radio = QRadioButton(f"☀️ {self.translator.t('settings.theme_light')}")
        self._dark_radio = QRadioButton(f"🌙 {self.translator.t('settings.theme_dark')}")
        self._theme_group.addButton(self._light_radio, 0)
        self._theme_group.addButton(self._dark_radio, 1)
        (self._dark_radio if self.theme_manager.is_dark else self._light_radio).setChecked(True)
        self._theme_group.idClicked.connect(self._on_theme_change)
        theme_box.addWidget(self._light_radio)
        theme_box.addWidget(self._dark_radio)
        theme_box.addStretch()
        grid.addLayout(theme_box, 0, 1)

        # ── Language row ──────────────
        self._lang_label = QLabel(f"🌐  {self.translator.t('settings.language')}")
        self._lang_label.setObjectName("settings_row_label")
        grid.addWidget(self._lang_label, 1, 0)

        self._lang_combo = QComboBox()
        self._lang_combo.setMinimumWidth(140)
        for lc in self.translator.available_languages:
            flag = "🇻🇳" if lc == "vi" else "🇺🇸"
            label = self.translator.LANGUAGE_LABELS.get(lc, lc)
            self._lang_combo.addItem(f"{flag} {label}", lc)
        idx = self.translator.available_languages.index(self.translator.current_language)
        self._lang_combo.setCurrentIndex(idx)
        self._lang_combo.currentIndexChanged.connect(self._on_language_change)
        lang_wrap = QHBoxLayout()
        lang_wrap.addWidget(self._lang_combo)
        lang_wrap.addStretch()
        grid.addLayout(lang_wrap, 1, 1)

        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)
        return card

    # ──────────────────────────────────────────────────────────────────
    def _build_about_card(self) -> QFrame:
        card = self._card()
        layout = card.layout()

        self._about_header = QLabel(f"📋  {self.translator.t('settings.about')}")
        self._about_header.setObjectName("settings_card_header")
        layout.addWidget(self._about_header)

        # Static info grid
        info_rows = [
            ("🧩", self.translator.t("about.version"), self.translator.t("app.version"), None),
            ("👤", self.translator.t("about.owner"), "Nguyễn Khương", None),
            ("📞", self.translator.t("about.phone"), "0356241963", "tel:0356241963"),
            ("💬", self.translator.t("about.support_group"),
             self.translator.t("about.support_group_text"), "https://zalo.me/g/newwww890"),
            ("🏆", self.translator.t("about.portfolio"),
             self.translator.t("about.portfolio_text"), "https://khuongsatou.github.io/whisk_policy/"),
            ("⚖️", self.translator.t("about.policy"),
             "Privacy Policy", "https://khuongsatou.github.io/whisk_policy/privacy-policy.html"),
        ]

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(6)
        for r, (icon, lbl, val, link) in enumerate(info_rows):
            key_lbl = QLabel(f"{icon}  {lbl}")
            key_lbl.setObjectName("about_meta_label")
            grid.addWidget(key_lbl, r, 0)
            grid.addWidget(self._value_label(val, link), r, 1)

        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)
        return card

    # ──────────────────────────────────────────────────────────────────
    def _build_account_card(self) -> QFrame:
        card = self._card()
        layout = card.layout()

        self._account_header = QLabel(f"👤  {self.translator.t('about.account')}")
        self._account_header.setObjectName("settings_card_header")
        layout.addWidget(self._account_header)

        # Dynamic user-info grid
        user_fields = [
            ("✉️",  self.translator.t("about.email"),    "mail"),
            ("🏷️",  self.translator.t("about.username"), "username"),
            ("🛡️",  self.translator.t("about.role"),     "roles"),
            ("🔄",  self.translator.t("about.status"),   "status"),
            ("💳",  self.translator.t("about.credit"),   "credit"),
            ("🧰",  self.translator.t("about.tools"),    "tools_access"),
            ("🕒",  self.translator.t("about.updated"),  "updated_at"),
        ]

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(6)

        self._user_field_defs = []
        for r, (icon, lbl, key) in enumerate(user_fields):
            key_lbl = QLabel(f"{icon}  {lbl}")
            key_lbl.setObjectName("about_meta_label")
            grid.addWidget(key_lbl, r, 0)
            val_lbl = self._value_label("—")
            grid.addWidget(val_lbl, r, 1)
            self._user_value_labels[r] = val_lbl
            self._user_field_defs.append((icon, lbl, key))

        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)

        # Separator
        layout.addWidget(self._separator())

        # Use-credit toggle
        credit_row = QHBoxLayout()
        credit_row.setSpacing(10)
        self._credit_label = QLabel(f"💳  {self.translator.t('about.use_credit')}")
        self._credit_label.setObjectName("settings_row_label")
        credit_row.addWidget(self._credit_label)
        credit_row.addStretch()
        self._use_credit_toggle = ToggleSwitch()
        self._use_credit_toggle.toggled.connect(self._on_use_credit_toggled)
        credit_row.addWidget(self._use_credit_toggle)
        layout.addLayout(credit_row)

        return card

    # ══════════════════════════════════════════════════════════════════
    #  Helpers
    # ══════════════════════════════════════════════════════════════════

    def _card(self) -> QFrame:
        """Return a styled card frame."""
        f = QFrame()
        f.setObjectName("settings_card")
        v = QVBoxLayout(f)
        v.setContentsMargins(20, 18, 20, 18)
        v.setSpacing(14)
        return f

    @staticmethod
    def _separator() -> QFrame:
        s = QFrame()
        s.setObjectName("about_separator")
        s.setFrameShape(QFrame.HLine)
        s.setFixedHeight(1)
        return s

    @staticmethod
    def _value_label(text: str, link: str = None) -> QLabel:
        if link:
            lbl = QLabel(f'<a href="{link}" style="text-decoration:none;">{text}</a>')
            lbl.setObjectName("about_meta_link")
            lbl.setOpenExternalLinks(True)
            lbl.setCursor(Qt.PointingHandCursor)
        else:
            lbl = QLabel(str(text))
            lbl.setObjectName("about_meta_value")
        lbl.setWordWrap(True)
        return lbl

    # ══════════════════════════════════════════════════════════════════
    #  Data refresh
    # ══════════════════════════════════════════════════════════════════

    def refresh_user_info(self):
        """Fetch user info from API and update dynamic labels."""
        if not self.auth_manager or not self.auth_manager.is_logged_in:
            return
        self.auth_manager.fetch_user_info()
        session = self.auth_manager.session
        if not session:
            return

        for i, (_icon, _lbl, key) in enumerate(self._user_field_defs):
            val_label = self._user_value_labels.get(i)
            if not val_label:
                continue
            value = getattr(session, key, "—")
            if key == "tools_access" and isinstance(value, dict):
                enabled = [k for k, v in value.items() if v]
                value = ", ".join(enabled) if enabled else "—"
            elif key == "credit":
                value = f"{value:,}" if isinstance(value, (int, float)) else str(value)
            else:
                value = str(value) if value else "—"
            val_label.setText(value)

        # Sync toggle
        self._use_credit_toggle.blockSignals(True)
        self._use_credit_toggle.setChecked(session.use_credit)
        self._use_credit_toggle.blockSignals(False)

    # ══════════════════════════════════════════════════════════════════
    #  Slots
    # ══════════════════════════════════════════════════════════════════

    def _on_use_credit_toggled(self, checked: bool):
        if not self.auth_manager or not self.auth_manager.is_logged_in:
            return
        ok, _msg = self.auth_manager.update_user(use_credit=checked)
        if not ok:
            self._use_credit_toggle.blockSignals(True)
            self._use_credit_toggle.setChecked(not checked)
            self._use_credit_toggle.blockSignals(False)

    def _on_theme_change(self, button_id: int):
        self.theme_change_requested.emit("dark" if button_id == 1 else "light")

    def _on_language_change(self, index: int):
        lang_code = self._lang_combo.itemData(index)
        if lang_code and lang_code != self.translator.current_language:
            self.language_change_requested.emit(lang_code)

    def update_theme_state(self):
        (self._dark_radio if self.theme_manager.is_dark else self._light_radio).setChecked(True)

    # ══════════════════════════════════════════════════════════════════
    #  i18n
    # ══════════════════════════════════════════════════════════════════

    def retranslate(self):
        self._title.setText(self.translator.t("settings.title"))
        self._appearance_header.setText(f"🎨  {self.translator.t('settings.appearance')}")
        self._theme_label.setText(f"🌗  {self.translator.t('settings.theme')}")
        self._light_radio.setText(f"☀️ {self.translator.t('settings.theme_light')}")
        self._dark_radio.setText(f"🌙 {self.translator.t('settings.theme_dark')}")
        self._lang_label.setText(f"🌐  {self.translator.t('settings.language')}")
        self._about_header.setText(f"📋  {self.translator.t('settings.about')}")
        self._account_header.setText(f"👤  {self.translator.t('about.account')}")
        self._credit_label.setText(f"💳  {self.translator.t('about.use_credit')}")
