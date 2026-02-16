# 🎨 UX Feedback

> **Owner**: 🎨 UI/UX Developer (`ui-ux-developer/SKILL.md`)
> **Palette**: Triadic purple-teal-amber (see skill for token table)

**Last updated**: 2026-02-15

---

## Implemented UI Components

| Widget             | QSS Object Name         | Theme Support | Status |
| ------------------ | ----------------------- | ------------- | ------ |
| ConfigPanel        | `#config_panel`         | ✅            | ✅     |
| TaskQueueTable     | `#task_queue_table`     | ✅            | ✅     |
| Sidebar            | `#sidebar`              | ✅            | ✅     |
| Header             | `#header`               | ✅            | ✅     |
| CollapsibleSection | `#collapsible_section`  | ✅            | ✅     |
| ToggleSwitch       | `#toggle_switch`        | ✅            | ✅     |
| ReferenceImageGrid | `#reference_image_grid` | ✅            | ✅     |
| StatusBadge        | `#status_badge`         | ✅            | ✅     |
| LogPanel           | `#log_panel`            | ✅            | ✅     |
| QueueToolbar       | `#queue_toolbar`        | ✅            | ✅     |

## Design Principles Applied

- **Triadic palette**: Purple (`#7C3AED`) / Teal (`#14B8A6`) / Amber (`#F59E0B`)
- **`{{token}}`** QSS placeholders → ThemeManager replaces at runtime
- **Both** `light.qss` + `dark.qss` have matching selectors
- **`setObjectName()`** on all widgets for QSS targeting

## Known UX Issues

_None reported yet._

## Improvement Backlog

| Item                           | Priority | Notes                         |
| ------------------------------ | -------- | ----------------------------- |
| Keyboard navigation audit      | P2       | Tab order, focus indicators   |
| WCAG 2.1 AA contrast check     | P2       | Verify dark mode meets 4.5:1  |
| Screen reader compatibility    | P3       | Accessible names on controls  |
| Responsive layout for < 1024px | P3       | Currently fixed-width sidebar |

## Observations

_Add UX observations after each review session._
