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

> [!IMPORTANT]
> **Mandatory Rule**: When the user requests a project status report (`báo cáo tiến độ`), you **MUST** update the following files:
>
> 1. `.manager/progress-report.md` — Full project report with metrics, features, coverage, architecture
> 2. `.manager/current_task.md` — Current active task + backlog status
> 3. `.agent/skills/project-manager/SKILL.md` — Feature Status table + Key Files table

---

## Current Feature Status

| Feature                                 | Status  | Owner       |
| --------------------------------------- | ------- | ----------- |
| Theme Engine (light/dark)               | ✅ Done | UI/UX Dev   |
| i18n System (en/vi)                     | ✅ Done | i18n        |
| Auth System (login/session)             | ✅ Done | Backend Dev |
| Config Panel (model/quality/ratio)      | ✅ Done | UI/UX Dev   |
| Dynamic Reference Slots (1-5)           | ✅ Done | UI/UX Dev   |
| Task Queue Table                        | ✅ Done | UI/UX Dev   |
| Reference Image Grid (3-column)         | ✅ Done | UI/UX Dev   |
| Animated Progress Bars                  | ✅ Done | UI/UX Dev   |
| Config Persistence (QSettings)          | ✅ Done | UI/UX Dev   |
| Clear/Reset Config                      | ✅ Done | UI/UX Dev   |
| Output Thumbnails (adaptive grid)       | ✅ Done | UI/UX Dev   |
| Mock API (TaskItem model)               | ✅ Done | Backend Dev |
| Sidebar (collapsible)                   | ✅ Done | UI/UX Dev   |
| Header (toggles, user info)             | ✅ Done | UI/UX Dev   |
| Cookie/Token Manager                    | ✅ Done | Backend Dev |
| Project Manager Dialog                  | ✅ Done | UI/UX Dev   |
| Real API Integration                    | ✅ Done | Backend Dev |
| Background Image Generation             | ✅ Done | Backend Dev |
| Concurrent Generation (threads)         | ✅ Done | Backend Dev |
| Real-time Progress Tracking             | ✅ Done | UI/UX Dev   |
| Image Preview Modal + Download          | ✅ Done | UI/UX Dev   |
| Styled Message Box (custom dialog)      | ✅ Done | UI/UX Dev   |
| Queue Checkpoint (save/load)            | ✅ Done | Backend Dev |
| Error Message Column                    | ✅ Done | UI/UX Dev   |
| Cookie from Project Dialog              | ✅ Done | UI/UX Dev   |
| Split Base URLs (admin/labs)            | ✅ Done | Backend Dev |
| Cross-Platform Build (macOS .app)       | ✅ Done | DevOps      |
| Prompt Normalizer (text/JSON)           | ✅ Done | Backend Dev |
| Per-Task Timeout (2min)                 | ✅ Done | Backend Dev |
| Lightweight Progress Updates            | ✅ Done | UI/UX Dev   |
| Scroll Position Preservation            | ✅ Done | UI/UX Dev   |
| Re-run Completed Tasks                  | ✅ Done | Backend Dev |
| Project-based Save Paths                | ✅ Done | Backend Dev |
| Emoji Log Messages                      | ✅ Done | DevOps      |
| Workflow Persistence (QSettings)        | ✅ Done | Backend Dev |
| Download All Button                     | ✅ Done | UI/UX Dev   |
| Add-to-Queue State Management           | ✅ Done | UI/UX Dev   |
| Per-Project Queue Isolation             | ✅ Done | Backend Dev |
| Cookie Expiration Validation            | ✅ Done | Backend Dev |
| Threaded Login with Loading             | ✅ Done | UI/UX Dev   |
| Disabled Button Styling                 | ✅ Done | UI/UX Dev   |
| Flow Name in Save Paths                 | ✅ Done | Backend Dev |
| Timeout Countdown (⏱ elapsed)           | ✅ Done | UI/UX Dev   |
| Auto-Retry Failed Tasks                 | ✅ Done | Backend Dev |
| Prompt Search Filter                    | ✅ Done | UI/UX Dev   |
| Status Filter (toolbar)                 | ✅ Done | UI/UX Dev   |
| Toast Notifications (batch done)        | ✅ Done | UI/UX Dev   |
| Select All Errors (⚠️ button)           | ✅ Done | UI/UX Dev   |
| Task Count Statistics (toolbar)         | ✅ Done | UI/UX Dev   |
| Stuck Task Cleanup (on reload)          | ✅ Done | Backend Dev |
| Prompt Count (config panel)             | ✅ Done | UI/UX Dev   |
| Max 300 Prompt Validation               | ✅ Done | Backend Dev |
| AI Fix Buttons (GPT/Gemini)             | ✅ Done | UI/UX Dev   |
| Copy All Prompts (header click)         | ✅ Done | UI/UX Dev   |
| Completion Timestamp Column             | ✅ Done | UI/UX Dev   |
| Sort by Newest Completed                | ✅ Done | Backend Dev |
| Ref Mode Toggle Buttons (UI)            | ✅ Done | UI/UX Dev   |
| Per-Category Get ID (title/scene/style) | ✅ Done | UI/UX Dev   |
| Background Ref Upload (QThread)         | ✅ Done | Backend Dev |
| Crash Fix (deleteLater race)            | ✅ Done | Backend Dev |
| Completion Timestamp Persistence        | ✅ Done | Backend Dev |
| File Splitting Rule (>500 lines)        | ✅ Done | DevOps      |
| Token Refresh + Server Logout           | ✅ Done | Backend Dev |
| Auto-Recovery Login Cascade             | ✅ Done | Backend Dev |
| Dynamic Timeout Budget (60s)            | ✅ Done | Backend Dev |
| Single Mode Preload Injection           | ✅ Done | Backend Dev |
| Ref Image Persistence Fix (from_dict)   | ✅ Done | Backend Dev |
| Sort Toggle on DONE AT Column           | ✅ Done | UI/UX Dev   |
| Dashboard Statistics Page               | ✅ Done | UI/UX Dev   |
| Per-Project Dashboard Stats             | ✅ Done | UI/UX Dev   |
| Google Credits (Cookie Manager)         | ✅ Done | Backend Dev |
| Language Switcher Redesign (pill)       | ✅ Done | UI/UX Dev   |
| Sidebar Logo Redesign + Branding        | ✅ Done | UI/UX Dev   |
| Preferences Persistence (theme/lang)    | ✅ Done | Backend Dev |
| Search Input Redesign (pill shape)      | ✅ Done | UI/UX Dev   |
| Cancel Running Tasks (⏹)                | ✅ Done | UI/UX Dev   |
| AI Prompt Generator (ChatGPT/Gemini)    | ✅ Done | UI/UX Dev   |
| Saved Prompts CRUD (local JSON)         | ✅ Done | UI/UX Dev   |
| Captcha Bridge Server (Extension HTTP)  | ✅ Done | Backend Dev |
| Captcha Sidecar Manager (Puppeteer)     | ✅ Done | Backend Dev |
| Captcha Bridge Landing Page (:18923)    | ✅ Done | UI/UX Dev   |
| Video Status Polling (async)            | ✅ Done | Backend Dev |
| Manual Refresh Button (🔄 per queue)    | ✅ Done | UI/UX Dev   |
| Video Thumbnail Output (ffmpeg)         | ✅ Done | UI/UX Dev   |
| Configurable Poll Interval (📡)         | ✅ Done | UI/UX Dev   |
| Configurable API Timeout (⏱)            | ✅ Done | Backend Dev |
| Video Download from fifeUrl             | ✅ Done | Backend Dev |
| Cookie Bridge Sync (extension→bridge)   | ✅ Done | Backend Dev |
| Separate Start Cookie Toggle            | ✅ Done | UI/UX Dev   |
| Auto-Fetch Cookie on Dialog Open        | ✅ Done | Backend Dev |
| Cookie Bridge Dashboard Docs            | ✅ Done | UI/UX Dev   |
| New Workflow Loading State              | ✅ Done | UI/UX Dev   |
| Cookie Get Thread Safety (Signal)       | ✅ Done | Backend Dev |
| Bridge Log Noise Suppression            | ✅ Done | DevOps      |

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

| File                                                 | Lines | Purpose                                                     |
| ---------------------------------------------------- | ----- | ----------------------------------------------------------- |
| `requirements.txt`                                   | —     | Dependencies                                                |
| `main.py`                                            | 113   | App entry point — must launch without errors                |
| `app/pages/image_creator_page/page_handlers.py`      | 1,130 | Queue ops, generation, polling, refresh, auth helpers       |
| `app/pages/image_creator_page/image_creator_page.py` | 287   | Page init, layout, signal wiring                            |
| `app/pages/image_creator_page/workers.py`            | 475   | GenerationWorker + RefUploadWorker + polling + download     |
| `app/widgets/task_queue_table/task_queue_table.py`   | 1,019 | Queue display, sort, refresh, thumbnails, AI fix, filters   |
| `app/widgets/config_panel/build_sections.py`         | 693   | Config panel UI (model, prompt, ref, output, poll, timeout) |
| `app/widgets/config_panel/settings_handlers.py`      | 535   | Config persistence, ref mode, pipeline, retranslation       |
| `app/api/mock_api/queue_ops.py`                      | 199   | Queue CRUD + checkpoint persistence                         |
| `app/api/mock_api/resource_ops.py`                   | 390   | Flow, cookie, token resource operations                     |
| `app/api/workflow_api/workflow_api.py`               | 706   | Whisk video generation + polling + upload API client        |
| `app/api/models.py`                                  | 456   | Data model definitions (TaskItem, FlowItem, etc.)           |
| `app/widgets/cookie_manager_dialog.py`               | 564   | Cookie CRUD, test & save, bridge sync, credit check         |
| `app/main_window.py`                                 | 504   | Tab management, menu wiring, captcha lifecycle              |
| `app/widgets/project_manager_dialog.py`              | 362   | Project CRUD, activate, cookie integration                  |
| `app/widgets/prompt_generator_dialog.py`             | 337   | AI prompt generator + saved prompts CRUD table              |
| `app/api/cookie_api.py`                              | 348   | Cookie/API-key REST client                                  |
| `app/pages/settings_page.py`                         | 324   | Settings page                                               |
| `app/auth/auth_manager.py`                           | 421   | Login, session, token refresh, logout, auto-recovery        |
| `app/widgets/styled_message_box.py`                  | 245   | Custom modal dialogs replacing QMessageBox                  |
| `app/widgets/reference_image_grid.py`                | 221   | Reference image display grid                                |
| `app/widgets/login_dialog.py`                        | 212   | Login modal with threaded API call + loading                |
| `app/widgets/queue_toolbar.py`                       | 217   | Search, status filter, pagination, stats, cancel running    |
| `app/api/flow_api.py`                                | 194   | Flow/project REST client                                    |
| `app/widgets/sidebar.py`                             | 195   | Collapsible sidebar navigation + branding                   |
| `app/widgets/header.py`                              | 266   | Page title, user info, theme/lang/captcha toggles           |
| `app/captcha_bridge_server.py`                       | 1,214 | HTTP server :18923 + cookie bridge + dashboard              |
| `app/captcha_sidecar_manager.py`                     | 304   | QThread subprocess wrapper (Puppeteer mode)                 |
| `pucaptcha/capture-sidecar.js`                       | 1,179 | Node.js Puppeteer sidecar (stdin/stdout protocol)           |
| `app/prompt_normalizer.py`                           | 114   | Prompt sanitization (plain text + JSON)                     |
| `app/preferences.py`                                 | 49    | Theme/language persistence                                  |
| `app/widgets/toast_notification.py`                  | 77    | Non-blocking auto-dismiss notifications                     |
| `app/theme/light.qss`                                | 1,695 | Light theme stylesheet                                      |
| `app/theme/dark.qss`                                 | 1,696 | Dark theme stylesheet                                       |
