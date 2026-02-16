# 📝 Requirements

> **Owner**: 📋 Project Manager (`project-manager/SKILL.md`)
> **Input from**: All skill roles

**Last updated**: 2026-02-15

---

## Product Vision

Whisk Desktop — PySide6 AI image generation tool with configurable queue, reference images, and persistent settings.

## Feature Status by Owner

### 🎨 UI/UX Developer (`ui-ux-developer/SKILL.md`)

- [x] Triadic theme engine (light/dark, purple-teal-amber)
- [x] Config Panel (model/quality/ratio/prompt/output)
- [x] Dynamic reference slots (1–5 per category)
- [x] Task queue table with animated progress bars
- [x] Reference image grid (3-column: Title/Scene/Style)
- [x] Collapsible sidebar navigation
- [x] Header with theme/language toggles
- [x] Pipeline step indicator (5 steps)
- [x] CollapsibleSection widget
- [x] ToggleSwitch widget (iOS-style animated)
- [ ] Keyboard navigation audit
- [ ] WCAG 2.1 AA color contrast check

### ⚙️ Backend Developer (`backend-developer/SKILL.md`)

- [x] Abstract `BaseApi` interface (ABC)
- [x] Data models (`TaskItem`, `ApiResponse`, `CookieItem`, `ProjectItem`, `TokenItem`)
- [x] Mock API implementation (`MockApi`)
- [x] Auth system (login/session persistence)
- [x] Cookie/Token manager dialogs
- [ ] Real API integration (`RealApi`)
- [ ] Batch prompt processing
- [ ] Export/import settings profiles

### 🌐 i18n Specialist (`i18n-specialist/SKILL.md`)

- [x] Translator engine (JSON-based)
- [x] English + Vietnamese translations
- [x] All widgets use `translator.t()` pattern
- [x] `retranslate()` on language switch

### 🧪 QA Engineer (`qa-engineer/SKILL.md`)

- [x] Test coverage ≥ 40% (currently 42%)
- [x] 163/163 tests passing
- [ ] Target 60% coverage
- [ ] Integration tests for page-level flows

### 🚀 DevOps Engineer (`devops-engineer/SKILL.md`)

- [x] Project setup + dependencies
- [ ] macOS `.app` bundle (PyInstaller)
- [ ] Windows `.exe` build
- [ ] CI/CD pipeline

## Non-Functional Requirements

| Area        | Requirement     | Status |
| ----------- | --------------- | ------ |
| Performance | Launch < 3s     | ✅     |
| Platforms   | macOS + Windows | 🔄     |
| Coverage    | ≥ 40%           | ✅ 42% |
| i18n        | EN + VI         | ✅     |
| Theming     | Light + Dark    | ✅     |
| Licensing   | PySide6 (LGPL)  | ✅     |
