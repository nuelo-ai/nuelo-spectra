---
phase: 57
slug: stripe-backend-webhook-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-20
---

# Phase 57 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + pytest-asyncio 0.23.x |
| **Config file** | backend/pyproject.toml (dev dependencies) |
| **Quick run command** | `cd backend && python -m pytest tests/test_webhook.py tests/test_subscription_service.py -x` |
| **Full suite command** | `cd backend && python -m pytest tests/ -x` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest tests/test_webhook.py tests/test_subscription_service.py -x`
- **After every plan wave:** Run `cd backend && python -m pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 57-01-01 | 01 | 1 | STRIPE-01 | unit | `pytest tests/test_stripe_config.py -x` | ❌ W0 | ⬜ pending |
| 57-01-02 | 01 | 1 | STRIPE-04 | unit | `pytest tests/test_webhook.py::test_signature_verification -x` | ❌ W0 | ⬜ pending |
| 57-01-03 | 01 | 1 | STRIPE-05 | unit | `pytest tests/test_webhook.py::test_deduplication -x` | ❌ W0 | ⬜ pending |
| 57-02-01 | 02 | 1 | STRIPE-06 | unit | `pytest tests/test_webhook.py::test_checkout_completed -x` | ❌ W0 | ⬜ pending |
| 57-02-02 | 02 | 1 | STRIPE-07 | unit | `pytest tests/test_webhook.py::test_invoice_paid -x` | ❌ W0 | ⬜ pending |
| 57-02-03 | 02 | 1 | STRIPE-08 | unit | `pytest tests/test_webhook.py::test_invoice_payment_failed -x` | ❌ W0 | ⬜ pending |
| 57-02-04 | 02 | 1 | STRIPE-09 | unit | `pytest tests/test_webhook.py::test_subscription_updated -x` | ❌ W0 | ⬜ pending |
| 57-02-05 | 02 | 1 | STRIPE-10 | unit | `pytest tests/test_webhook.py::test_subscription_deleted -x` | ❌ W0 | ⬜ pending |
| 57-03-01 | 03 | 2 | STRIPE-02 | unit | `pytest tests/test_subscription_service.py::test_create_subscription_checkout -x` | ❌ W0 | ⬜ pending |
| 57-03-02 | 03 | 2 | STRIPE-03 | unit | `pytest tests/test_subscription_service.py::test_create_topup_checkout -x` | ❌ W0 | ⬜ pending |
| 57-03-03 | 03 | 2 | SUB-06 | unit | `pytest tests/test_billing_models.py -x` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_webhook.py` — stubs for STRIPE-04 through STRIPE-10 (webhook signature, dedup, all handlers)
- [ ] `tests/test_subscription_service.py` — stubs for STRIPE-01, STRIPE-02, STRIPE-03 (SDK config, checkout creation)
- [ ] Mock fixtures for Stripe API responses (stripe Event objects, Session objects, Customer objects)
- [ ] stripe package install: add `"stripe>=14.0.0,<15.0"` to pyproject.toml dependencies

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Stripe Dashboard price configuration | STRIPE-02, STRIPE-03 | Requires Stripe Dashboard access | Create test prices in Stripe, add Price IDs to platform_settings |
| End-to-end webhook delivery | STRIPE-04 | Requires Stripe CLI or live webhook | `stripe listen --forward-to localhost:8000/webhooks/stripe` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
