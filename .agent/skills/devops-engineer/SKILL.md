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

---

## Build Rules

> [!IMPORTANT]
> **Production environment is mandatory for release builds.** The build script (`scripts/build_mac.sh`) automatically handles this.

### Environment Switching

| Item             | Dev (local `python main.py`) | Prod (bundled `.app`)         |
| ---------------- | ---------------------------- | ----------------------------- |
| `APP_ENV`        | `dev` (from `.env`)          | `prod` (set in `launcher.sh`) |
| `ADMIN_BASE_URL` | `http://localhost:8000`      | `https://tools.1nutnhan.com`  |
| `FLOW_BASE_URL`  | `http://localhost:8000`      | `https://tools.1nutnhan.com`  |
| `LABS_BASE_URL`  | `https://labs.google/fx`     | `https://labs.google/fx`      |

### How it works

1. `launcher.sh` (inside `.app/Contents/MacOS/`) exports `APP_ENV=prod`
2. `.env` with `APP_ENV=prod` is created inside the bundle at `Resources/app_bundle/.env`
3. `.env.prod` is copied to `Resources/app_bundle/.env.prod`
4. `app/api/api_config.py` reads `APP_ENV` → selects correct base URLs

### Key files

| File                    | Role                                                                |
| ----------------------- | ------------------------------------------------------------------- |
| `.env`                  | Root env (sets `APP_ENV=dev` locally)                               |
| `.env.dev`              | Dev-specific overrides                                              |
| `.env.prod`             | Prod-specific overrides                                             |
| `app/api/api_config.py` | Reads env → sets `ADMIN_BASE_URL`, `FLOW_BASE_URL`, `LABS_BASE_URL` |
| `scripts/build_mac.sh`  | Injects `APP_ENV=prod` into launcher + bundles `.env.prod`          |

---

## Windows Build Server (SSH)

> [!IMPORTANT]
> **Always use this server for Windows .exe builds.** No need to ask the user for credentials.

| Item     | Value                   |
| -------- | ----------------------- |
| Host     | `45.32.63.217`          |
| User     | `root`                  |
| Password | `m[Z3T(r%ghDWpk.q`      |
| Command  | `ssh root@45.32.63.217` |

### Windows Build Workflow

1. SSH into the server
2. Sync project files via `scp` or `rsync`
3. Install dependencies: `pip install -r requirements.txt pyinstaller`
4. Run PyInstaller: `pyinstaller --name Veo3DeskTop --windowed --onedir --icon=resources/icon.ico --add-data "app/i18n;app/i18n" --add-data "app/theme;app/theme" --add-data "app/assets;app/assets" main.py`
5. Set `APP_ENV=prod` in the bundled `.env`
6. Copy `.exe` back to Mac via `scp`
