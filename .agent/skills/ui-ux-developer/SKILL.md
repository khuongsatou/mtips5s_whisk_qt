---
name: UI/UX Developer
description: Responsible for theming (triadic palette, light/dark mode), QSS stylesheets, reusable widgets, page layouts, and visual polish for the PySide6 desktop application.
---

# UI/UX Developer Skill

## Role Overview

The **UI/UX Developer** owns:

- Triadic color scheme implementation (purple-teal-amber)
- Light / Dark mode via `ThemeManager`
- QSS stylesheets (`light.qss`, `dark.qss`) with `{{token}}` placeholders
- All widgets in `app/widgets/`
- All pages in `app/pages/`
- Responsive layout, animations, and visual polish

---

## Triadic Color Palette

| Token                 | Light Mode | Dark Mode | Usage                          |
| --------------------- | ---------- | --------- | ------------------------------ |
| `bg-primary`          | `#FFFFFF`  | `#1E1B2E` | Main backgrounds               |
| `bg-secondary`        | `#F5F3FF`  | `#2D2A3E` | Cards, sidebar                 |
| `bg-hover`            | `#EDE9FE`  | `#3D3A4E` | Hover states                   |
| `text-primary`        | `#1F2937`  | `#F9FAFB` | Main text                      |
| `text-secondary`      | `#6B7280`  | `#9CA3AF` | Subtle text                    |
| `color-primary`       | `#7C3AED`  | `#A78BFA` | Primary actions, active states |
| `color-primary-light` | `#A78BFA`  | `#C4B5FD` | Gradients, highlights          |
| `color-secondary`     | `#14B8A6`  | `#2DD4BF` | Success, secondary actions     |
| `color-accent`        | `#F59E0B`  | `#FBBF24` | Warnings, highlights           |
| `border`              | `#E5E7EB`  | `#4B5563` | Borders, dividers              |

---

## File Ownership

| File                                  | Description                                                           |
| ------------------------------------- | --------------------------------------------------------------------- |
| `app/theme/theme_manager.py`          | Theme engine with palette, `{{token}}` + `{{icons-path}}` replacement |
| `app/theme/light.qss`                 | Light mode stylesheet (~1370 lines)                                   |
| `app/theme/dark.qss`                  | Dark mode stylesheet (~1370 lines)                                    |
| `app/theme/icons/`                    | SVG icons (arrows, etc.) for QSS                                      |
| `app/widgets/config_panel.py`         | Config panel with dynamic slots, QSettings                            |
| `app/widgets/task_queue_table.py`     | Task queue table with animated progress                               |
| `app/widgets/reference_image_grid.py` | 3-column reference image grid                                         |
| `app/widgets/collapsible_section.py`  | Animated collapsible section                                          |
| `app/widgets/toggle_switch.py`        | iOS-style animated toggle switch                                      |
| `app/widgets/sidebar.py`              | Collapsible sidebar navigation                                        |
| `app/widgets/header.py`               | Header with user info, toggles                                        |
| `app/widgets/log_panel.py`            | Collapsible log panel                                                 |
| `app/widgets/queue_toolbar.py`        | Queue action toolbar                                                  |
| `app/pages/image_creator_page.py`     | Main image creator page                                               |
| `app/pages/dashboard_page.py`         | Dashboard page                                                        |
| `app/main_window.py`                  | Main window layout                                                    |

---

## QSS Conventions

- Use `{{token}}` placeholders — `ThemeManager` replaces them at runtime
- Use `{{icons-path}}` for SVG icon references: `url({{icons-path}}/arrow_up.svg)`
- Never hardcode hex colors in `.py` files — always use QSS or palette tokens
- Group styles by widget type, use `objectName` selectors: `#config_panel`, `#task_queue_table`
- Both `light.qss` and `dark.qss` must have matching selectors

---

## Adding a New Widget

1. Create `app/widgets/my_widget.py`
2. Accept `translator` in constructor
3. Implement `retranslate()` method for i18n refresh
4. Use `setObjectName()` for QSS targeting
5. Add styles to both `light.qss` and `dark.qss`
6. Add tests in `tests/`

---

## Key Patterns

- **Dynamic slot rows**: `ConfigPanel._add_ref_slot_row()` — dynamically creates UI rows
- **QPropertyAnimation**: Used for progress bar pulsing, toggle switch animation
- **QSettings**: `ConfigPanel` persists settings with `QSettings("Whisk", "ConfigPanel")`
- **CollapsibleSection**: Wraps groups of related controls with expand/collapse animation
- **QGridLayout**: Used for output thumbnails (2 columns) and reference image grid
