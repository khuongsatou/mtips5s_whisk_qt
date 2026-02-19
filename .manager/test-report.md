# 🧪 QA Coverage Report

> **Date**: 2026-02-19 13:13 (ICT)
> **Target**: 60% coverage
> **Result**: **76%** ✅ Target Achieved

---

## Summary

| Metric               | Value      |
| -------------------- | ---------- |
| Total tests          | **861**    |
| Pass rate            | **100%**   |
| Total statements     | 8,245      |
| Statements missed    | 2,007      |
| **Overall coverage** | **76%** ✅ |
| Runtime              | ~14s       |

---

## Modules Above 90%

| Module                    | Cover |
| ------------------------- | ----- |
| `preferences.py`          | 100%  |
| `theme_manager.py`        | 100%  |
| `build_sections.py`       | 100%  |
| `config_panel.py`         | 100%  |
| `collapsible_section.py`  | 100%  |
| `data_table.py`           | 100%  |
| `toggle_switch.py`        | 100%  |
| `prompt_normalizer.py`    | 97%   |
| `queue_toolbar.py`        | 97%   |
| `log_panel.py`            | 97%   |
| `auth_manager.py`         | 95%   |
| `status_badge.py`         | 95%   |
| `translator.py`           | 94%   |
| `sidebar.py`              | 99%   |
| `dashboard_page.py`       | 99%   |
| `update_dialog.py`        | 99%   |
| `token_manager_dialog.py` | 98%   |
| `login_dialog.py`         | 96%   |
| `styled_message_box.py`   | 92%   |
| `project_tab_bar.py`      | 91%   |

---

## Modules Below 60% (Need Improvement)

| Module                       | Stmts | Miss | Cover   | Notes                                  |
| ---------------------------- | ----- | ---- | ------- | -------------------------------------- |
| `captcha_sidecar_manager.py` | 189   | 189  | **0%**  | Puppeteer mode disabled — low priority |
| `app.py`                     | 21    | 21   | **0%**  | App entry point — hard to unit test    |
| `image_creator_page.py`      | 177   | 153  | **14%** | Page init/layout — UI-heavy            |
| `toast_notification.py`      | 39    | 31   | **21%** | Widget lifecycle — needs QTimer mock   |
| `main_window.py`             | 306   | 211  | **31%** | Tab mgmt, captcha lifecycle — complex  |
| `update_api.py`              | 31    | 21   | **32%** | HTTP client — needs mock               |
| `page_handlers.py`           | 665   | 404  | **39%** | Queue ops, generation — large module   |

---

## Modules 60-80% (Acceptable, Room for Growth)

| Module                      | Stmts | Miss | Cover |
| --------------------------- | ----- | ---- | ----- |
| `workers.py`                | 243   | 84   | 65%   |
| `workflow_api.py`           | 274   | 90   | 67%   |
| `task_queue_table.py`       | 650   | 213  | 67%   |
| `captcha_bridge_server.py`  | 205   | 66   | 68%   |
| `header.py`                 | 151   | 37   | 75%   |
| `project_manager_dialog.py` | 341   | 78   | 77%   |

---

## Coverage by Component

| Component    | Avg Coverage |
| ------------ | ------------ |
| API layer    | ~75%         |
| Auth         | 95%          |
| Config panel | ~95%         |
| Theme        | 100%         |
| i18n         | 94%          |
| Widgets      | ~85%         |
| Pages        | ~50%         |
| Captcha      | ~34%         |

---

## Recommendations

### High Impact (Biggest Coverage Gains)

1. **`page_handlers.py`** (39% → target 60%) — Add tests for queue ops and generation flow with mocked API
2. **`task_queue_table.py`** (67% → target 80%) — Test sort, filter, refresh paths
3. **`main_window.py`** (31% → target 50%) — Test tab management and captcha mode switching

### Low Priority

4. **`captcha_sidecar_manager.py`** (0%) — Puppeteer is disabled, skip
5. **`app.py`** (0%) — Entry point, integration test territory
6. **`toast_notification.py`** (21%) — Small widget, low impact

---

## Conclusion

At **76% overall coverage**, the project **exceeds the 60% target** by 16 percentage points. Core modules (auth, config, theme, i18n, most widgets) are at 90%+ coverage. The main gaps are in page-level code (`page_handlers`, `image_creator_page`) and the disabled puppeteer sidecar.
