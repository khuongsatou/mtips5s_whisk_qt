---
name: i18n Specialist
description: Responsible for internationalization system, translation files, language switching, and ensuring all UI text is properly localized for Vietnamese and English.
---

# i18n Specialist Skill

## Role Overview

The **i18n Specialist** owns:

- `Translator` class and language-switching mechanism
- Translation JSON files (`en.json`, `vi.json`)
- Ensuring all UI text uses translation keys (no hardcoded strings)

---

## File Ownership

| File                     | Description             |
| ------------------------ | ----------------------- |
| `app/i18n/translator.py` | Translation engine      |
| `app/i18n/en.json`       | English translations    |
| `app/i18n/vi.json`       | Vietnamese translations |

---

## Translation Key Namespaces

| Namespace | Example Keys                                                                                  |
| --------- | --------------------------------------------------------------------------------------------- |
| `app`     | `app.title`, `app.version`                                                                    |
| `nav`     | `nav.image_creator`, `nav.dashboard`, `nav.settings`                                          |
| `header`  | `header.theme_toggle`, `header.language`, `header.auto_mode`, `header.quota`, `header.logout` |
| `config`  | `config.title`, `config.add_to_queue`, `config.model`, `config.quality`, `config.ratio`       |
| `config`  | `config.images_per_prompt`, `config.concurrent_runs`, `config.delay_range`                    |
| `config`  | `config.ref_title`, `config.ref_scene`, `config.ref_style`, `config.output_folder`            |
| `config`  | `config.prompt`, `config.load_file`, `config.split_mode`, `config.filename_prefix`            |
| `queue`   | `queue.start`, `queue.stop`, `queue.delete`, `queue.select_all`, `queue.download`             |
| `status`  | `status.completed`, `status.running`, `status.pending`, `status.error`                        |
| `dialog`  | `dialog.confirm`, `dialog.cancel`, `dialog.save`                                              |

---

## Translator API

```python
class Translator(QObject):
    language_changed = Signal(str)

    def set_language(self, lang_code: str): ...
    def t(self, key: str) -> str: ...

    @property
    def current_language(self) -> str: ...

    @property
    def available_languages(self) -> list[str]: ...
```

---

## Widget Integration Pattern

Every widget that displays text must:

1. Accept `translator` in constructor
2. Use `self.translator.t("key")` for all visible text
3. Implement `retranslate()` method
4. Connect to `translator.language_changed` signal

---

## Adding a New Language

1. Copy `en.json` → `{lang_code}.json`
2. Translate all values
3. Add language code to `Translator.available_languages`
4. Add option in language dropdown (`app/widgets/header.py`)

---

## Quality Checklist

- [ ] All visible strings use `translator.t()` — zero hardcoded text
- [ ] Both `en.json` and `vi.json` have identical key sets
- [ ] Missing key returns the key itself (no crashes)
- [ ] Language switch updates all visible widgets immediately
