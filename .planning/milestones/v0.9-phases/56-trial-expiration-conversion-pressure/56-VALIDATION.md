---
phase: 56
slug: trial-expiration-conversion-pressure
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-18
---

# Phase 56 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (with async support) |
| **Config file** | `backend/pyproject.toml` |
| **Quick run command** | `cd backend && python -m pytest tests/test_trial.py -x -q` |
| **Full suite command** | `cd backend && python -m pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest tests/test_trial.py -x -q`
- **After every plan wave:** Run `cd backend && python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 56-01-01 | 01 | 1 | TRIAL-01 | unit | `cd backend && python -m pytest tests/test_trial.py::test_registration_trial_state -x` | ❌ W0 | ⬜ pending |
| 56-01-02 | 01 | 1 | TRIAL-02 | unit | `cd backend && python -m pytest tests/test_trial.py::test_trial_duration_config -x` | ❌ W0 | ⬜ pending |
| 56-01-03 | 01 | 1 | TRIAL-03 | unit | `cd backend && python -m pytest tests/test_trial.py::test_expired_trial_returns_402 -x` | ❌ W0 | ⬜ pending |
| 56-01-04 | 01 | 1 | TRIAL-03 | unit | `cd backend && python -m pytest tests/test_trial.py::test_exempt_paths_bypass_trial -x` | ❌ W0 | ⬜ pending |
| 56-01-05 | 01 | 1 | TRIAL-03 | unit | `cd backend && python -m pytest tests/test_trial.py::test_non_trial_users_unaffected -x` | ❌ W0 | ⬜ pending |
| 56-02-01 | 02 | 2 | TRIAL-04 | manual | Visual check in browser | N/A | ⬜ pending |
| 56-02-02 | 02 | 2 | TRIAL-05 | manual | Visual check in browser | N/A | ⬜ pending |
| 56-02-03 | 02 | 2 | TRIAL-06 | manual | Visual check in browser | N/A | ⬜ pending |
| 56-01-06 | 01 | 1 | TRIAL-07 | unit | `cd backend && python -m pytest tests/test_trial.py::test_trial_topup_blocked -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_trial.py` — stubs for TRIAL-01, TRIAL-02, TRIAL-03, TRIAL-07
- [ ] Test fixtures for mock User with `trial_expires_at` (in test file or `conftest.py`)

*Frontend component tests deferred — no test infrastructure for React components in project.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Trial banner renders for trial users | TRIAL-04 | React component, no frontend test infra | Log in as trial user, verify banner visible with days remaining and credit balance |
| Banner turns amber at 3 days / 10 credits | TRIAL-05 | Visual styling verification | Set trial to expire in 2 days or credits to 5, verify amber styling |
| Overlay blocks expired trial users | TRIAL-06 | Full-page overlay requires browser | Set trial_expires_at to past date, verify overlay blocks dashboard, "View Plans" links to /settings/plan |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
