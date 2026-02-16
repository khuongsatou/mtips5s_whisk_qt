---
description: Git commit and branch conventions for Whisk Desktop
---

# Git Rules

## Commit Messages

Format: `[task_id] nội_dung_task`

Where:

- `task_id` — short identifier for the task (e.g. `feat_queue`, `fix_auth`, `test_coverage`)
- `nội_dung_task` — brief description of what was done

### Task ID Prefixes

| Prefix     | When                                    |
| ---------- | --------------------------------------- |
| `feat`     | New feature or page                     |
| `fix`      | Bug fix                                 |
| `test`     | Adding or updating tests                |
| `refactor` | Code restructuring (no behavior change) |
| `style`    | QSS/theme changes, formatting           |
| `docs`     | Documentation, README, SKILL.md         |
| `chore`    | Dependencies, config, CI                |
| `i18n`     | Translation updates                     |

### Examples

```
[feat_queue] add open folder button to progress column
[fix_config] resolve AttributeError on concurrency spinbox
[test_coverage] add tests for 7 modules below 80%
[style_theme] update dark mode button hover colors
[i18n_vi] translate cookie manager dialog
[refactor_api] split base URLs for admin vs generation
[feat_workflow] auto-add to queue after workflow link
[docs_rules] add task tracking and test report rules
```

## Auto-Commit After Task

After completing a task, the agent should:

1. **Stage changes**: `git add .`
2. **Commit** with the convention: `git commit -m "[task_id] description"`
3. **Push** to remote: `git push origin main`

> **Important**: Only commit after all tests pass and the task is verified.

## Branch Naming

Format: `<type>/<short-description>`

```
feat/cookie-manager
fix/login-status-visibility
test/zero-coverage-modules
```

## Rules

1. **One logical change per commit** — don't mix features with bug fixes
2. **Run tests before committing**: `python3 -m pytest tests/ -q`
3. **Never commit** `__pycache__/`, `.pyc`, `.DS_Store`, `*.egg-info/`
4. **Keep `.gitignore` updated** for build artifacts (`dist/`, `build/`)
