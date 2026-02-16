---
description: Testing conventions, fixtures, and coverage targets for Whisk Desktop
---

# Testing Rules

## Stack

- **pytest** ≥ 8.0
- **pytest-qt** ≥ 4.3 (PySide6 widget testing)
- **pytest-cov** ≥ 4.0 (coverage reporting)

## File Naming

- Test file: `tests/test_<module_name>.py`
- One test file per source module
- Mirror the `app/` structure in file names

## Test Structure

```python
"""
Tests for <ModuleName> — <brief description>.
"""
import pytest
from unittest.mock import MagicMock

class Test<Feature>:
    """Test <what this group covers>."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, translator):
        self.widget = SomeWidget(translator)
        qtbot.addWidget(self.widget)

    def test_<specific_behavior>(self):
        assert ...
```

## Shared Fixtures (from `conftest.py`)

| Fixture         | Type           | Notes           |
| --------------- | -------------- | --------------- |
| `theme_manager` | `ThemeManager` | Fresh instance  |
| `translator`    | `Translator`   | English default |
| `mock_api`      | `MockApi`      | Cleared queue   |

## Rules

1. **Always use `qtbot.addWidget()`** for widgets — ensures cleanup
2. **Never use `widget.show()` or `widget.isVisible()`** — use internal state instead
3. **Mock external APIs** with `MagicMock`, not real HTTP calls
4. **Use `qtbot.waitSignal()`** to verify signal emissions
5. **Don't test PySide6 internals** — only test our logic
6. **Each test method tests ONE behavior** — keep focused
7. **Test names are descriptive**: `test_empty_key_shows_error`, not `test1`

## Coverage Targets

| Layer       |  Target   | Current |
| ----------- | :-------: | :-----: |
| widgets/    | **≥ 85%** |   ✅    |
| pages/      | **≥ 85%** |   ✅    |
| api/ (mock) | **≥ 60%** |   ✅    |
| auth/       | **≥ 60%** | 🟡 41%  |
| Overall     | **≥ 70%** | 🟡 67%  |

## Commands

```bash
# Run all tests
python3 -m pytest tests/ -v --tb=short

# Run with coverage
python3 -m pytest tests/ --cov=app --cov-report=term-missing

# Run single file
python3 -m pytest tests/test_config_panel.py -v

# Run single test
python3 -m pytest tests/test_config_panel.py::TestConfigPanelDefaults::test_model_default -v
```

## Anti-Patterns (DO NOT)

- ❌ Don't use `time.sleep()` — use `qtbot.waitSignal()` or `waitUntil()`
- ❌ Don't create `QApplication` manually — `pytest-qt` handles it
- ❌ Don't write tests that depend on execution order
- ❌ Don't mock Qt internal classes (QLabel, QVBoxLayout, etc.)
- ❌ Don't test visual appearance (pixel colors, exact sizes)
