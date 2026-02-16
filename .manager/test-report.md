# 🧪 Test Report

> **Owner**: 🧪 QA Engineer (`qa-engineer/SKILL.md`)
> **Stack**: pytest 9.0.2 · pytest-qt 4.5.0 · pytest-cov 7.0.0

**Date**: 2026-02-15 | **Python**: 3.11.11 | **PySide6**: 6.9.3

---

## Summary

| Metric      | Value  |
| ----------- | ------ |
| Total tests | 163    |
| Passed      | 163 ✅ |
| Failed      | 0      |
| Coverage    | 42%    |
| Duration    | 0.62s  |

## Coverage by Skill Owner

### 🎨 UI/UX Developer Modules

| Module                    | Stmts | Coverage | Test File                  |
| ------------------------- | ----- | -------- | -------------------------- |
| `collapsible_section.py`  | 50    | 100% ✅  | `test_collapsible_section` |
| `sidebar.py`              | 136   | 99% ✅   | `test_widgets`             |
| `status_badge.py`         | 22    | 95% ✅   | `test_widgets`             |
| `config_panel.py`         | 553   | 93% ✅   | `test_config_panel`        |
| `reference_image_grid.py` | 145   | 86%      | `test_widgets`             |
| `header.py`               | 108   | 86%      | `test_widgets`             |
| `toggle_switch.py`        | 70    | 63%      | `test_toggle_switch`       |
| `task_queue_table.py`     | 200   | 0% 🔴    | _none_                     |
| `log_panel.py`            | 76    | 0% 🔴    | _none_                     |
| `queue_toolbar.py`        | 63    | 0% 🔴    | _none_                     |

### ⚙️ Backend Developer Modules

| Module            | Stmts | Coverage | Test File           |
| ----------------- | ----- | -------- | ------------------- |
| `base_api.py`     | 55    | 100% ✅  | `test_mock_api`     |
| `models.py`       | 136   | 93% ✅   | `test_models`       |
| `auth_manager.py` | 111   | 58%      | `test_auth_manager` |
| `mock_api.py`     | 223   | 54%      | `test_mock_api`     |

### 🌐 i18n Specialist Modules

| Module          | Stmts | Coverage | Test File         |
| --------------- | ----- | -------- | ----------------- |
| `translator.py` | 35    | 94% ✅   | `test_translator` |

### 🎨 UI/UX Theme

| Module             | Stmts | Coverage | Test File            |
| ------------------ | ----- | -------- | -------------------- |
| `theme_manager.py` | 40    | 70%      | `test_theme_manager` |

## Bugs Found & Fixed (Iteration #1)

| Bug                          | Owner          | Severity |
| ---------------------------- | -------------- | -------- |
| `_quality_group` not defined | ⚙️ Backend Dev | 🔴 High  |
| Delay spinners reset to 0    | ⚙️ Backend Dev | 🟡 Med   |
| Duplicate orphaned code      | 🎨 UI/UX Dev   | 🟡 Med   |

## Running Tests

```bash
# Full suite (per qa-engineer/SKILL.md)
python3 -m pytest tests/ -v --tb=short

# With coverage
python3 -m pytest tests/ -v --cov=app --cov-report=term-missing
```
