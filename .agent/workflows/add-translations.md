---
description: Add or update translation strings for Vietnamese and English
---

# Add Translations

## Steps

1. **Identify all new user-facing strings** in your code changes
   - Search for hardcoded strings in Python files
   - Each string should become a `translator.t("key")` call

2. **Determine the key names** following the naming convention:
   - Format: `<page_or_widget>.<element>`
   - Examples: `config.model`, `login.button`, `cookie.title`

3. **Add keys to English file** (`app/i18n/en.json`)

4. **Add keys to Vietnamese file** (`app/i18n/vi.json`)

// turbo

5. **Verify no missing keys**

```bash
cd /Users/apple/Desktop/extension/mtips5s_whisk && python3 -c "
import json
with open('app/i18n/en.json') as f: en = set(json.load(f).keys())
with open('app/i18n/vi.json') as f: vi = set(json.load(f).keys())
missing_vi = en - vi
missing_en = vi - en
if missing_vi: print(f'Missing in vi.json: {missing_vi}')
if missing_en: print(f'Missing in en.json: {missing_en}')
if not missing_vi and not missing_en: print('✅ All keys match!')
"
```

// turbo

6. **Verify translations load correctly**

```bash
cd /Users/apple/Desktop/extension/mtips5s_whisk && python3 -c "
from app.i18n.translator import Translator
t = Translator()
print(f'EN keys: {len(t._translations)}')
t.set_language('vi')
print(f'VI keys: {len(t._translations)}')
print('✅ Both languages load OK')
"
```

## Key Naming Rules

| Prefix        | Usage                  | Example             |
| ------------- | ---------------------- | ------------------- |
| `nav.*`       | Sidebar navigation     | `nav.dashboard`     |
| `config.*`    | Config panel           | `config.model`      |
| `login.*`     | Login dialog           | `login.button`      |
| `project.*`   | Project manager        | `project.title`     |
| `cookie.*`    | Cookie manager         | `cookie.add`        |
| `settings.*`  | Settings page          | `settings.theme`    |
| `toolbar.*`   | Queue toolbar tooltips | `toolbar.run_all`   |
| `queue.*`     | Queue table headers    | `queue.status`      |
| `dashboard.*` | Dashboard page         | `dashboard.welcome` |

## Rules

- **EVERY key added to `en.json` MUST also be in `vi.json`** (and vice versa)
- Keys are lowercase, dot-separated for hierarchy, underscores within segments
- Never delete a key without removing all `translator.t()` references first
