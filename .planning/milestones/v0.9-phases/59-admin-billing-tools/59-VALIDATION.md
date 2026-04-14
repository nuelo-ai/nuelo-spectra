---
phase: 59
slug: admin-billing-tools
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-24
---

# Phase 59 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (backend), vitest (admin-frontend) |
| **Config file** | `backend/pytest.ini`, `admin-frontend/vitest.config.ts` |
| **Quick run command** | `cd backend && python -m pytest tests/ -x -q --tb=short` |
| **Full suite command** | `cd backend && python -m pytest tests/ -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest tests/ -x -q --tb=short`
- **After every plan wave:** Run `cd backend && python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 59-01-01 | 01 | 1 | ADMIN-01 | unit | `pytest tests/test_admin_billing.py -k billing_detail` | ❌ W0 | ⬜ pending |
| 59-01-02 | 01 | 1 | ADMIN-02 | unit | `pytest tests/test_admin_billing.py -k force_set_tier` | ❌ W0 | ⬜ pending |
| 59-01-03 | 01 | 1 | ADMIN-03 | unit | `pytest tests/test_admin_billing.py -k cancel_subscription` | ❌ W0 | ⬜ pending |
| 59-02-01 | 02 | 1 | ADMIN-04 | unit | `pytest tests/test_admin_billing.py -k refund` | ❌ W0 | ⬜ pending |
| 59-02-02 | 02 | 1 | ADMIN-05 | unit | `pytest tests/test_admin_billing.py -k audit_log` | ❌ W0 | ⬜ pending |
| 59-03-01 | 03 | 2 | ADMIN-06 | unit | `pytest tests/test_admin_billing.py -k billing_settings` | ❌ W0 | ⬜ pending |
| 59-03-02 | 03 | 2 | ADMIN-07 | unit | `pytest tests/test_admin_billing.py -k monetization_switch` | ❌ W0 | ⬜ pending |
| 59-04-01 | 04 | 2 | ADMIN-08 | unit | `pytest tests/test_admin_billing.py -k discount_code` | ❌ W0 | ⬜ pending |
| 59-04-02 | 04 | 2 | ADMIN-09 | unit | `pytest tests/test_admin_billing.py -k coupon_stripe` | ❌ W0 | ⬜ pending |
| 59-04-03 | 04 | 2 | ADMIN-10 | unit | `pytest tests/test_admin_billing.py -k promotion_code` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_admin_billing.py` — stubs for ADMIN-01 through ADMIN-10
- [ ] Test fixtures for mock Stripe client, admin user, test subscription/payment data

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Stripe Dashboard link opens correct customer | ADMIN-01 | External URL | Click "View in Stripe" button, verify correct customer page opens |
| Stripe-hosted Checkout applies promotion code | ADMIN-10 | External Stripe UI | Create discount code in admin, attempt checkout with code in Stripe-hosted page |
| Monetization switch hides billing UI on public frontend | ADMIN-07 | Cross-app visual | Toggle switch OFF, verify public frontend hides plan selection/buy credits |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
