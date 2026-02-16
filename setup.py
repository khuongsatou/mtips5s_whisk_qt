"""
Whisk Desktop — py2app setup for macOS .app bundling.
"""
import sys
import sysconfig
from setuptools import setup

APP = ['main.py']
APP_NAME = 'WhiskDesktop'

DATA_FILES = []

# Determine Python library path for PyRuntimeLocations
_libdir = sysconfig.get_config_var('LIBDIR')
_ldlib = sysconfig.get_config_var('LDLIBRARY')
_python_lib = f"{_libdir}/{_ldlib}" if _libdir and _ldlib else ""

OPTIONS = {
    'argv_emulation': False,
    'semi_standalone': True,
    'iconfile': 'app/assets/logo.png',
    'plist': {
        'CFBundleName': 'Whisk Desktop',
        'CFBundleDisplayName': 'Whisk Desktop',
        'CFBundleIdentifier': 'com.1nutnhanwhisk.desktop',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
        'PyRuntimeLocations': [
            f'@executable_path/../Frameworks/Python.framework/Versions/{sys.version_info.major}.{sys.version_info.minor}/Python',
            f'/usr/local/lib/libpython{sys.version_info.major}.{sys.version_info.minor}.dylib',
            _python_lib,
            sys.executable,
        ],
    },
    'packages': ['PySide6', 'app'],
    'includes': [
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtSvg',
        'PySide6.QtSvgWidgets',
    ],
    'resources': [
        'app/theme/light.qss',
        'app/theme/dark.qss',
        'app/theme/icons',
        'app/i18n/en.json',
        'app/i18n/vi.json',
        'app/assets/logo.png',
    ],
}

setup(
    name=APP_NAME,
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
