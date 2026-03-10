---
phase: 53
slug: shell-and-navigation-fixes
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-10
---

# Phase 53 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Manual visual inspection (no automated UI tests) |
| **Config file** | none |
| **Quick run command** | `cd frontend && npm run build` |
| **Full suite command** | `cd frontend && npm run build && npm run lint` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npm run build`
- **After every plan wave:** Run `cd frontend && npm run build && npm run lint`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 53-01-01 | 01 | 1 | LBAR-01 | build | `cd frontend && npm run build` | ✅ | ⬜ pending |
| 53-01-02 | 01 | 1 | LBAR-02 | build + manual | `cd frontend && npm run build` | ✅ | ⬜ pending |
| 53-02-01 | 02 | 1 | CHAT-01 | build | `cd frontend && npm run build` | ✅ | ⬜ pending |
| 53-02-02 | 02 | 1 | CHAT-02 | build + manual | `cd frontend && npm run build` | ✅ | ⬜ pending |
| 53-02-03 | 02 | 1 | CHAT-03 | build + manual | `cd frontend && npm run build` | ✅ | ⬜ pending |
| 53-03-01 | 03 | 1 | FILES-01 | build | `cd frontend && npm run build` | ✅ | ⬜ pending |
| 53-03-02 | 03 | 1 | FILES-02 | build + manual | `cd frontend && npm run build` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. No new test files needed — all phase behaviors are pure UI layout fixes verified by build success + manual visual inspection.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Leftbar toggle visible in Pulse Analysis | LBAR-01 | UI layout, no DOM assertion | Open Pulse Analysis section; confirm `SidebarTrigger` visible at top-left of main screen |
| Menu icon padding alignment | LBAR-02 | Visual alignment check | Open sidebar; confirm Pulse Analysis, Chat, Files, Admin Panel icons align horizontally |
| No Spectra logo in Chat panel | CHAT-01 | Visual element removal | Select Chat; confirm no gradient "S" logo or "Spectra" text in top-left of main panel |
| Rightbar expand toggle visible after collapse (new chat) | CHAT-02 | UI toggle visibility | In new chat, collapse rightbar; confirm expand button appears at top-right |
| Rightbar toggle at top-right (existing chat) | CHAT-03 | Layout position check | Open existing chat; confirm toggle is pinned to right edge, not centered |
| No Spectra logo in Files panel | FILES-01 | Visual element removal | Select Files; confirm no gradient "S" logo or "Spectra" text in top-left |
| Leftbar toggle at top of Files screen | FILES-02 | UI layout | Select Files; confirm `SidebarTrigger` is in fixed header above scrollable content |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
