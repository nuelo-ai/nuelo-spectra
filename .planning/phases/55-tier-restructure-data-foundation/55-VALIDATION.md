---
phase: 55
slug: tier-restructure-data-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-18
---

# Phase 55 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.0+ / pytest-asyncio 0.23+ |
| **Config file** | `backend/pyproject.toml` (dev dependency) |
| **Quick run command** | `cd backend && python -m pytest tests/ -x -q` |
| **Full suite command** | `cd backend && python -m pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest tests/ -x -q`
- **After every plan wave:** Run `cd backend && python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 55-01-01 | 01 | 1 | TIER-01 | unit | `pytest tests/test_tier_config.py::test_four_consumer_tiers -x` | ❌ W0 | ⬜ pending |
| 55-01-02 | 01 | 1 | TIER-02 | unit | `pytest tests/test_tier_config.py::test_tier_keys -x` | ❌ W0 | ⬜ pending |
| 55-01-03 | 01 | 1 | TIER-03 | manual-only | N/A — owner confirmed no prod users | N/A | ⬜ pending |
| 55-02-01 | 02 | 1 | TIER-04 | unit | `pytest tests/test_dual_balance.py::test_balance_split -x` | ❌ W0 | ⬜ pending |
| 55-02-02 | 02 | 1 | TIER-05 | unit | `pytest tests/test_dual_balance.py::test_deduction_order -x` | ❌ W0 | ⬜ pending |
| 55-02-03 | 02 | 1 | TIER-06 | unit | `pytest tests/test_dual_balance.py::test_purchased_persists_on_reset -x` | ❌ W0 | ⬜ pending |
| 55-02-04 | 02 | 1 | TIER-07 | unit | `pytest tests/test_dual_balance.py::test_subscription_reset -x` | ❌ W0 | ⬜ pending |
| 55-02-05 | 02 | 1 | TIER-08 | unit | `pytest tests/test_scheduler_skip.py::test_skip_subscription_tiers -x` | ❌ W0 | ⬜ pending |
| 55-03-01 | 03 | 1 | DATA-01 | unit | `pytest tests/test_billing_models.py::test_subscription_model -x` | ❌ W0 | ⬜ pending |
| 55-03-02 | 03 | 1 | DATA-02 | unit | `pytest tests/test_billing_models.py::test_payment_history_model -x` | ❌ W0 | ⬜ pending |
| 55-03-03 | 03 | 1 | DATA-03 | unit | `pytest tests/test_billing_models.py::test_credit_package_model -x` | ❌ W0 | ⬜ pending |
| 55-03-04 | 03 | 1 | DATA-04 | unit | `pytest tests/test_billing_models.py::test_stripe_event_model -x` | ❌ W0 | ⬜ pending |
| 55-03-05 | 03 | 1 | DATA-05 | unit | `pytest tests/test_billing_models.py::test_user_trial_field -x` | ❌ W0 | ⬜ pending |
| 55-03-06 | 03 | 1 | DATA-06 | unit | `pytest tests/test_billing_models.py::test_user_credit_purchased_balance -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_tier_config.py` — stubs for TIER-01, TIER-02 (YAML config validation)
- [ ] `tests/test_dual_balance.py` — stubs for TIER-04, TIER-05, TIER-06, TIER-07 (dual-balance CreditService logic)
- [ ] `tests/test_scheduler_skip.py` — stubs for TIER-08 (APScheduler subscription skip)
- [ ] `tests/test_billing_models.py` — stubs for DATA-01 through DATA-06 (model importability, field existence)
- [ ] Update `tests/test_tier_gating.py` — fix references to dropped `free` tier

*Existing infrastructure covers framework needs — only test files are missing.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| No free tier users exist in production | TIER-03 | Owner confirmed no prod users — no migration needed | Verify by querying `SELECT count(*) FROM users WHERE user_class = 'free'` returns 0 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
