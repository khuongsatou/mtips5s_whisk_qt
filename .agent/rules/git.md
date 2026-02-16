---
description: Git commit and branch conventions for Whisk Desktop
---

# Git Rules

## Commit Messages

Format: `<type>(<scope>): <description>`

### Types

| Type       | When                                    |
| ---------- | --------------------------------------- |
| `feat`     | New feature or page                     |
| `fix`      | Bug fix                                 |
| `test`     | Adding or updating tests                |
| `refactor` | Code restructuring (no behavior change) |
| `style`    | QSS/theme changes, formatting           |
| `docs`     | Documentation, README, SKILL.md         |
| `chore`    | Dependencies, config, CI                |
| `i18n`     | Translation updates                     |

### Scopes

Use module name: `config`, `queue`, `auth`, `api`, `theme`, `settings`, `i18n`

### Examples

```
feat(queue): add error message column to task table
fix(config): resolve AttributeError on concurrency spinbox
test(widgets): add tests for LogPanel and QueueToolbar
style(theme): update dark mode button hover colors
i18n(vi): translate cookie manager dialog
refactor(api): split base URLs for admin vs generation
```

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
