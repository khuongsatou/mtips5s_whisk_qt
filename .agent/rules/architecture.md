---
description: Module architecture, dependency flow, and file placement rules
---

# Architecture Rules

## Directory Structure

```
app/
├── api/            # API layer (base, mock, real HTTP clients)
├── auth/           # Authentication (AuthManager, session)
├── i18n/           # Translations (en.json, vi.json, Translator)
├── pages/          # Full-page views (DashboardPage, SettingsPage, etc.)
├── theme/          # QSS stylesheets, icons, ThemeManager
├── widgets/        # Reusable UI components (dialogs, panels, toolbars)
├── app.py          # Application entry point
├── main_window.py  # Main window orchestration
└── utils.py        # Shared utilities
tests/              # Unit tests (mirrors app/ structure)
```

## Dependency Flow (Top → Bottom)

```
main_window.py
├── pages/*         ← Full pages, one per feature
│   ├── widgets/*   ← Reusable UI components
│   ├── api/*       ← Data access (mock or HTTP)
│   └── i18n/*      ← Translation strings
├── theme/*         ← Visual styling only
└── auth/*          ← Login/session management
```

### Rules

1. **widgets/** MUST NOT import from **pages/** (no circular deps)
2. **api/** MUST NOT import from **widgets/** or **pages/**
3. **pages/** CAN import from **widgets/**, **api/**, **i18n/**
4. **widgets/** CAN import from **api/models** (data types only), **i18n/**
5. **theme/** MUST NOT be imported by **api/** or **auth/**

## File Placement

| What                 | Where                              | Example                  |
| -------------------- | ---------------------------------- | ------------------------ |
| New page             | `app/pages/`                       | `analytics_page.py`      |
| New dialog           | `app/widgets/`                     | `export_dialog.py`       |
| New reusable widget  | `app/widgets/`                     | `progress_card.py`       |
| New API endpoint     | `app/api/`                         | `analytics_api.py`       |
| New test             | `tests/`                           | `test_analytics_page.py` |
| New translation keys | `app/i18n/en.json` + `vi.json`     | —                        |
| New QSS theme rules  | `app/theme/light.qss` + `dark.qss` | —                        |

## New Page Checklist

When creating a new page:

- [ ] Create `app/pages/<name>_page.py` with class `<Name>Page(QWidget)`
- [ ] Accept `translator` as first arg, connect `language_changed` signal
- [ ] Implement `retranslate()` method
- [ ] Add nav entry in `app/widgets/sidebar.py`
- [ ] Add page to stack in `app/main_window.py`
- [ ] Add translation keys to both `en.json` and `vi.json`
- [ ] Create `tests/test_<name>_page.py`

## New Dialog Checklist

When creating a new dialog:

- [ ] Create `app/widgets/<name>_dialog.py` with class `<Name>Dialog(QDialog)`
- [ ] Set `self.setModal(True)`
- [ ] Set object name: `self.setObjectName("<name>_dialog")`
- [ ] Accept `api` and `translator` as constructor args
- [ ] Add translation keys to both `en.json` and `vi.json`
- [ ] Create `tests/test_<name>_dialog.py`

## API Layer Rules

- All API methods MUST return `ApiResponse` (from `app.api.models`)
- `MockApi` extends `BaseApi` for local development
- Real HTTP clients (e.g., `CookieApi`) use `requests` directly
- Never call HTTP endpoints from widgets — always go through an API class
