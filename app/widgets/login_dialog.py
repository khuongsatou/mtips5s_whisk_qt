"""
Whisk Desktop — Login Dialog.

Modal dialog for authenticating with a key_code.
Shows user info on success, with remember-me persistence.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QWidget, QFrame,
)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QPixmap, QDesktopServices
import os


class LoginDialog(QDialog):
    """Login modal with key_code input and status feedback."""

    login_success = Signal(object)  # Emits UserSession

    def __init__(self, auth_manager, translator, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.translator = translator
        self.setObjectName("login_dialog")
        self.setWindowTitle(self.translator.t("login.title"))
        self.setFixedSize(420, 420)
        self.setWindowFlags(
            Qt.Dialog | Qt.WindowCloseButtonHint | Qt.MSWindowsFixedSizeDialogHint
        )
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(0)

        # Logo + Title
        header_layout = QVBoxLayout()
        header_layout.setAlignment(Qt.AlignCenter)
        header_layout.setSpacing(8)

        logo_label = QLabel()
        logo_label.setObjectName("login_logo")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "assets", "logo.png"
        )
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            logo_label.setPixmap(
                pixmap.scaled(56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        logo_label.setFixedSize(64, 64)
        header_layout.addWidget(logo_label, 0, Qt.AlignCenter)

        title = QLabel(self.translator.t("login.title"))
        title.setObjectName("login_title")
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)

        subtitle = QLabel(self.translator.t("login.subtitle"))
        subtitle.setObjectName("login_subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        header_layout.addWidget(subtitle)

        layout.addLayout(header_layout)
        layout.addSpacing(20)

        # Key Code Input
        input_label = QLabel(self.translator.t("login.key_label"))
        input_label.setObjectName("login_input_label")
        layout.addWidget(input_label)
        layout.addSpacing(4)

        self._key_input = QLineEdit()
        self._key_input.setObjectName("login_input")
        self._key_input.setPlaceholderText(self.translator.t("login.key_placeholder"))
        self._key_input.setText("wuBL8k31tk")  # TODO: remove after testing
        self._key_input.setEchoMode(QLineEdit.Password)
        self._key_input.returnPressed.connect(self._on_login)
        layout.addWidget(self._key_input)

        # Show/hide toggle
        show_row = QHBoxLayout()
        show_row.setContentsMargins(0, 4, 0, 0)
        self._show_btn = QPushButton(self.translator.t("login.show_key"))
        self._show_btn.setObjectName("login_show_btn")
        self._show_btn.setCheckable(True)
        self._show_btn.setCursor(Qt.PointingHandCursor)
        self._show_btn.toggled.connect(self._on_toggle_visibility)
        show_row.addStretch()
        show_row.addWidget(self._show_btn)
        layout.addLayout(show_row)

        layout.addSpacing(16)

        # Status message
        self._status_label = QLabel("")
        self._status_label.setObjectName("login_status")
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setWordWrap(True)
        self._status_label.setVisible(False)
        layout.addWidget(self._status_label)

        # Login button
        self._login_btn = QPushButton(f"🔑 {self.translator.t('login.button')}")
        self._login_btn.setObjectName("login_btn")
        self._login_btn.setCursor(Qt.PointingHandCursor)
        self._login_btn.setFixedHeight(42)
        self._login_btn.clicked.connect(self._on_login)
        layout.addWidget(self._login_btn)

        # Forgot key code link
        layout.addSpacing(12)
        self._forgot_btn = QPushButton(self.translator.t("login.forgot_key"))
        self._forgot_btn.setObjectName("login_forgot_btn")
        self._forgot_btn.setCursor(Qt.PointingHandCursor)
        self._forgot_btn.setFlat(True)
        self._forgot_btn.clicked.connect(self._on_forgot_key)
        layout.addWidget(self._forgot_btn, 0, Qt.AlignCenter)

        layout.addStretch()

    def _on_toggle_visibility(self, checked):
        if checked:
            self._key_input.setEchoMode(QLineEdit.Normal)
            self._show_btn.setText(self.translator.t("login.hide_key"))
        else:
            self._key_input.setEchoMode(QLineEdit.Password)
            self._show_btn.setText(self.translator.t("login.show_key"))

    def _on_login(self):
        key_code = self._key_input.text().strip()
        if not key_code:
            self._show_status(self.translator.t("login.empty_key"), error=True)
            return

        self._login_btn.setEnabled(False)
        self._key_input.setEnabled(False)
        self._status_label.setVisible(False)

        # Start loading animation
        self._loading_dots = 0
        self._loading_base = self.translator.t("login.logging_in")
        self._login_btn.setText(f"⏳ {self._loading_base}")

        from PySide6.QtCore import QTimer
        self._loading_timer = QTimer(self)
        self._loading_timer.timeout.connect(self._animate_loading)
        self._loading_timer.start(400)

        # Run login in background thread
        from PySide6.QtCore import QThread, Signal as TSignal

        class LoginWorker(QThread):
            finished = TSignal(bool, str)

            def __init__(self, auth_manager, key_code):
                super().__init__()
                self._auth = auth_manager
                self._key = key_code

            def run(self):
                success, message = self._auth.login(self._key)
                self.finished.emit(success, message)

        self._worker = LoginWorker(self.auth_manager, key_code)
        self._worker.finished.connect(self._on_login_finished)
        self._worker.start()

    def _animate_loading(self):
        """Animate dots on login button while waiting."""
        self._loading_dots = (self._loading_dots + 1) % 4
        dots = "." * self._loading_dots
        self._login_btn.setText(f"⏳ {self._loading_base}{dots}")

    def _on_login_finished(self, success: bool, message: str):
        """Handle login result from background thread."""
        # Stop animation
        if hasattr(self, '_loading_timer'):
            self._loading_timer.stop()

        self._key_input.setEnabled(True)

        if success:
            self._show_status(f"✅ {message}", error=False)
            self.login_success.emit(self.auth_manager.session)
            from PySide6.QtCore import QTimer
            QTimer.singleShot(800, self.accept)
        else:
            self._show_status(f"❌ {message}", error=True)
            self._login_btn.setEnabled(True)
            self._login_btn.setText(f"🔑 {self.translator.t('login.button')}")

    def _show_status(self, text: str, error: bool = False):
        self._status_label.setText(text)
        self._status_label.setVisible(True)
        if error:
            self._status_label.setObjectName("login_status_error")
        else:
            self._status_label.setObjectName("login_status_success")
        self._status_label.style().unpolish(self._status_label)
        self._status_label.style().polish(self._status_label)

    def _on_forgot_key(self):
        """Open Zalo contact link so the user can reach admin."""
        QDesktopServices.openUrl(QUrl("https://zalo.me/0356241963"))

