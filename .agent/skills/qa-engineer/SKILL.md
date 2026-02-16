---
name: QA Engineer
description: Responsible for unit tests, integration tests, test coverage, and quality assurance for the Whisk Desktop PySide6 application.
---

# QA Engineer Skill

## Role Overview

The **QA Engineer** owns:

- All test files in `tests/`
- Test coverage targets
- Test conventions and patterns
- Bug verification

---

## Test Stack

| Tool         | Purpose                                |
| ------------ | -------------------------------------- |
| `pytest`     | Test runner                            |
| `pytest-qt`  | Qt widget testing with `qtbot` fixture |
| `pytest-cov` | Coverage reporting                     |

---

## Test Conventions

1. **One test file per module**: `test_{module_name}.py`
2. **Descriptive names**: `test_{what}_{expected_result}`
3. **AAA pattern**: Arrange → Act → Assert
4. **Use fixtures**: Share setup via `conftest.py`

---

## Key Areas to Test

### Config Panel

- Default values are correct
- QSettings save/load/reset works
- Dynamic slot row creation (max 5)
- clear_inputs clears prompt and refs
- reset_to_defaults resets all values

### Task Queue Table

- Tasks render with correct columns
- images_per_prompt controls output placeholder count
- Running tasks show animated progress
- Reference images grid displays correctly

### Mock API

- add_to_queue stores all fields including `images_per_prompt`, `reference_images_by_cat`
- update_task modifies allowed fields
- delete_tasks re-indexes STT
- get_queue returns all tasks

### Reference Image Grid

- set_paths auto-expands slots up to 5
- set_paths_by_category handles case-insensitive keys
- Max 5 slots per column

---

## Running Tests

```bash
# All tests
python3 -m pytest tests/ -v --tb=short

# With coverage
python3 -m pytest tests/ -v --cov=app --cov-report=term-missing

# Single file
python3 -m pytest tests/test_mock_api.py -v

# Stop on first failure
python3 -m pytest tests/ -x -v
```
