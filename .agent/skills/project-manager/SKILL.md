---
name: Project Manager
description: Tracks project progress, reports status, coordinates between team roles, and manages the timeline for the Whisk Desktop application.
---

# Project Manager Skill

## Role Overview

The **Project Manager** is responsible for:

- Tracking overall project progress
- Reporting status to the user/stakeholder
- Coordinating work between team roles (UI/UX, Backend, i18n, QA, DevOps)
- Identifying blockers and risks

---

## Current Feature Status

| Feature                            | Status  | Owner       |
| ---------------------------------- | ------- | ----------- |
| Theme Engine (light/dark)          | ✅ Done | UI/UX Dev   |
| i18n System (en/vi)                | ✅ Done | i18n        |
| Auth System (login/session)        | ✅ Done | Backend Dev |
| Config Panel (model/quality/ratio) | ✅ Done | UI/UX Dev   |
| Dynamic Reference Slots (1-5)      | ✅ Done | UI/UX Dev   |
| Task Queue Table                   | ✅ Done | UI/UX Dev   |
| Reference Image Grid (3-column)    | ✅ Done | UI/UX Dev   |
| Animated Progress Bars             | ✅ Done | UI/UX Dev   |
| Config Persistence (QSettings)     | ✅ Done | UI/UX Dev   |
| Clear/Reset Config                 | ✅ Done | UI/UX Dev   |
| Output Thumbnails (adaptive grid)  | ✅ Done | UI/UX Dev   |
| Mock API (TaskItem model)          | ✅ Done | Backend Dev |
| Sidebar (collapsible)              | ✅ Done | UI/UX Dev   |
| Header (toggles, user info)        | ✅ Done | UI/UX Dev   |
| Cookie/Token Manager               | ✅ Done | Backend Dev |
| Project Manager Dialog             | ✅ Done | UI/UX Dev   |
| Real API Integration               | ✅ Done | Backend Dev |
| Background Image Generation        | ✅ Done | Backend Dev |
| Concurrent Generation (threads)    | ✅ Done | Backend Dev |
| Real-time Progress Tracking        | ✅ Done | UI/UX Dev   |
| Image Preview Modal + Download     | ✅ Done | UI/UX Dev   |
| Styled Message Box (custom dialog) | ✅ Done | UI/UX Dev   |
| Queue Checkpoint (save/load)       | ✅ Done | Backend Dev |
| Error Message Column               | ✅ Done | UI/UX Dev   |
| Cookie from Project Dialog         | ✅ Done | UI/UX Dev   |
| Split Base URLs (admin/labs)       | ✅ Done | Backend Dev |
| Cross-Platform Build (macOS .app)  | ✅ Done | DevOps      |
| Prompt Normalizer (text/JSON)      | ✅ Done | Backend Dev |
| Per-Task Timeout (2min)            | ✅ Done | Backend Dev |
| Lightweight Progress Updates       | ✅ Done | UI/UX Dev   |
| Scroll Position Preservation       | ✅ Done | UI/UX Dev   |
| Re-run Completed Tasks             | ✅ Done | Backend Dev |
| Project-based Save Paths           | ✅ Done | Backend Dev |
| Emoji Log Messages                 | ✅ Done | DevOps      |
| Workflow Persistence (QSettings)   | ✅ Done | Backend Dev |
| Download All Button                | ✅ Done | UI/UX Dev   |
| Add-to-Queue State Management      | ✅ Done | UI/UX Dev   |
| Per-Project Queue Isolation        | ✅ Done | Backend Dev |
| Cookie Expiration Validation       | ✅ Done | Backend Dev |
| Threaded Login with Loading        | ✅ Done | UI/UX Dev   |
| Disabled Button Styling            | ✅ Done | UI/UX Dev   |
| Flow Name in Save Paths            | ✅ Done | Backend Dev |

---

## Team Coordination Map

| Role              | Skill File                   | Responsible For                       |
| ----------------- | ---------------------------- | ------------------------------------- |
| UI/UX Developer   | `ui-ux-developer/SKILL.md`   | Theme, widgets, pages, QSS styling    |
| Backend Developer | `backend-developer/SKILL.md` | API layer, data models, mock/real API |
| i18n Specialist   | `i18n-specialist/SKILL.md`   | Translations, language switching      |
| QA Engineer       | `qa-engineer/SKILL.md`       | Unit tests, coverage                  |
| DevOps Engineer   | `devops-engineer/SKILL.md`   | Setup, cross-platform builds          |

---

## Key Files to Monitor

| File                                    | Lines | Purpose                                             |
| --------------------------------------- | ----- | --------------------------------------------------- |
| `requirements.txt`                      | —     | Dependencies                                        |
| `main.py`                               | 97    | App entry point — must launch without errors        |
| `app/widgets/config_panel.py`           | 863   | Largest widget, most active development             |
| `app/pages/image_creator_page.py`       | 849   | Generation logic, worker threads, progress tracking |
| `app/widgets/task_queue_table.py`       | 559   | Core queue display, output grid, image preview      |
| `app/api/mock_api.py`                   | 733   | Mock API + checkpoint save/load                     |
| `app/api/models.py`                     | 451   | Data model definitions                              |
| `app/widgets/cookie_manager_dialog.py`  | 416   | Cookie CRUD, test & save flow                       |
| `app/main_window.py`                    | 384   | Tab management, menu wiring, theme switching        |
| `app/widgets/project_manager_dialog.py` | 362   | Project CRUD, activate, cookie integration          |
| `app/api/cookie_api.py`                 | 348   | Cookie/API-key REST client                          |
| `app/api/workflow_api.py`               | 317   | Whisk image generation API client                   |
| `app/auth/auth_manager.py`              | 306   | Login, session management, user profile             |
| `app/prompt_normalizer.py`              | 110   | Prompt sanitization (plain text + JSON)             |
| `app/widgets/styled_message_box.py`     | 245   | Custom modal dialogs replacing QMessageBox          |
| `app/widgets/login_dialog.py`           | 210   | Login modal with threaded API call + loading        |
| `app/theme/light.qss`                   | 1517  | Light theme stylesheet                              |
| `app/theme/dark.qss`                    | 1518  | Dark theme stylesheet                               |
