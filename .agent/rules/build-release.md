# Build & Release Rules

## Khi user yêu cầu "build win" hoặc "build mac"

### Build macOS

- Script: `scripts/build_mac_nuitka.sh`
- Output: `dist/Whisk Desktop.app` + `dist/WhiskDesktop.dmg`
- Command: `chmod +x scripts/build_mac_nuitka.sh && bash scripts/build_mac_nuitka.sh`

### Build Windows

- Script: `scripts/build_win_remote.sh`
- Output: `dist/WhiskDesktop/WhiskDesktop.exe`
- Command: `chmod +x scripts/build_win_remote.sh && bash scripts/build_win_remote.sh`
- Server: `root@45.32.63.217` (AlmaLinux 8.10, Docker + Wine + PyInstaller)

## Version Bump (bắt buộc trước mỗi lần build)

**Trước khi chạy build script, PHẢI tăng version** theo semver (patch +1 mặc định, hoặc minor/major nếu user chỉ định).

Cập nhật version ở TẤT CẢ các file sau (giữ đồng bộ):

| File                          | Pattern                        |
| ----------------------------- | ------------------------------ |
| `app/version.py`              | `__version__ = "X.Y.Z"`        |
| `pyproject.toml`              | `version = "X.Y.Z"`            |
| `scripts/build_mac_nuitka.sh` | `VERSION="X.Y.Z"`              |
| `scripts/build_mac.sh`        | `VERSION="X.Y.Z"`              |
| `scripts/installer.iss`       | `#define MyAppVersion "X.Y.Z"` |

### Quy tắc tăng version:

- **Patch** (1.0.0 → 1.0.1): mặc định, mỗi lần build
- **Minor** (1.0.x → 1.1.0): khi user nói "tính năng mới" hoặc "minor"
- **Major** (1.x.x → 2.0.0): khi user nói "major"
