---
description: Quick health check — run tests, verify app launch, check translations
---

# Quick Health Check

Run this after major changes to verify nothing is broken.

## Steps

// turbo-all

1. **Run all tests**

```bash
cd /Users/apple/Desktop/extension/mtips5s_whisk && python3 -m pytest tests/ -q --tb=line
```

2. **Check for import errors**

```bash
cd /Users/apple/Desktop/extension/mtips5s_whisk && python3 -c "
from app.main_window import MainWindow
from app.pages.dashboard_page import DashboardPage
from app.pages.image_creator_page import ImageCreatorPage
from app.pages.items_page import ItemsPage
from app.pages.settings_page import SettingsPage
from app.widgets.config_panel import ConfigPanel
from app.widgets.task_queue_table import TaskQueueTable
from app.widgets.project_manager_dialog import ProjectManagerDialog
from app.widgets.cookie_manager_dialog import CookieManagerDialog
from app.widgets.token_manager_dialog import TokenManagerDialog
from app.widgets.login_dialog import LoginDialog
print('✅ All imports OK')
"
```

3. **Verify translation key parity**

```bash
cd /Users/apple/Desktop/extension/mtips5s_whisk && python3 -c "
import json
with open('app/i18n/en.json') as f: en = set(json.load(f).keys())
with open('app/i18n/vi.json') as f: vi = set(json.load(f).keys())
missing_vi = en - vi
missing_en = vi - en
if missing_vi: print(f'⚠️ Missing in vi.json: {sorted(missing_vi)}')
if missing_en: print(f'⚠️ Missing in en.json: {sorted(missing_en)}')
if not missing_vi and not missing_en: print('✅ Translation keys match')
"
```

4. **Check for hardcoded strings (potential i18n misses)**

```bash
cd /Users/apple/Desktop/extension/mtips5s_whisk && grep -rn 'setText("' app/pages/ app/widgets/ --include="*.py" | grep -v 'translator\|setObjectName\|#\|emoji\|→\|✅\|❌\|🔑\|🍪\|📋' | head -20
```

## Expected Results

- Step 1: All tests pass (0 failures)
- Step 2: "All imports OK" printed
- Step 3: "Translation keys match" printed
- Step 4: Ideally empty (no hardcoded strings)
