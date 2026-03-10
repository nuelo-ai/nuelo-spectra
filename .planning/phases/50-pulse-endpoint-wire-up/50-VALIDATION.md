---
phase: 50
slug: pulse-endpoint-wire-up
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-07
---

# Phase 50 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + httpx (AsyncClient) |
| **Config file** | `backend/pyproject.toml` |
| **Quick run command** | `cd backend && pytest tests/test_pulse_endpoints.py -x -q` |
| **Full suite command** | `cd backend && pytest -x -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && pytest tests/test_pulse_endpoints.py -x -q`
- **After every plan wave:** Run `cd backend && pytest -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 50-01-01 | 01 | 0 | PULSE-01 | unit | `pytest tests/test_pulse_endpoints.py -x -q` | ❌ W0 | ⬜ pending |
| 50-01-02 | 01 | 1 | PULSE-01 | integration | `pytest tests/test_pulse_endpoints.py::test_trigger_pulse_202 -x` | ❌ W0 | ⬜ pending |
| 50-01-03 | 01 | 1 | PULSE-01 | integration | `pytest tests/test_pulse_endpoints.py::test_trigger_pulse_402 -x` | ❌ W0 | ⬜ pending |
| 50-01-04 | 01 | 1 | PULSE-01 | integration | `pytest tests/test_pulse_endpoints.py::test_trigger_pulse_409 -x` | ❌ W0 | ⬜ pending |
| 50-02-01 | 02 | 0 | PULSE-04 | unit | `pytest tests/test_pulse_endpoints.py -x -q` | ❌ W0 | ⬜ pending |
| 50-02-02 | 02 | 1 | PULSE-04 | integration | `pytest tests/test_pulse_endpoints.py::test_poll_pulse_run -x` | ❌ W0 | ⬜ pending |
| 50-02-03 | 02 | 1 | PULSE-05 | integration | `pytest tests/test_pulse_endpoints.py::test_poll_pulse_run_completed -x` | ❌ W0 | ⬜ pending |
| 50-02-04 | 02 | 1 | PULSE-05 | unit | `pytest tests/test_orphan_refund.py::test_orphan_refund_job -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_pulse_endpoints.py` — stubs for PULSE-01 (trigger 202/402/409), PULSE-04 (polling status), PULSE-05 (signals in completed response)
- [ ] `backend/tests/test_orphan_refund.py` — stubs for orphan-refund job logic (PULSE-05 success criteria 4)
- [ ] Verify pytest installed: `cd backend && python -m pytest --version`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| APScheduler orphan job fires on schedule (5-min interval) | PULSE-05 | Requires time-based trigger in live environment | Start server with `ENABLE_SCHEDULER=true`, trigger a run, kill the pipeline mid-flight, wait 10+ minutes, confirm run status=failed and credits refunded |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
