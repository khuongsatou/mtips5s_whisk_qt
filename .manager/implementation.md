# 🛠️ Implementation Notes

> **Contributors**: 🎨 UI/UX Dev · ⚙️ Backend Dev · 🌐 i18n
> **Reference**: `pyqt-desktop-app/SKILL.md` (master architecture)

**Last updated**: 2026-02-15

---

## Architecture

```
main.py → MainWindow
            ├── ThemeManager          (🎨 UI/UX Dev)
            ├── Translator            (🌐 i18n)
            ├── AuthManager           (⚙️ Backend Dev)
            ├── MockApi → BaseApi     (⚙️ Backend Dev)
            ├── Sidebar               (🎨 UI/UX Dev)
            ├── Header                (🎨 UI/UX Dev)
            └── QStackedWidget
                ├── DashboardPage     (🎨 UI/UX Dev)
                ├── ImageCreatorPage  (🎨 UI/UX Dev)
                │   ├── ConfigPanel   (🎨 UI/UX Dev)
                │   ├── TaskQueueTable(🎨 UI/UX Dev)
                │   ├── QueueToolbar  (🎨 UI/UX Dev)
                │   └── LogPanel      (🎨 UI/UX Dev)
                ├── ItemsPage         (🎨 UI/UX Dev)
                └── SettingsPage      (🎨 UI/UX Dev)
```

## Recent Changes

### Iteration #1 — 2026-02-15

**🎨 UI/UX Dev:**

- Refactored `config_panel.py` `_setup_ui` (462 lines) → 6 `_build_*` methods
- Removed 34-line orphaned duplicate code block

**⚙️ Backend Dev:**

- Fixed `_quality_group` → `_quality_buttons`/`_quality_values` in `_load_settings`/`reset_to_defaults`
- Fixed delay spinner QSettings loading (added `s.contains()` guard)

**🧪 QA Engineer:**

- Created 5 new test files (111 tests added)
- Coverage: 21% → 42%

## Tech Debt by Owner

### 🎨 UI/UX Dev

- [ ] `task_queue_table.py` — 200 stmts, 0% coverage
- [ ] Dialog widgets (cookie, token, project, login) — 0% coverage each
- [ ] Pages (dashboard, image_creator, items, settings) — 0% coverage

### ⚙️ Backend Dev

- [ ] `mock_api.py` — only 54% coverage (complex queue methods untested)
- [ ] Design Real API endpoints before `RealApi` implementation

### 🚀 DevOps

- [ ] Create `build.spec` PyInstaller config
- [ ] Create `scripts/build_mac.sh` and `scripts/build_win.bat`

## Key Design Patterns

> Documented in `pyqt-desktop-app/SKILL.md` § Key Design Decisions

| Pattern            | Owner          | Details                                                      |
| ------------------ | -------------- | ------------------------------------------------------------ |
| Abstract `BaseApi` | ⚙️ Backend Dev | Swap `MockApi` → `RealApi` with zero UI changes              |
| `{{token}}` QSS    | 🎨 UI/UX Dev   | ThemeManager replaces tokens at runtime                      |
| JSON i18n          | 🌐 i18n        | `translator.t("key")` pattern, `retranslate()` on switch     |
| QSettings          | 🎨 UI/UX Dev   | ConfigPanel persists via `QSettings("Whisk", "ConfigPanel")` |
| Dynamic slot rows  | 🎨 UI/UX Dev   | Users add ref image slots (1–5) per category                 |
| `resource_path()`  | 🚀 DevOps      | Resolves paths in dev & PyInstaller bundles                  |
