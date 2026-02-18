# Current Task

## Active: Cookie Management & UX Polish (Session 2026-02-18)

**Status:** ✅ Completed

### Completed Items

- [x] Dedicated "Get Cookie" button in bridge dashboard
- [x] Extension: extract `__Secure-next-auth.session-token` from `labs.google`
- [x] Bridge server: `POST /bridge/cookie` + `GET /bridge/cookie` endpoints
- [x] Extension popup: cookie POST status feedback (✅/⚠️)
- [x] Separate Start Cookie / Stop Cookie toggle (2h sync)
- [x] Auto-fetch cookie on Cookie Manager dialog open
- [x] Fixed Get Cookie freeze (Qt Signal instead of QTimer from threads)
- [x] Suppress noisy GET /bridge/cookie logs
- [x] Cookie endpoint API docs in dashboard
- [x] New Workflow button loading state (background thread)

### Backlog

- [ ] Persistent cookie storage on bridge (survive app restart)
- [ ] Chrome alarms API for MV3 background sync
- [ ] Cookie integration tests
