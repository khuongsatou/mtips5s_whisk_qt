---
description: Step-by-step workflow to add a new dialog widget to the Whisk Desktop app
---

# Add New Dialog

## Inputs

- `DIALOG_NAME`: e.g., `export` (snake_case)
- `CLASS_NAME`: e.g., `ExportDialog` (PascalCase)

## Steps

1. **Create the dialog file** at `app/widgets/<DIALOG_NAME>_dialog.py`

```python
"""
Whisk Desktop — <CLASS_NAME>.

<Description of this dialog>.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QCursor


class <CLASS_NAME>(QDialog):
    """<One-line description>."""

    # Signals
    action_completed = Signal()

    def __init__(self, api, translator, parent=None):
        super().__init__(parent)
        self.api = api
        self.translator = translator
        self.setObjectName("<DIALOG_NAME>_dialog")
        self.setModal(True)
        self.setMinimumSize(700, 500)
        self.setWindowTitle(self.translator.t("<DIALOG_NAME>.title"))
        self.translator.language_changed.connect(self.retranslate)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Title
        title = QLabel(self.translator.t("<DIALOG_NAME>.title"))
        title.setObjectName("dialog_title")
        layout.addWidget(title)

        # Content area
        layout.addStretch()

        # Bottom buttons
        bottom = QHBoxLayout()
        bottom.addStretch()

        self._close_btn = QPushButton(self.translator.t("<DIALOG_NAME>.close"))
        self._close_btn.setObjectName("<DIALOG_NAME>_close_btn")
        self._close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self._close_btn.clicked.connect(self.accept)
        bottom.addWidget(self._close_btn)

        layout.addLayout(bottom)

    def retranslate(self):
        self.setWindowTitle(self.translator.t("<DIALOG_NAME>.title"))
        self._close_btn.setText(self.translator.t("<DIALOG_NAME>.close"))
```

2. **Add translation keys** to both `app/i18n/en.json` and `app/i18n/vi.json`

```json
{
  "<DIALOG_NAME>.title": "Dialog Title",
  "<DIALOG_NAME>.close": "Close"
}
```

3. **Wire up the dialog** from the calling widget/page
   - Import the dialog class
   - Create and `exec()` it when triggered

4. **Create test file** at `tests/test_<DIALOG_NAME>_dialog.py`

```python
"""
Tests for <CLASS_NAME>.
"""
import pytest

class Test<CLASS_NAME>Init:
    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator, mock_api):
        from app.widgets.<DIALOG_NAME>_dialog import <CLASS_NAME>
        self.dialog = <CLASS_NAME>(mock_api, translator)
        qtbot.addWidget(self.dialog)

    def test_window_title(self):
        assert self.dialog.windowTitle()

    def test_modal(self):
        assert self.dialog.isModal()

    def test_has_close_btn(self):
        assert self.dialog._close_btn is not None
```

// turbo

5. **Run tests to verify**

```bash
cd /Users/apple/Desktop/extension/mtips5s_whisk && python3 -m pytest tests/test_<DIALOG_NAME>_dialog.py -v
```
