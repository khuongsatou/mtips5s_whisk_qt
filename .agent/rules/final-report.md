# Final Report Rule

After completing a **significant task** or at the end of a **work session**, you **must** update `.manager/final_report.md` with the latest project status.

## When to update

- After completing a major feature or refactoring
- After a test coverage improvement round
- After fixing critical bugs
- At the end of any multi-step work session
- When the user explicitly requests a status update

## What to update

### 1. Date line

Set `**Date**` to today's date (`YYYY-MM-DD`).

### 2. Health Score by Role

Update star ratings (⭐ 1–5) and key metrics based on current state:

| Role                 | Score | Key Metric             |
| -------------------- | ----- | ---------------------- |
| 🎨 UI/UX Developer   | ⭐×N  | Widget count, themes   |
| ⚙️ Backend Developer | ⭐×N  | API status, models     |
| 🌐 i18n Specialist   | ⭐×N  | Languages, coverage    |
| 🧪 QA Engineer       | ⭐×N  | Coverage %, test count |
| 🚀 DevOps Engineer   | ⭐×N  | Build status           |

### 3. Overall Metrics

Update all values from latest test run and codebase state:

- Test files, total tests, code coverage
- Languages, themes, widgets, pages
- Known bugs (open count + fixed count)

### 4. Risk Register

- Update severity of existing risks based on progress
- Remove risks that are fully resolved (mark as ✅ Resolved)
- Add new risks discovered during work

### 5. Next Iteration Goals

Replace with **actionable next steps** based on remaining backlog from `.manager/current_task.md`. List 2–4 concrete goals.

## Rules

- **Never delete** resolved risks — change severity to `✅ Resolved`
- Keep star ratings **honest** — reflect actual module coverage and completeness
- Cross-reference `.manager/test-report.md` for accurate coverage numbers
- Cross-reference `.manager/current_task.md` for backlog status
