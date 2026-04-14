---
phase: 58
slug: billing-ui-subscription-management
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-22
---

# Phase 58 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (backend) / TypeScript check (frontend) |
| **Config file** | `backend/pyproject.toml` / `frontend/tsconfig.json` |
| **Quick run command** | `cd backend && python -m pytest tests/ -x -q --timeout=30` |
| **Full suite command** | `cd backend && python -m pytest tests/ -q --timeout=60` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest tests/ -x -q --timeout=30`
- **After every plan wave:** Run `cd backend && python -m pytest tests/ -q --timeout=60`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 58-01-00 | 01 | 1 | Wave 0 stubs | unit | `cd backend && pytest tests/test_subscription_change.py tests/test_subscription_cancel.py tests/test_billing_history.py -x -q` | ❌ W0 | ⬜ pending |
| 58-01-01 | 01 | 1 | SUB-02, SUB-03, SUB-04, SUB-05 | unit | `cd backend && pytest tests/test_subscription_change.py tests/test_subscription_cancel.py -x -q` | ❌ W0 | ⬜ pending |
| 58-01-02 | 01 | 1 | TOPUP-01, TOPUP-02, BILL-01, BILL-02, BILL-05 | unit | `cd backend && pytest tests/ -x -q` | ❌ W0 | ⬜ pending |
| 58-02-01 | 02 | 1 | BILL-04, BILL-07, TOPUP-04 | unit | `cd backend && pytest tests/ -x -q` | ✅ | ⬜ pending |
| 58-02-02 | 02 | 1 | TOPUP-05 | unit | `cd backend && pytest tests/ -x -q` | ✅ | ⬜ pending |
| 58-03-01 | 03 | 2 | SUB-01, BILL-06 | typecheck | `cd frontend && npx tsc --noEmit` | ✅ | ⬜ pending |
| 58-03-02 | 03 | 2 | BILL-01, BILL-02, BILL-04, BILL-07 | typecheck | `cd frontend && npx tsc --noEmit` | ✅ | ⬜ pending |
| 58-04-01 | 04 | 2 | BILL-03, SUB-03, SUB-04, SUB-05, TOPUP-01 | typecheck | `cd frontend && npx tsc --noEmit` | ✅ | ⬜ pending |
| 58-04-02 | 04 | 2 | TOPUP-02, TOPUP-03, TOPUP-05, BILL-05 | typecheck | `cd frontend && npx tsc --noEmit` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_subscription_change.py` — stubs for SUB-02, SUB-03, SUB-05
- [ ] `backend/tests/test_subscription_cancel.py` — stubs for SUB-04
- [ ] `backend/tests/test_billing_history.py` — stubs for BILL-01, BILL-05

*Existing pytest infrastructure covers backend. Frontend validated via tsc --noEmit.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Stripe redirect checkout completes | SUB-02 | Requires Stripe test mode | Open /settings/plan, click Subscribe, verify redirect to Stripe Checkout |
| Plan highlight shows current tier | SUB-01 | Visual verification | Log in as Basic user, verify Basic card highlighted |
| Credit balance updates after top-up | TOPUP-05 | End-to-end Stripe flow | Purchase credits via test mode, verify balance increments |
| Billing history shows entries | BILL-05 | Requires Stripe test transactions | Complete a payment, verify entry appears in history table |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
