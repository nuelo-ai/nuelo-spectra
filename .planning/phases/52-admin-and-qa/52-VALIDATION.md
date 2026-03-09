---
phase: 52
slug: admin-and-qa
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-09
---

# Phase 52 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio |
| **Config file** | `backend/pytest.ini` (or `backend/pyproject.toml` — verify at implementation time) |
| **Quick run command** | `cd backend && python -m pytest tests/test_tier_gating.py -x -q` |
| **Full suite command** | `cd backend && python -m pytest tests/ -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest tests/test_tier_gating.py -x -q`
- **After every plan wave:** Run `cd backend && python -m pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 52-01-01 | 01 | 1 | ADMIN-01 | unit | `pytest tests/test_tier_gating.py::TestWorkspaceAccess -x -q` | ❌ W0 | ⬜ pending |
| 52-01-02 | 01 | 1 | ADMIN-01 | unit | `pytest tests/test_tier_gating.py::TestCollectionLimit -x -q` | ❌ W0 | ⬜ pending |
| 52-01-03 | 01 | 1 | ADMIN-01 | unit | `pytest tests/test_tier_gating.py::TestUnlimitedTiers -x -q` | ❌ W0 | ⬜ pending |
| 52-02-01 | 02 | 2 | ADMIN-02 | unit | `pytest tests/test_tier_gating.py -x -q` | ❌ W0 | ⬜ pending |
| 52-02-02 | 02 | 2 | ADMIN-02 | manual | `52-SMOKE-TEST.md` flow 3 | ❌ W0 | ⬜ pending |
| 52-02-03 | 02 | 2 | ADMIN-02 | manual | `52-SMOKE-TEST.md` flow 4 | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_tier_gating.py` — tier gating test stubs for ADMIN-01 (workspace access, collection limit, unlimited tiers)
- [ ] `52-SMOKE-TEST.md` — manual QA checklist (4 flows: tier access gating UI, collection + Pulse flow, credit cost display, admin settings round-trip)

*No new test framework install needed — pytest already configured.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Credit cost display updates after admin changes `workspace_credit_cost_pulse` | ADMIN-02 | Requires live admin portal + workspace UI interaction; 5-min cache TTL | `52-SMOKE-TEST.md` flow 4 |
| `free` tier user sees access-gated UI state at `/workspace` | ADMIN-01 | Frontend access-gated state rendering requires browser | `52-SMOKE-TEST.md` flow 1 |
| Full Pulse flow: create collection → upload → trigger → verify results | ADMIN-02 | End-to-end browser flow | `52-SMOKE-TEST.md` flow 2 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
