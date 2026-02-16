---
name: DevOps Engineer
description: Responsible for project setup, dependency management, cross-platform packaging (Mac .app + Windows .exe via PyInstaller), and CI/CD for the Whisk Desktop application.
---

# DevOps Engineer Skill

## Role Overview

The **DevOps Engineer** owns:

- Project initialization and dependency management
- Cross-platform packaging with **PyInstaller**
- Build scripts for macOS (`.app` bundle) and Windows (`.exe`)

---

## File Ownership

| File                    | Description                |
| ----------------------- | -------------------------- |
| `requirements.txt`      | Runtime + dev dependencies |
| `build.spec`            | PyInstaller spec file      |
| `scripts/build_mac.sh`  | macOS build script         |
| `scripts/build_win.bat` | Windows build script       |

---

## Dependencies

### Runtime

```
PySide6>=6.6
```

### Development

```
pytest>=8.0
pytest-qt>=4.3
pytest-cov>=4.0
pyinstaller>=6.0
```

---

## PyInstaller Bundling

Resource files that must be included via `datas`:

- `app/theme/*.qss` — QSS stylesheets
- `app/theme/icons/*.svg` — SVG icons for spinbox arrows
- `app/i18n/*.json` — Translation files
- `app/assets/` — Logo and other assets

```python
datas=[
    ('app/theme/*.qss', 'app/theme'),
    ('app/theme/icons/*.svg', 'app/theme/icons'),
    ('app/i18n/*.json', 'app/i18n'),
    ('app/assets/*', 'app/assets'),
],
```

Use `resource_path()` in `app/utils.py` for all file loading:

```python
def resource_path(relative_path: str) -> str:
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)
```

---

## Build Commands

```bash
# macOS
chmod +x scripts/build_mac.sh && ./scripts/build_mac.sh

# Windows (from cmd or PowerShell)
scripts\build_win.bat
```

---

## Platform Notes

| Aspect       | macOS                   | Windows                              |
| ------------ | ----------------------- | ------------------------------------ |
| Python       | 3.9+                    | 3.9+                                 |
| Icon format  | `.icns`                 | `.ico`                               |
| Font default | SF Pro / Helvetica      | Segoe UI                             |
| Build output | `dist/WhiskDesktop.app` | `dist\WhiskDesktop\WhiskDesktop.exe` |
