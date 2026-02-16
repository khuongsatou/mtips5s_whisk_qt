# 🧪 Test Report

> **Owner**: 🧪 QA Engineer (`qa-engineer/SKILL.md`)
> **Stack**: pytest 9.0.2 · pytest-qt 4.5.0 · pytest-cov 7.0.0

**Date**: 2026-02-16 17:50 | **Python**: 3.12.8 | **PySide6**: 6.9.3

---

## Summary

| Metric      | Value   |
| ----------- | ------- |
| Total tests | 637     |
| Passed      | 637 ✅  |
| Failed      | 0       |
| Coverage    | **81%** |
| Duration    | 7.28s   |

## Coverage by Skill Owner

### 🎨 UI/UX Developer Modules

| Module                      | Stmts | Coverage | Test File                     |
| --------------------------- | ----- | -------- | ----------------------------- |
| `collapsible_section.py`    | 50    | 100% ✅  | `test_collapsible_section`    |
| `toggle_switch.py`          | 70    | 100% ✅  | `test_toggle_switch`          |
| `data_table.py`             | 68    | 100% ✅  | `test_data_table`             |
| `queue_toolbar.py`          | 78    | 100% ✅  | `test_queue_toolbar`          |
| `sidebar.py`                | 136   | 99% ✅   | `test_widgets`                |
| `cookie_manager_dialog.py`  | 252   | 99% ✅   | `test_cookie_manager_dialog`  |
| `token_manager_dialog.py`   | 247   | 98% ✅   | `test_token_manager_dialog`   |
| `log_panel.py`              | 76    | 97% ✅   | `test_log_panel`              |
| `login_dialog.py`           | 144   | 96% ✅   | `test_login_dialog`           |
| `status_badge.py`           | 22    | 95% ✅   | `test_widgets`                |
| `config_panel.py`           | 578   | 92% ✅   | `test_config_panel`           |
| `styled_message_box.py`     | 107   | 92% ✅   | `test_styled_message_box`     |
| `project_tab_bar.py`        | 105   | 91% ✅   | `test_project_tab_bar`        |
| `task_queue_table.py`       | 355   | 90% ✅   | `test_task_queue_table`       |
| `reference_image_grid.py`   | 145   | 86%      | `test_widgets`                |
| `header.py`                 | 107   | 85%      | `test_widgets`                |
| `project_manager_dialog.py` | 225   | 85%      | `test_project_manager_dialog` |

### ⚙️ Backend Developer Modules

| Module                 | Stmts | Coverage | Test File                |
| ---------------------- | ----- | -------- | ------------------------ |
| `base_api.py`          | 69    | 100% ✅  | `test_mock_api`          |
| `utils.py`             | 9     | 100% ✅  | `test_utils`             |
| `auth_manager.py`      | 176   | 97% ✅   | `test_auth_manager`      |
| `prompt_normalizer.py` | 63    | 97% ✅   | `test_prompt_normalizer` |
| `flow_api.py`          | 91    | 97% ✅   | `test_flow_api`          |
| `workflow_api.py`      | 126   | 95% ✅   | `test_workflow_api`      |
| `mock_api.py`          | 324   | 80%      | `test_mock_api`          |
| `models.py`            | 223   | 81%      | `test_models`            |
| `api_config.py`        | 38    | 58%      | —                        |

### 🌐 i18n Specialist Modules

| Module          | Stmts | Coverage | Test File         |
| --------------- | ----- | -------- | ----------------- |
| `translator.py` | 35    | 94% ✅   | `test_translator` |

### 🎨 UI/UX Theme

| Module             | Stmts | Coverage | Test File            |
| ------------------ | ----- | -------- | -------------------- |
| `theme_manager.py` | 40    | 100% ✅  | `test_theme_manager` |

### 📄 Pages

| Module                  | Stmts | Coverage | Test File             |
| ----------------------- | ----- | -------- | --------------------- |
| `dashboard_page.py`     | 101   | 99% ✅   | `test_dashboard_page` |
| `settings_page.py`      | 208   | 86%      | `test_settings_page`  |
| `items_page.py`         | 119   | 85%      | `test_items_page`     |
| `image_creator_page.py` | 492   | 24% �    | partial               |
| `main_window.py`        | 224   | 0% 🔴    | _none_                |
| `app.py`                | 20    | 0% 🔴    | _none_                |

## Running Tests

```bash
# Full suite (per qa-engineer/SKILL.md)
python3 -m pytest tests/ -v --tb=short

# With coverage
python3 -m pytest tests/ -v --cov=app --cov-report=term-missing
```
