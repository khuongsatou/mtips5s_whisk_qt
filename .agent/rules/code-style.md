---
description: Python code style and formatting conventions for Whisk Desktop
---

# Code Style Rules

## Python Version

- Target **Python 3.9+** — no walrus operators in critical paths
- Use type hints: `def foo(x: str) -> int:`
- Use `list[str]` (PEP 585) instead of `typing.List[str]`

## File Header

Every `.py` file MUST start with a module docstring:

```python
"""
Whisk Desktop — <Module Name>.

<One-line purpose description>.
"""
```

## Imports

Order (separated by blank lines):

1. Standard library
2. Third-party (`PySide6`, `requests`, etc.)
3. Local (`app.xxx`)

```python
import os
from pathlib import Path

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal, Qt

from app.api.models import ApiResponse
from app.i18n.translator import Translator
```

## Naming

| Element           | Convention  | Example                          |
| ----------------- | ----------- | -------------------------------- |
| Classes           | PascalCase  | `ConfigPanel`, `TaskQueueTable`  |
| Functions/methods | snake_case  | `load_data()`, `_setup_ui()`     |
| Private methods   | `_` prefix  | `_on_save()`, `_build_card()`    |
| Signals           | snake_case  | `add_to_queue`, `login_success`  |
| Constants         | UPPER_SNAKE | `MODELS`, `LEVEL_COLORS`         |
| Files             | snake_case  | `config_panel.py`, `mock_api.py` |

## Class Structure

Order inside a class:

1. Class-level constants (`MODELS = [...]`)
2. Qt Signals (`add_to_queue = Signal(dict)`)
3. `__init__`
4. `_setup_ui` (if widget)
5. Public methods
6. Private methods (`_on_xxx`, `_build_xxx`)
7. `retranslate` (if i18n-aware)

## Docstrings

- Classes: one-line docstring minimum
- Public methods: docstring with Args/Returns when non-obvious
- Private methods: optional, but recommended for complex logic

## Line Length

- Soft limit: **100 characters**
- Hard limit: **120 characters**

## No Magic Numbers

Use named constants or config values. Bad: `self.setFixedWidth(350)`. Better: `PANEL_WIDTH = 350`.
