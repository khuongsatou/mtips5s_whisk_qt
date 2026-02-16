---
description: Step-by-step workflow to add a new page to the Whisk Desktop app
---

# Add New Page

## Inputs

- `PAGE_NAME`: e.g., `analytics` (snake_case)
- `CLASS_NAME`: e.g., `AnalyticsPage` (PascalCase)

## Steps

1. **Create the page file** at `app/pages/<PAGE_NAME>_page.py`

```python
"""
Whisk Desktop — <CLASS_NAME>.

<Description of this page>.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class <CLASS_NAME>(QWidget):
    """<One-line description>."""

    def __init__(self, translator, api=None, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.api = api
        self.setObjectName("<PAGE_NAME>_page")
        self.translator.language_changed.connect(self.retranslate)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        self._title = QLabel(self.translator.t("<PAGE_NAME>.title"))
        self._title.setObjectName("page_title")
        layout.addWidget(self._title)

        layout.addStretch()

    def retranslate(self):
        self._title.setText(self.translator.t("<PAGE_NAME>.title"))
```

2. **Add translation keys** to both `app/i18n/en.json` and `app/i18n/vi.json`

```json
{
  "<PAGE_NAME>.title": "Page Title",
  "nav.<PAGE_NAME>": "Page Label"
}
```

3. **Add navigation entry** in `app/widgets/sidebar.py`
   - Add `"<PAGE_NAME>"` to the `NAV_ITEMS` list
   - Add the emoji icon mapping

4. **Register in MainWindow** (`app/main_window.py`)
   - Import `<CLASS_NAME>` from `app.pages.<PAGE_NAME>_page`
   - Create instance and add to the stacked widget
   - Update `_switch_page()` to handle the new page

5. **Create test file** at `tests/test_<PAGE_NAME>_page.py`

```python
"""
Tests for <CLASS_NAME> — <description>.
"""
import pytest

class Test<CLASS_NAME>Init:
    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        from app.pages.<PAGE_NAME>_page import <CLASS_NAME>
        self.page = <CLASS_NAME>(translator)
        qtbot.addWidget(self.page)

    def test_has_title(self):
        assert self.page._title is not None
        assert self.page._title.text()
```

// turbo

6. **Run tests to verify**

```bash
cd /Users/apple/Desktop/extension/mtips5s_whisk && python3 -m pytest tests/test_<PAGE_NAME>_page.py -v
```
