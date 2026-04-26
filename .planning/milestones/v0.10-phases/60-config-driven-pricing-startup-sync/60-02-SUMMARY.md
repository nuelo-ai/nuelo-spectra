---
phase: 60-config-driven-pricing-startup-sync
plan: 02
subsystem: pricing-sync
tags: [pricing, stripe, seeding, startup, config-driven]
dependency_graph:
  requires: [60-01]
  provides: [pricing_sync_module, monetization_default_false]
  affects: [platform_settings, credit_packages, stripe_integration]
tech_stack:
  added: []
  patterns: [lazy-import-stripe, direct-db-query-during-seeding, idempotent-upsert]
key_files:
  created:
    - backend/app/services/pricing_sync.py
    - backend/tests/test_pricing_sync.py
  modified:
    - backend/app/services/platform_settings.py
decisions:
  - "Lazy import SubscriptionService inside Stripe functions to avoid circular imports"
  - "Direct DB queries (not cached get/get_all) during seeding to avoid stale cache pitfall"
  - "monetization_enabled defaults to False -- admin must explicitly enable after Stripe setup"
metrics:
  duration: 219s
  completed: 2026-04-23T19:09:16Z
  tasks_completed: 2
  tasks_total: 2
  files_created: 2
  files_modified: 1
---

# Phase 60 Plan 02: Pricing Sync Service Summary

**One-liner:** Config-driven pricing sync module with DB seeding, Stripe Product/Price provisioning, readiness checks, and reset-to-defaults -- all idempotent and mode-guarded.

## Completed Tasks

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Create pricing_sync.py with seeding, Stripe sync, readiness check, and reset functions | 4d2b0ff | backend/app/services/pricing_sync.py |
| 2 | Update platform_settings.py DEFAULTS and write unit tests | 6dbc9ea | backend/app/services/platform_settings.py, backend/tests/test_pricing_sync.py |

## Implementation Details

### pricing_sync.py (342 lines)

**Public functions:**
- `seed_pricing_from_config(db)` -- Main entry point for startup. Seeds subscription pricing to platform_settings and credit packages to credit_packages table. Syncs Stripe Products/Prices in dev/public mode only.
- `check_stripe_readiness(db)` -- Validates all Stripe Price IDs are configured for monetization enablement.
- `reset_subscription_pricing(db)` -- Overwrites DB subscription pricing with config defaults, deactivates old Stripe Prices, creates new ones.
- `reset_credit_packages(db)` -- Resets credit packages to match config. Non-config packages deactivated (never deleted).

**Private helpers:**
- `_seed_subscription_pricing(db, tiers)` -- Inserts missing price_cents and stripe_price keys via direct DB queries.
- `_seed_credit_packages(db, packages)` -- Inserts missing credit packages matched by name.
- `_sync_stripe_prices(db, tiers)` -- Creates Stripe Product + recurring Price for tiers missing stripe_price_id.
- `_sync_stripe_packages(db)` -- Creates Stripe Product + one-time Price for packages missing stripe_price_id.

### Key Design Decisions

1. **Direct DB queries during seeding** (not cached `get()`/`get_all()`) to avoid stale cache during startup (Pitfall 1 from RESEARCH.md).
2. **Lazy import** of `SubscriptionService` inside Stripe functions to avoid circular imports (same pattern as billing_settings.py).
3. **Stripe sync guarded by spectra_mode** -- only runs in `dev`/`public` modes per D-09.
4. **DB failures propagate (fail-fast)** while **Stripe failures are caught (graceful)** per D-05.
5. **monetization_enabled** defaults to `False` per D-06 -- admin must enable after Stripe readiness.

### platform_settings.py Change

Single-line change: `monetization_enabled` default from `json.dumps(True)` to `json.dumps(False)`.

## Test Coverage

14 unit tests in `test_pricing_sync.py` covering:

| Test | Requirement | What It Verifies |
|------|-------------|------------------|
| test_yaml_has_plan | SUB-01 | has_plan flag per tier in YAML |
| test_yaml_price_cents | SUB-02 | price_cents values in YAML |
| test_yaml_credit_packages | PKG-01 | credit_packages list in YAML |
| test_seed_subscription_pricing | SUB-03 | Seeds pricing keys on empty DB |
| test_no_overwrite_existing | SAFE-01 | Never overwrites existing DB rows |
| test_seed_credit_packages | PKG-02 | Seeds credit packages on empty DB |
| test_seed_credit_packages_idempotent | SAFE-01 | Idempotent package seeding |
| test_stripe_sync_subscription | SUB-04 | Creates Stripe recurring Prices for tiers |
| test_stripe_sync_packages | PKG-03 | Creates Stripe one-time Prices for packages |
| test_stripe_sync_graceful_failure | D-05 | Stripe errors logged, not raised |
| test_check_stripe_readiness_all_ready | D-07 | Ready=True when all configured |
| test_check_stripe_readiness_missing | D-07 | Ready=False with missing details |
| test_spectra_mode_guard | D-09 | Stripe sync skipped in admin mode |
| test_monetization_default_false | D-06 | monetization_enabled defaults to False |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed mock patch targets for lazy imports**
- **Found during:** Task 2
- **Issue:** Plan specified `@patch("app.services.pricing_sync.SubscriptionService")` but SubscriptionService is lazily imported inside functions, not at module level. The attribute does not exist on the module.
- **Fix:** Changed patch target to `@patch("app.services.subscription.SubscriptionService._get_stripe_client")` which patches the method at its source.
- **Files modified:** backend/tests/test_pricing_sync.py
- **Commit:** 6dbc9ea

## Known Stubs

None -- all functions are fully implemented with real logic.

## Self-Check: PASSED
