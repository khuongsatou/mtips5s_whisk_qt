# Task Tracking Rule

After completing **every task** (before the final `notify_user` call), you **must** update `.manager/current_task.md` to reflect the work just finished.

## What to update

1. **Status** — set to the current state:
   - `✅ idle` — no active work
   - `🔄 in progress` — mid-task (if pausing for user input)
   - `✅ completed` — just finished a task

2. **Updated** — set to today's date (`YYYY-MM-DD`)

3. **Active Task** — describe what was just done or what is in progress:
   - If idle: `_No active task._`
   - If completed: brief summary of what was done, e.g. `Added auto-add to queue after workflow link`

4. **Backlog** — update the status of any backlog items that were addressed:
   - `⬜ Not Started` → `🔄 In Progress` → `✅ Done`
   - Add new items discovered during the task
   - Re-prioritize if needed

## Format

Keep the existing file structure intact:

```markdown
# 📋 Current Task

> **Owner**: 📋 Project Manager (`project-manager/SKILL.md`)

**Status**: ✅ idle
**Updated**: 2026-02-16
**Iteration**: #N

---

## Active Task

_Summary of current/last completed task._

## Backlog

| Priority | Task | Owner | Status |
| -------- | ---- | ----- | ------ |
| P0       | ...  | ...   | ...    |

## Blockers

_None._
```

## Rules

- **Never delete** existing backlog items — only update their status
- **Increment Iteration** number when starting a new major task
- Keep descriptions **concise** (one line per item)
