# Test Report Rule

After running tests (via `pytest` or the `/test-coverage` workflow), you **must** update `.manager/test-report.md` with the latest results.

## When to update

- After running `python3 -m pytest tests/` (full suite or subset)
- After running `python3 -m pytest tests/ --cov=app --cov-report=term-missing`
- After fixing failing tests and re-running

## What to update

### 1. Summary table

Update from pytest output:

| Metric      | Value               |
| ----------- | ------------------- |
| Total tests | _from output_       |
| Passed      | _count_ ✅          |
| Failed      | _count_ 🔴 (if any) |
| Coverage    | _overall %_         |
| Duration    | _time_              |

### 2. Date line

Set `**Date**` to today's date (`YYYY-MM-DD`).

### 3. Coverage by module tables

Update each module row with the latest `Stmts`, `Coverage`, and `Test File` from `--cov-report=term-missing`. Use these indicators:

- `100% ✅` or `≥90% ✅` — good
- `≥80%` — acceptable (no indicator)
- `<80%` — needs work (no indicator)
- `0% 🔴` — no tests

### 4. Bugs Found section

If tests revealed new bugs, add them to the bugs table with:

| Bug           | Owner  | Severity                  |
| ------------- | ------ | ------------------------- |
| _description_ | _role_ | 🔴 High / 🟡 Med / 🟢 Low |

## Rules

- **Never delete** historical bug entries — they serve as a record
- **Keep module grouping** by skill owner (UI/UX, Backend, i18n, Theme)
- Add new modules that appear in the codebase but are missing from the tables
- If a module reaches 0 missed lines, mark it `100% ✅`
