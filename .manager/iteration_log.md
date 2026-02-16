# 🔄 Iteration Log

> **Owner**: 📋 Project Manager (`project-manager/SKILL.md`)
> **Team**: 🎨 UI/UX · ⚙️ Backend · 🌐 i18n · 🧪 QA · 🚀 DevOps

---

## Iteration #1 — 2026-02-15

### Goal

Address project risks: refactor ConfigPanel, fix unit tests, improve coverage.

### Work by Role

**🎨 UI/UX Developer:**

- Refactored `config_panel.py` `_setup_ui` (462 → 30 lines) into 6 `_build_*` methods
- Removed 34-line orphaned duplicate code block

**⚙️ Backend Developer:**

- Fixed `_quality_group` AttributeError in `reset_to_defaults` and `_load_settings`
- Fixed delay spinner QSettings loading (`s.contains()` guard)

**🧪 QA Engineer:**

- Created 5 new test files: `test_config_panel`, `test_auth_manager`, `test_models`, `test_collapsible_section`, `test_toggle_switch`
- 111 new tests added (52 → 163 total)
- Coverage: 21% → 42%
- Found and reported 3 production bugs

### Results

| Metric     | Before | After |
| ---------- | ------ | ----- |
| Tests      | 52     | 163   |
| Coverage   | 21%    | 42%   |
| Pass rate  | 96%    | 100%  |
| Bugs fixed | —      | 3     |

### Decisions Made

- Deferred Real API integration (⚙️ Backend — needs endpoint design)
- Used `_quality_buttons[]` pattern instead of `QButtonGroup` (⚙️ Backend)
- Used `s.contains()` guard for QSettings integer loading (⚙️ Backend)
- Used `isHidden()` instead of `isVisible()` for headless test assertions (🧪 QA)

---

_Add new iterations below._
