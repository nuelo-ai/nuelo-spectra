---
phase: 49
slug: pulse-agent
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-06
---

# Phase 49 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (existing) |
| **Config file** | `backend/pyproject.toml` `[tool.pytest]` |
| **Quick run command** | `cd backend && python -m pytest tests/test_pulse_agent.py tests/test_pulse_service.py -x` |
| **Full suite command** | `cd backend && python -m pytest tests/ -x` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest tests/test_pulse_agent.py tests/test_pulse_service.py -x`
- **After every plan wave:** Run `cd backend && python -m pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 49-01-01 | 01 | 1 | PULSE-02 | unit | `cd backend && python -m pytest tests/test_pulse_service.py::test_credit_precheck_insufficient -x` | ❌ W0 | ⬜ pending |
| 49-01-02 | 01 | 1 | PULSE-02 | unit | `cd backend && python -m pytest tests/test_pulse_service.py::test_credit_precheck_sufficient -x` | ❌ W0 | ⬜ pending |
| 49-01-03 | 01 | 1 | PULSE-03 | unit | `cd backend && python -m pytest tests/test_pulse_service.py::test_credit_deduction_on_start -x` | ❌ W0 | ⬜ pending |
| 49-01-04 | 01 | 1 | PULSE-03 | unit | `cd backend && python -m pytest tests/test_pulse_service.py::test_credit_refund_on_failure -x` | ❌ W0 | ⬜ pending |
| 49-02-01 | 02 | 1 | SC-1 | unit | `cd backend && python -m pytest tests/test_pulse_agent.py::test_pipeline_end_to_end -x` | ❌ W0 | ⬜ pending |
| 49-02-02 | 02 | 1 | SC-2 | unit | `cd backend && python -m pytest tests/test_pulse_agent.py::test_pydantic_validation -x` | ❌ W0 | ⬜ pending |
| 49-02-03 | 02 | 1 | SC-3 | unit | `cd backend && python -m pytest tests/test_pulse_agent.py::test_pulse_timeout_config -x` | ❌ W0 | ⬜ pending |
| 49-02-04 | 02 | 1 | SC-4 | unit | `cd backend && python -m pytest tests/test_pulse_service.py::test_active_run_conflict -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_pulse_agent.py` — stubs for SC-1, SC-2, SC-3 (pipeline, Pydantic, config)
- [ ] `backend/tests/test_pulse_service.py` — stubs for PULSE-02, PULSE-03, SC-4 (credit logic, lifecycle, conflict)
- [ ] No new framework install needed (pytest already configured)
- [ ] No new conftest fixtures needed (existing fixtures sufficient)

*Existing infrastructure covers framework requirements.*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
