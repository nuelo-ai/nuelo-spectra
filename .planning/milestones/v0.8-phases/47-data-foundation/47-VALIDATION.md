---
phase: 47
slug: data-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-06
---

# Phase 47 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >= 8.0.0 + pytest-asyncio >= 0.23.0 |
| **Config file** | backend/pyproject.toml (dev dependency) |
| **Quick run command** | `cd backend && python -m pytest tests/ -x -q` |
| **Full suite command** | `cd backend && python -m pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest tests/ -x -q`
- **After every plan wave:** Run `cd backend && python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 47-01-01 | 01 | 0 | -- | unit (smoke) | `cd backend && python -m pytest tests/test_models_import.py -x` | No - W0 | pending |
| 47-01-02 | 01 | 0 | ADMIN-01 | unit | `cd backend && python -m pytest tests/test_user_classes_workspace.py -x` | No - W0 | pending |
| 47-01-03 | 01 | 0 | ADMIN-02 | unit | `cd backend && python -m pytest tests/test_platform_settings_pulse.py -x` | No - W0 | pending |
| 47-02-01 | 02 | 1 | -- | unit (smoke) | `cd backend && python -c "from app.models import Collection, CollectionFile, Signal, Report, PulseRun, pulse_run_files"` | N/A | pending |
| 47-02-02 | 02 | 1 | ADMIN-01 | unit | `cd backend && python -m pytest tests/test_user_classes_workspace.py -x` | W0 | pending |
| 47-02-03 | 02 | 1 | ADMIN-02 | unit | `cd backend && python -m pytest tests/test_platform_settings_pulse.py -x` | W0 | pending |
| 47-03-01 | 03 | 2 | -- | integration | `cd backend && alembic upgrade head` | N/A | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_models_import.py` — smoke test that all new models import without errors from app.models
- [ ] `backend/tests/test_user_classes_workspace.py` — validates workspace_access and max_active_collections fields exist with correct values for all 5 tiers (ADMIN-01)
- [ ] `backend/tests/test_platform_settings_pulse.py` — validates workspace_credit_cost_pulse in DEFAULTS, VALID_KEYS, and validate_setting() accepts/rejects correct values (ADMIN-02)

*Existing infrastructure covers framework installation — pytest already configured.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `alembic upgrade head` creates all tables with correct columns and FKs | SC-1 | Requires live database connection | Run `alembic upgrade head` against dev DB, verify tables exist with `\dt` in psql |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
