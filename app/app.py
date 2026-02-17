"""
Whisk Desktop — Application Factory.

Creates and configures the QApplication instance.
"""
import os
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QFontDatabase

from app.utils import resource_path
from app.version import __version__


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
    app.setApplicationVersion(__version__)
    app.setOrganizationName("Whisk")

    # Load bundled Roboto font
    fonts_dir = resource_path(os.path.join("app", "assets", "fonts"))
    for font_file in ("Roboto.ttf", "Roboto-Italic.ttf"):
        font_path = os.path.join(fonts_dir, font_file)
        if os.path.isfile(font_path):
            QFontDatabase.addApplicationFont(font_path)

    # Set Roboto as the app-wide font
    font = QFont("Roboto", 13)
    app.setFont(font)

    return app
