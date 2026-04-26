---
phase: 60
slug: config-driven-pricing-startup-sync
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-23
---

# Phase 60 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | backend/pytest.ini or pyproject.toml [tool.pytest] |
| **Quick run command** | `cd backend && python -m pytest tests/ -x -q --timeout=30` |
| **Full suite command** | `cd backend && python -m pytest tests/ -v --timeout=60` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest tests/ -x -q --timeout=30`
- **After every plan wave:** Run `cd backend && python -m pytest tests/ -v --timeout=60`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 60-01-01 | 01 | 1 | SUB-01 | — | N/A | unit | `python -m pytest tests/test_pricing_config.py -k "test_yaml_has_plan_price"` | ❌ W0 | ⬜ pending |
| 60-01-02 | 01 | 1 | PKG-01 | — | N/A | unit | `python -m pytest tests/test_pricing_config.py -k "test_credit_packages_config"` | ❌ W0 | ⬜ pending |
| 60-02-01 | 02 | 1 | SUB-02, SUB-03 | — | N/A | integration | `python -m pytest tests/test_startup_sync.py -k "test_seed_subscription_pricing"` | ❌ W0 | ⬜ pending |
| 60-02-02 | 02 | 1 | PKG-02 | — | N/A | integration | `python -m pytest tests/test_startup_sync.py -k "test_seed_credit_packages"` | ❌ W0 | ⬜ pending |
| 60-02-03 | 02 | 1 | SAFE-01 | — | Idempotent seeding never overwrites existing values | integration | `python -m pytest tests/test_startup_sync.py -k "test_idempotent_no_overwrite"` | ❌ W0 | ⬜ pending |
| 60-03-01 | 03 | 2 | SUB-04, PKG-03 | T-60-01 | Stripe API keys validated before calls | integration | `python -m pytest tests/test_stripe_sync.py -k "test_auto_provision_stripe"` | ❌ W0 | ⬜ pending |
| 60-03-02 | 03 | 2 | SAFE-02 | — | Graceful degradation on Stripe failure | integration | `python -m pytest tests/test_stripe_sync.py -k "test_stripe_failure_graceful"` | ❌ W0 | ⬜ pending |
| 60-04-01 | 04 | 3 | SAFE-01 | T-60-02 | Readiness check blocks monetization without Stripe | unit | `python -m pytest tests/test_stripe_readiness.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_pricing_config.py` — stubs for SUB-01, PKG-01
- [ ] `backend/tests/test_startup_sync.py` — stubs for SUB-02, SUB-03, PKG-02, SAFE-01
- [ ] `backend/tests/test_stripe_sync.py` — stubs for SUB-04, PKG-03, SAFE-02
- [ ] `backend/tests/test_stripe_readiness.py` — stubs for SAFE-01
- [ ] `backend/tests/conftest.py` — shared fixtures (mock Stripe client, test DB session)

*Existing pytest infrastructure covers framework requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Stripe Dashboard shows correct Products/Prices | SUB-04, PKG-03 | Requires live Stripe test account | 1. Set STRIPE_SECRET_KEY to test key 2. Start app 3. Check Stripe Dashboard for created Products |
| v0.8.x → v0.10 upgrade path | SAFE-02 | Requires multi-version database state | 1. Start with v0.8 DB 2. Run v0.10 migrations 3. Verify monetization_enabled=false 4. Verify no Stripe errors without key |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
