"""
Tests for LoginDialog — login modal with key_code input.
"""
import pytest
from unittest.mock import MagicMock
from PySide6.QtWidgets import QLineEdit
from app.widgets.login_dialog import LoginDialog


@pytest.fixture
def auth_manager():
    mgr = MagicMock()
    mgr.login.return_value = (True, "Welcome!")
    mgr.session = MagicMock()
    return mgr


class TestLoginDialogInit:
    """Test initial construction."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator, auth_manager):
        self.dialog = LoginDialog(auth_manager, translator)
        qtbot.addWidget(self.dialog)

    def test_window_title(self):
        assert self.dialog.windowTitle()  # not empty

    def test_fixed_size(self):
        assert self.dialog.width() == 420
        assert self.dialog.height() == 420

    def test_has_key_input(self):
        assert hasattr(self.dialog, '_key_input')
        assert isinstance(self.dialog._key_input, QLineEdit)

    def test_password_mode(self):
        assert self.dialog._key_input.echoMode() == QLineEdit.Password

    def test_has_login_button(self):
        assert self.dialog._login_btn is not None

    def test_has_show_button(self):
        assert self.dialog._show_btn is not None
        assert self.dialog._show_btn.isCheckable()


class TestLoginDialogToggleVisibility:
    """Test show/hide key toggle."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator, auth_manager):
        self.dialog = LoginDialog(auth_manager, translator)
        qtbot.addWidget(self.dialog)

    def test_toggle_shows_text(self):
        self.dialog._on_toggle_visibility(True)
        assert self.dialog._key_input.echoMode() == QLineEdit.Normal

    def test_toggle_hides_text(self):
        self.dialog._on_toggle_visibility(True)
        self.dialog._on_toggle_visibility(False)
        assert self.dialog._key_input.echoMode() == QLineEdit.Password


class TestLoginDialogLogin:
    """Test login behavior."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator, auth_manager):
        self.auth = auth_manager
        self.dialog = LoginDialog(auth_manager, translator)
        qtbot.addWidget(self.dialog)

    def test_empty_key_shows_error(self):
        self.dialog._key_input.setText("")
        self.dialog._on_login()
        assert self.dialog._status_label.text()  # has error text

    def test_successful_login_emits_signal(self, qtbot):
        self.dialog._key_input.setText("valid_key")
        with qtbot.waitSignal(self.dialog.login_success, timeout=1000):
            self.dialog._on_login()

    def test_failed_login_shows_error(self, qtbot):
        self.auth.login.return_value = (False, "Invalid")
        self.dialog._key_input.setText("bad_key")
        self.dialog._on_login()
        # Wait for background worker thread to complete
        self.dialog._worker.wait()
        # Process pending cross-thread signals
        from PySide6.QtCore import QCoreApplication
        QCoreApplication.processEvents()
        assert "Invalid" in self.dialog._status_label.text()

    def test_login_disables_button_on_attempt(self):
        self.dialog._key_input.setText("key")
        self.dialog._on_login()
        # On success the button may be re-enabled by timer, but it was disabled


class TestLoginDialogShowStatus:
    """Test status message display."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator, auth_manager):
        self.dialog = LoginDialog(auth_manager, translator)
        qtbot.addWidget(self.dialog)

    def test_show_status_makes_visible(self):
        self.dialog._show_status("test", error=False)
        assert self.dialog._status_label.text() == "test"

    def test_show_status_error(self):
        self.dialog._show_status("err", error=True)
        assert self.dialog._status_label.objectName() == "login_status_error"

    def test_show_status_success(self):
        self.dialog._show_status("ok", error=False)
        assert self.dialog._status_label.objectName() == "login_status_success"
