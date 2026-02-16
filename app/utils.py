"""
Whisk Desktop — Resource path utility for bundled app compatibility.
"""
import sys
import os


def resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev, PyInstaller, and .app bundle.

    Resolution order:
    1. PyInstaller frozen bundle (sys._MEIPASS)
    2. macOS .app bundle (WHISK_RESOURCE_DIR env var)
    3. Development mode (relative to project root)

    Args:
        relative_path: Path relative to the project root (e.g. 'app/theme/light.qss')

    Returns:
        Absolute path to the resource file.
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller frozen bundle
        return os.path.join(sys._MEIPASS, relative_path)

    resource_dir = os.environ.get('WHISK_RESOURCE_DIR')
    if resource_dir:
        # macOS .app bundle — resources in Contents/Resources/
        return os.path.join(resource_dir, relative_path)

    return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', relative_path)

