---
phase: 54
slug: pulse-analysis-fixes
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-10
---

# Phase 54 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + pytest-asyncio |
| **Config file** | backend/pyproject.toml |
| **Quick run command** | `cd backend && python -m pytest tests/test_collections.py -x -q` |
| **Full suite command** | `cd backend && python -m pytest tests/ -x -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest tests/test_collections.py -x -q`
- **After every plan wave:** Run `cd backend && python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green + manual visual check of all 5 requirements
- **Max feedback latency:** ~30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 54-01-01 | 01 | 1 | PULSE-01 | unit (backend) | `cd backend && python -m pytest tests/test_collections.py -x -q -k "credits"` | ❌ W0 | ⬜ pending |
| 54-01-02 | 01 | 1 | PULSE-01 | unit (backend) | `cd backend && python -m pytest tests/test_collections.py -x -q -k "credits"` | ❌ W0 | ⬜ pending |
| 54-02-01 | 02 | 1 | PULSE-04 | manual visual | N/A | ✅ | ⬜ pending |
| 54-02-02 | 02 | 1 | PULSE-05 | manual visual | N/A | ✅ | ⬜ pending |
| 54-03-01 | 03 | 2 | PULSE-02 | manual visual | N/A | ✅ | ⬜ pending |
| 54-04-01 | 04 | 2 | PULSE-03 | manual visual | N/A | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_collections.py` — add test for `credits_used` aggregate field in GET /collections/{id} response (PULSE-01)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Signal detail panel accessible on small screens | PULSE-02 | CSS class-based responsive layout — no programmatic assertion | Resize browser to <640px, click a signal, verify detail panel appears |
| "Chat with Spectra" button present between Analysis and Statistical Evidence | PULSE-03 | UI placement and full integration flow | Open Signal View, verify button location, click it, confirm new Chat session opens with collection files pre-linked |
| Activity history entries show date AND time | PULSE-04 | Frontend string rendering — no automated frontend test infra | Open Collection Overview Activity tab, verify entries show e.g. "Mar 10, 2026, 02:34 PM" |
| Files added list entries show date AND time | PULSE-05 | Frontend string rendering — no automated frontend test infra | Open Collection Overview Files tab, verify entries show date + time |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
