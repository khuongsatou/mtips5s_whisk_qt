"""
Whisk Desktop — Entry Point.

Bootstraps the application: creates QApp, initializes theme, i18n, auth,
then shows login dialog (if needed) and the main window.
"""
import sys
import os
import logging
from app.app import create_app
from app.theme.theme_manager import ThemeManager
from app.i18n.translator import Translator
from app.api.mock_api import MockApi
from app.api.flow_api import FlowApiClient
from app.api.cookie_api import CookieApiClient
from app.api.workflow_api import WorkflowApiClient
from app.auth.auth_manager import AuthManager
from app.main_window import MainWindow
from app.widgets.login_dialog import LoginDialog
from app.utils import resource_path
from PySide6.QtGui import QIcon

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("whisk")


def main():
    """Launch the Whisk Desktop application."""
    logger.info("Starting Whisk Desktop...")
    app = create_app(sys.argv)

    # Initialize core services
    theme_manager = ThemeManager()
    translator = Translator(default_language="en")
    api = MockApi()
    auth_manager = AuthManager()
    flow_api = FlowApiClient()
    cookie_api = CookieApiClient()
    workflow_api = WorkflowApiClient()
    logger.info("Core services initialized")

    # Set app icon
    logo_path = resource_path(os.path.join("app", "assets", "logo.png"))
    if os.path.exists(logo_path):
        app.setWindowIcon(QIcon(logo_path))

    # Apply theme stylesheet (needed for login dialog styling)
    app.setStyleSheet(theme_manager.get_stylesheet())
    logger.info(f"Theme applied: {theme_manager.current_theme}")

    # Try to restore saved session; show login dialog if not logged in
    while True:
        # Try to restore saved session; show login dialog if not logged in
        if auth_manager.try_restore_session():
            logger.info(f"Session restored for user: {auth_manager.session.username}")
        else:
            logger.info("No saved session, showing login dialog...")
            login_dialog = LoginDialog(auth_manager, translator)
            if login_dialog.exec() != LoginDialog.Accepted:
                logger.info("User cancelled login, exiting")
                sys.exit(0)
            logger.info(f"Login successful: {auth_manager.session.username}")

        # Update real API clients with the logged-in user's access token
        token = auth_manager.session.access_token
        flow_api.set_access_token(token)
        cookie_api.set_access_token(token)
        workflow_api.set_access_token(token)
        logger.info("Real API clients updated with access token")

        # Create and show main window (user is now authenticated)
        window = MainWindow(
            theme_manager, translator, api, auth_manager,
            flow_api=flow_api, cookie_api=cookie_api,
            workflow_api=workflow_api,
        )

        window.show()
        logger.info("Main window displayed")

        exit_code = app.exec()

        if exit_code == 42:
            # Logout requested — loop back to show login dialog
            logger.info("Logout requested, restarting with login dialog...")
            continue
        else:
            sys.exit(exit_code)


if __name__ == "__main__":
    main()
