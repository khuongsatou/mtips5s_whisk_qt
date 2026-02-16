---
description: Build macOS .app bundle and DMG installer using PyInstaller
---

# Build macOS App

## Prerequisites

- PyInstaller ≥ 6.0 installed (`pip install pyinstaller`)
- All dependencies in `requirements.txt` installed

## Steps

// turbo-all

1. **Clean previous build artifacts**

```bash
cd /Users/apple/Desktop/extension/mtips5s_whisk && rm -rf build/ dist/ *.spec
```

2. **Build the .app bundle**

```bash
cd /Users/apple/Desktop/extension/mtips5s_whisk && python3 -m PyInstaller --name "Whisk Desktop" --windowed --onedir --icon=app/theme/icons/app_icon.icns --add-data "app/i18n:app/i18n" --add-data "app/theme:app/theme" main.py
```

3. **Verify the build**

```bash
ls -la /Users/apple/Desktop/extension/mtips5s_whisk/dist/Whisk\ Desktop.app/Contents/MacOS/
```

4. **Test launch the built app**

```bash
open /Users/apple/Desktop/extension/mtips5s_whisk/dist/Whisk\ Desktop.app
```

## Notes

- The `--add-data` flags ensure i18n JSON files and theme QSS/icons are bundled
- For Windows build, replace `.icns` with `.ico` and use `--onefile` for single EXE
- For universal binary (Intel + Apple Silicon), build on each architecture separately
