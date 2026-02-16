---
description: PySide6 widget development patterns, signals, and theming rules
---

# UI Widget Rules

## Widget Constructor Pattern

Every widget MUST follow this constructor pattern:

```python
class MyWidget(QWidget):
    """One-line description."""

    # 1. Signals first
    some_action = Signal(str)

    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.setObjectName("my_widget")  # Required for QSS
        self.translator.language_changed.connect(self.retranslate)
        self._setup_ui()

    def _setup_ui(self):
        """Build the UI tree."""
        ...

    def retranslate(self):
        """Update texts when language changes."""
        ...
```

## Object Names

- Every widget that needs custom styling MUST have `setObjectName()`
- Use snake_case: `"config_panel"`, `"task_queue_table"`, `"login_dialog"`
- Buttons: `"<context>_<action>_btn"` → `"project_save_btn"`, `"cookie_close_btn"`

## Layout Rules

1. Use `QVBoxLayout` / `QHBoxLayout` for simple stacking
2. Use `QGridLayout` for grid-based content (e.g., 2×2 image thumbnails)
3. Set margins: `layout.setContentsMargins(12, 8, 12, 8)` (keep consistent)
4. Set spacing: `layout.setSpacing(6)` or `layout.setSpacing(8)`
5. Use `layout.addStretch()` to push content to edges

## Signals

- Define at class level (not in `__init__`)
- Use descriptive names: `add_to_queue`, `login_success`, `project_activated`
- Emit with typed data: `Signal(str)`, `Signal(dict)`, `Signal(str, str)`
- Connect in the owning widget, not in children

## Dialog Pattern

```python
class MyDialog(QDialog):
    """Modal dialog for X."""

    def __init__(self, api, translator, parent=None):
        super().__init__(parent)
        self.setObjectName("my_dialog")
        self.setModal(True)
        self.setMinimumSize(700, 500)
        self.setWindowTitle(translator.t("my_dialog.title"))
        self._setup_ui()
```

## Theming

- **NEVER hardcode colors in Python** — use QSS stylesheets
- Exception: dynamic colors computed at runtime (e.g., `LEVEL_COLORS` in LogPanel)
- Put static styles in `app/theme/light.qss` and `dark.qss`
- Reference widgets by object name: `#config_panel { ... }`

## Cursor

- Interactive elements MUST set `setCursor(QCursor(Qt.PointingHandCursor))`
- Non-interactive labels should NOT set cursor

## Icons & Emoji

- Use emoji for inline icons: `"🔑"`, `"🍪"`, `"📋"`
- Use theme icons from `app/theme/icons/` for toolbar buttons
- Prefix button text with emoji for visual identity

## Performance

- Use `QTimer.singleShot()` for delayed actions, never `time.sleep()`
- Use `QCoreApplication.processEvents()` sparingly (only for immediate UI refresh)
- Lazy-load heavy content (e.g., load cookies only when dialog opens)
