---
name: PyQt Desktop App
description: Instructions for developing, extending, and maintaining the Whisk Desktop PySide6 application — an AI image generation tool with configurable queue, reference images, and persistent settings.
---

# PyQt Desktop App — Master Skill

## Overview

**Whisk Desktop** is a PySide6 desktop application for AI image generation. Users configure generation parameters, pick reference images, write prompts, and manage a task queue with progress tracking.

---

## Team Skills

| Role                 | Skill                        | Focus Area                            |
| -------------------- | ---------------------------- | ------------------------------------- |
| 📋 Project Manager   | `project-manager/SKILL.md`   | Progress reports, milestone tracking  |
| 🎨 UI/UX Developer   | `ui-ux-developer/SKILL.md`   | Theme, QSS, widgets, pages            |
| ⚙️ Backend Developer | `backend-developer/SKILL.md` | API layer, data models, mock/real API |
| 🌐 i18n Specialist   | `i18n-specialist/SKILL.md`   | Translations, language switching      |
| 🧪 QA Engineer       | `qa-engineer/SKILL.md`       | Unit tests, coverage                  |
| 🚀 DevOps Engineer   | `devops-engineer/SKILL.md`   | Setup, cross-platform build           |

---

## Quick Reference

```bash
# Install
python3 -m pip install -r requirements.txt

# Run
python3 main.py

# Test
python3 -m pytest tests/ -v
```

---

## Architecture

```
main.py → MainWindow
            ├── ThemeManager (light/dark triadic palette)
            ├── Translator (en/vi JSON i18n)
            ├── AuthManager (login/session)
            ├── MockApi → BaseApi (abstract)
            ├── Sidebar → page switching (collapsible)
            ├── Header → theme/lang toggle, user info, auto/quota switches
            └── QStackedWidget
                ├── DashboardPage
                ├── ImageCreatorPage ← main page
                │   ├── ConfigPanel (left)
                │   │   ├── Model/Quality/Ratio selection
                │   │   ├── Execution settings (images/prompt, concurrency, delay)
                │   │   ├── Prompt input (multi-line, split modes)
                │   │   ├── Reference images (Title/Scene/Style, dynamic slots 1-5)
                │   │   ├── Output folder picker
                │   │   ├── Pipeline steps guide
                │   │   ├── Add to Queue + Reset buttons
                │   │   └── QSettings persistence
                │   ├── TaskQueueTable (center)
                │   │   ├── Checkbox | STT | Task | Ref Images | Prompt | Output | Progress
                │   │   ├── ReferenceImageGrid (3-column: Title/Scene/Style)
                │   │   ├── Output thumbnails (grid, based on images_per_prompt)
                │   │   ├── Animated progress bars (pulsing for running tasks)
                │   │   └── Action buttons (download for completed)
                │   ├── QueueToolbar (start/stop/delete/select-all)
                │   └── LogPanel (collapsible bottom)
                ├── ItemsPage
                └── SettingsPage
```

---

## Key Widgets

| Widget                 | File                                    | Description                                             |
| ---------------------- | --------------------------------------- | ------------------------------------------------------- |
| `ConfigPanel`          | `app/widgets/config_panel.py`           | All generation settings, dynamic ref slots, persistence |
| `TaskQueueTable`       | `app/widgets/task_queue_table.py`       | Task queue with editable prompts, ref grids, progress   |
| `ReferenceImageGrid`   | `app/widgets/reference_image_grid.py`   | 3-column image grid (Title/Scene/Style, up to 5 slots)  |
| `CollapsibleSection`   | `app/widgets/collapsible_section.py`    | Animated collapsible group widget                       |
| `ToggleSwitch`         | `app/widgets/toggle_switch.py`          | Animated iOS-style toggle switch                        |
| `QueueToolbar`         | `app/widgets/queue_toolbar.py`          | Toolbar for queue actions                               |
| `LogPanel`             | `app/widgets/log_panel.py`              | Bottom log panel                                        |
| `Sidebar`              | `app/widgets/sidebar.py`                | Collapsible navigation sidebar                          |
| `Header`               | `app/widgets/header.py`                 | Top bar with user info, toggles                         |
| `CookieManagerDialog`  | `app/widgets/cookie_manager_dialog.py`  | Cookie management dialog                                |
| `TokenManagerDialog`   | `app/widgets/token_manager_dialog.py`   | Token management dialog                                 |
| `ProjectManagerDialog` | `app/widgets/project_manager_dialog.py` | Project management dialog                               |
| `LoginDialog`          | `app/widgets/login_dialog.py`           | Login dialog                                            |

---

## Key Design Decisions

1. **PySide6** (LGPL) over PyQt6 (GPL) — friendlier licensing
2. **Triadic palette** — Purple / Teal / Amber at 120° intervals
3. **`resource_path()`** — resolves paths in dev mode and PyInstaller bundles
4. **Abstract `BaseApi`** — swap `MockApi` → `RealApi` with zero UI changes
5. **JSON-based i18n** — simpler than Qt `.ts` files, easy to edit
6. **QSettings** — persists config panel settings across app restarts
7. **Dynamic slot rows** — users add reference image slots (1-5) per category
8. **QPropertyAnimation** — smooth pulsing progress bars for running tasks
