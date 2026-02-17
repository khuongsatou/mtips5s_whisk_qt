# 🧪 Báo Cáo Chất Lượng — Whisk Desktop

> **Ngày**: 2026-02-17 17:15 | **QA Engineer** | **Python 3.12.8**

---

## 📊 Tổng Quan

| Metric         | Giá trị           |
| -------------- | ----------------- |
| **Tests**      | **650 passed ✅** |
| **Failed**     | 0                 |
| **Coverage**   | **77%**           |
| **Test Lines** | 5,596 dòng        |
| **Test Files** | 18 files          |
| **Thời gian**  | 7.54s             |

---

## ✅ Modules 100% Coverage (10 modules)

| Module                      | Stmts | Cover |
| --------------------------- | ----- | ----- |
| `base_api.py`               | 69    | 100%  |
| `collapsible_section.py`    | 50    | 100%  |
| `toggle_switch.py`          | 70    | 100%  |
| `data_table.py`             | 68    | 100%  |
| `theme_manager.py`          | 40    | 100%  |
| `utils.py`                  | 9     | 100%  |
| `build_sections.py`         | 381   | 100%  |
| `config_panel.py`           | 57    | 100%  |
| `workflow_api/constants.py` | 5     | 100%  |
| `mock_api/mock_api.py`      | 25    | 100%  |

## ✅ Modules 90%+ Coverage (17 modules)

| Module                     | Stmts | Cover | Missing Lines |
| -------------------------- | ----- | ----- | ------------- |
| `cookie_api.py`            | 153   | 98%   | 3 lines       |
| `cookie_manager_dialog.py` | 252   | 99%   | 3 lines       |
| `token_manager_dialog.py`  | 247   | 98%   | 5 lines       |
| `flow_api.py`              | 91    | 97%   | 3 lines       |
| `prompt_normalizer.py`     | 63    | 97%   | 2 lines       |
| `log_panel.py`             | 76    | 97%   | 2 lines       |
| `login_dialog.py`          | 145   | 96%   | 6 lines       |
| `auth_manager.py`          | 242   | 95%   | 12 lines      |
| `status_badge.py`          | 22    | 95%   | 1 line        |
| `queue_toolbar.py`         | 152   | 95%   | 7 lines       |
| `i18n/translator.py`       | 35    | 94%   | 2 lines       |
| `mock_api/queue_ops.py`    | 118   | 93%   | 8 lines       |
| `styled_message_box.py`    | 107   | 92%   | 9 lines       |
| `project_tab_bar.py`       | 105   | 91%   | 9 lines       |
| `sidebar.py`               | 136   | 99%   | 1 line        |
| `dashboard_page.py`        | 101   | 99%   | 1 line        |
| `mock_api/mock_api.py`     | 25    | 96%   | 1 line        |

## 🟡 Modules 70-89% Coverage (9 modules)

| Module                        | Stmts | Cover | Ghi chú                      |
| ----------------------------- | ----- | ----- | ---------------------------- |
| `reference_image_grid.py`     | 145   | 86%   | 21 lines missing             |
| `settings_page.py`            | 208   | 86%   | 30 lines missing             |
| `items_page.py`               | 119   | 85%   | 18 lines missing             |
| `project_manager_dialog.py`   | 225   | 85%   | 34 lines missing             |
| `header.py`                   | 101   | 84%   | 16 lines missing             |
| `task_queue_table/helpers.py` | 85    | 84%   | 14 lines missing             |
| `models.py`                   | 224   | 81%   | 42 lines missing             |
| `sample_data.py`              | 36    | 78%   | 8 lines missing              |
| `task_queue_table.py`         | 522   | 74%   | 134 lines — pagination, sort |
| `settings_handlers.py`        | 297   | 72%   | 83 lines — ref mode logic    |
| `resource_ops.py`             | 390   | 70%   | 48 lines missing             |

## 🔴 Modules <70% Coverage (5 modules)

| Module                  | Stmts | Cover | Ghi chú                           |
| ----------------------- | ----- | ----- | --------------------------------- |
| `workers.py`            | 149   | 67%   | 49 lines — ref upload, save logic |
| `api_config.py`         | 38    | 63%   | 14 lines — env config             |
| `workflow_api.py`       | 209   | 59%   | 85 lines — API calls (cần mock)   |
| `toast_notification.py` | 39    | 21%   | 31 lines — animation logic        |
| `image_creator_page.py` | 112   | 17%   | 93 lines — page init, layout      |
| `page_handlers.py`      | 418   | 9%    | 379 lines — core generation logic |
| `main_window.py`        | 224   | 0%    | Full file — complex widget deps   |
| `app.py`                | 20    | 0%    | Entry point, ít logic             |

---

## 📈 Xu Hướng Coverage

| Ngày       | Tests | Coverage | Ghi chú                        |
| ---------- | ----- | -------- | ------------------------------ |
| 2026-02-16 | 637   | 81%      | Trước file splitting           |
| 2026-02-17 | 650   | 77%      | Sau file splitting (+13 tests) |

> ⚠️ Coverage giảm 4% do file splitting tạo thêm modules mới (`page_handlers.py`, `settings_handlers.py`) chưa có tests riêng. Tổng số tests tăng +13.

---

## 🎯 Khuyến Nghị Ưu Tiên

| Priority | Action                                      | Tác động |
| -------- | ------------------------------------------- | -------- |
| P0       | Thêm tests cho `page_handlers.py` (9%)      | +6% cov  |
| P1       | Thêm tests cho `workflow_api.py` (59%)      | +2% cov  |
| P1       | Thêm tests cho `settings_handlers.py` (72%) | +1% cov  |
| P2       | Thêm tests cho `workers.py` (67%)           | +1% cov  |
| P3       | `main_window.py` (0%) — khó test            | +4% cov  |

---

> **Tổng kết**: **650 tests, 77% coverage**. Codebase ổn định, không có test nào fail. Coverage giảm nhẹ do file splitting, cần bổ sung tests cho `page_handlers.py` và `settings_handlers.py` mới tách ra.
