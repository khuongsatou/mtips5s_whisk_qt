# -*- mode: python ; coding: utf-8 -*-
"""
Whisk Desktop — PyInstaller Build Spec.

Builds the application for Windows (.exe).
Bundles QSS themes and JSON translation files.
"""
import sys

block_cipher = None
app_name = "Veo3DeskTop"

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app/theme/*.qss', 'app/theme'),
        ('app/theme/icons/*.svg', 'app/theme/icons'),
        ('app/i18n/*.json', 'app/i18n'),
        ('app/assets/*', 'app/assets'),
        ('app/assets/fonts/*', 'app/assets/fonts'),
    ],
    hiddenimports=[
        'PySide6.QtSvg',
        'PySide6.QtSvgWidgets',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    strip=False,
    upx=True,
    console=False,
    icon='resources/icon.icns' if sys.platform == 'darwin' else 'resources/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name=app_name,
)

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name=f'{app_name}.app',
        icon='resources/icon.icns',
        bundle_identifier='com.1nutnhanveo3.desktop',
        info_plist={
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleName': 'Whisk Desktop',
            'NSHighResolutionCapable': True,
        },
    )
