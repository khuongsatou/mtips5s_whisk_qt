"""
Whisk Desktop — Application Factory.

Creates and configures the QApplication instance.
"""
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont


def create_app(argv=None) -> QApplication:
    """Create and configure the QApplication.

    Args:
        argv: Command line arguments. Defaults to sys.argv.

    Returns:
        Configured QApplication instance.
    """
    if argv is None:
        argv = sys.argv
    app = QApplication(argv)
    app.setApplicationName("Whisk Desktop")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Whisk")

    # Set default font — use system-available fonts
    if sys.platform == "darwin":
        font = QFont(".AppleSystemUIFont", 13)
    elif sys.platform == "win32":
        font = QFont("Segoe UI", 10)
    else:
        font = QFont("Helvetica Neue", 11)
    app.setFont(font)

    return app
