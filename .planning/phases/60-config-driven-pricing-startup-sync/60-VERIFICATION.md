---
phase: 60-config-driven-pricing-startup-sync
verified: 2026-04-23T20:00:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
---

# Phase 60: Config-Driven Pricing & Startup Sync — Verification Report

**Phase Goal:** Subscription pricing and credit packages are fully defined in config files and automatically provisioned in both the database and Stripe on first startup -- zero manual setup required
**Verified:** 2026-04-23T20:00:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | user_classes.yaml includes `has_plan` and `price_cents` fields for subscription tiers, and the backend reads them correctly | VERIFIED | YAML confirmed: `has_plan: true`, `price_cents: 2900` under `standard:`; `has_plan: true`, `price_cents: 7900` under `premium:`; `has_plan: false` on free_trial/on_demand/internal. Loader confirmed: `get_user_classes()` returns correct dicts. Runtime check passed. |
| 2 | A config file defines default credit packages (name, price_cents, credit_amount, display_order) and the backend reads them correctly | VERIFIED | `credit_packages:` top-level key in user_classes.yaml with 3 packages (Starter Pack, Value Pack, Pro Pack). `get_credit_packages()` returns list of 3 dicts. Runtime check passed. |
| 3 | On first startup with an empty database, subscription pricing is seeded to platform_settings and credit packages are seeded to the credit_packages table from config defaults | VERIFIED | `_seed_subscription_pricing()` uses direct DB queries (not cache), inserts missing `price_{tier}_monthly_cents` and `stripe_price_{tier}_monthly` keys. `_seed_credit_packages()` matches by name, inserts missing CreditPackage rows. Tests `test_seed_subscription_pricing` and `test_seed_credit_packages` pass. |
| 4 | On startup, Stripe Products and Prices are auto-created for any subscription tier or credit package that is missing a Stripe Price ID -- no manual Stripe Dashboard configuration required | VERIFIED | `_sync_stripe_prices()` creates Stripe Product + recurring Price for tiers with empty `stripe_price_id`. `_sync_stripe_packages()` creates Stripe Product + one-time Price for packages with `stripe_price_id IS NULL`. Both called from `seed_pricing_from_config()`. Tests `test_stripe_sync_subscription` and `test_stripe_sync_packages` pass. Lifespan in `main.py` calls `seed_pricing_from_config()` on every startup. |
| 5 | Existing admin-customized Stripe Price IDs in the database are never overwritten by the startup sync (fills gaps only) | VERIFIED | `_seed_subscription_pricing()` checks `scalar_one_or_none()` before calling `upsert()` — skips if row exists. `_seed_credit_packages()` matches by name, skips if exists. Tests `test_no_overwrite_existing` and `test_seed_credit_packages_idempotent` pass. |

**Score:** 5/5 truths verified

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/app/config/user_classes.yaml` | Pricing config with has_plan, price_cents, credit_packages | VERIFIED | All 5 tiers have `has_plan`, standard/premium have `price_cents`. 3 credit packages defined. |
| `backend/app/services/user_class.py` | get_credit_packages() + shared _load_yaml() cache | VERIFIED | 68 lines. Contains `_load_yaml()`, `get_credit_packages()`, `get_user_classes()`, `invalidate_cache()`. No `_user_classes_cache` (renamed to `_yaml_cache`). |
| `backend/app/services/pricing_sync.py` | Seeding, Stripe sync, readiness check, reset functions | VERIFIED | 343 lines. All 4 public functions and 4 private helpers present. Direct DB queries used (no `get_all`/`get(db,`). Mode guard present. |
| `backend/app/services/platform_settings.py` | monetization_enabled defaults to False | VERIFIED | Line 36: `"monetization_enabled": json.dumps(False)` |
| `backend/tests/test_pricing_sync.py` | 14+ unit tests covering all requirements | VERIFIED | 427 lines, 14 test functions, all passing in 0.21s. |
| `backend/app/main.py` | Pricing sync call in lifespan() | VERIFIED | Lines 230-235: inline import + `async_session_maker()` session + `seed_pricing_from_config(pricing_db)` + `pricing_db.commit()`. |
| `backend/app/routers/admin/billing_settings.py` | Monetization toggle guard | VERIFIED | Lines 88-99: `updates.get("monetization_enabled") is True` guard calls `check_stripe_readiness(db)`, returns 422 with `missing` list if not ready. |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `user_class.py` | `user_classes.yaml` | `_load_yaml()` reads `data["credit_packages"]` | WIRED | `data.get("credit_packages", [])` present in `get_credit_packages()` |
| `pricing_sync.py` | `user_class.py` | `from app.services.user_class import get_user_classes, get_credit_packages` | WIRED | Line 17 of pricing_sync.py |
| `pricing_sync.py` | `platform_settings.py` | `upsert()` and `invalidate_cache as invalidate_platform_cache` | WIRED | Line 16 of pricing_sync.py; called throughout seeding functions |
| `pricing_sync.py` | `subscription.py` | Lazy import `SubscriptionService._get_stripe_client()` | WIRED | Inline `from app.services.subscription import SubscriptionService` inside Stripe functions |
| `main.py` | `pricing_sync.py` | Inline `from app.services.pricing_sync import seed_pricing_from_config` | WIRED | Line 230 of main.py, called at line 233 |
| `billing_settings.py` | `pricing_sync.py` | Inline `from app.services.pricing_sync import check_stripe_readiness` | WIRED | Line 89 of billing_settings.py, called at line 90 |

---

## Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `pricing_sync.py` `_seed_subscription_pricing` | `existing` (PlatformSetting row) | `select(PlatformSetting).where(...)` direct DB query | Yes — real DB select | FLOWING |
| `pricing_sync.py` `_seed_credit_packages` | `existing` (CreditPackage row) | `select(CreditPackage).where(CreditPackage.name == ...)` | Yes — real DB select by name | FLOWING |
| `pricing_sync.py` `_sync_stripe_prices` | Stripe `price.id` | `SubscriptionService._get_stripe_client().v1.prices.create(...)` | Yes — real Stripe API call | FLOWING |
| `pricing_sync.py` `check_stripe_readiness` | `stripe_id` | `select(PlatformSetting)` + `json.loads(row.value)` | Yes — real DB row read | FLOWING |

---

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| YAML parses correctly with all fields | `python -c "..."` (loader runtime check) | All assertions passed, "Loader OK" printed | PASS |
| pricing_sync module imports without errors | `from app.services.pricing_sync import ...` | "Import OK" printed | PASS |
| 14 unit tests pass | `pytest tests/test_pricing_sync.py -x -v` | 14 passed in 0.21s | PASS |
| Lifespan block ordering correct | `python3 -c "..."` ordering check | SMTP=227, pricing=230, checkpointer=238 — order verified | PASS |
| Billing settings guard ordering correct | `python3 -c "..."` ordering check | validation=83, guard=89, current_settings=101 — order verified | PASS |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| SUB-01 | 60-01 | User classes config includes `has_plan` flag | SATISFIED | `has_plan` field present in all 5 tier blocks in user_classes.yaml; `test_yaml_has_plan` passes |
| SUB-02 | 60-01 | User classes config includes `price_cents` for tiers with `has_plan: true` | SATISFIED | `price_cents: 2900` under `standard:`, `price_cents: 7900` under `premium:`; `test_yaml_price_cents` passes |
| SUB-03 | 60-02, 60-03 | Default subscription pricing seeded to platform_settings on first startup | SATISFIED | `_seed_subscription_pricing()` fills gaps, called from `seed_pricing_from_config()` in lifespan; `test_seed_subscription_pricing` passes |
| SUB-04 | 60-02, 60-03 | Stripe Products/Prices auto-created for subscription tiers missing Stripe Price ID | SATISFIED | `_sync_stripe_prices()` creates Product + recurring Price; guarded by `spectra_mode`; `test_stripe_sync_subscription` passes |
| PKG-01 | 60-01 | Default credit packages defined in config file | SATISFIED | 3 packages in `credit_packages:` section of user_classes.yaml; `test_yaml_credit_packages` passes |
| PKG-02 | 60-02, 60-03 | Credit packages seeded to DB on first startup | SATISFIED | `_seed_credit_packages()` inserts missing packages by name; `test_seed_credit_packages` passes |
| PKG-03 | 60-02, 60-03 | Stripe Products/Prices auto-created for credit packages missing Stripe Price ID | SATISFIED | `_sync_stripe_packages()` queries `stripe_price_id IS NULL`, creates Product + one-time Price; `test_stripe_sync_packages` passes |
| SAFE-01 | 60-02 | Existing admin-customized Stripe Price IDs preserved (fills gaps only) | SATISFIED | Direct DB existence check before every `upsert()`; `test_no_overwrite_existing` and `test_seed_credit_packages_idempotent` pass |
| SAFE-02 | 60-02, 60-03 | No manual Stripe Price ID configuration needed for initial deployment | SATISFIED | Auto-creation in `_sync_stripe_prices()` / `_sync_stripe_packages()` on startup; monetization can only be enabled after Stripe is ready (guard in billing_settings.py) |

**Orphaned requirements check:** SUB-05, SUB-06, SUB-07, PKG-04, PKG-05, PKG-06, UI-01, UI-02 are all mapped to Phase 61 in REQUIREMENTS.md traceability table — none are orphaned for Phase 60.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None found | — | — | — | — |

No TODOs, FIXMEs, placeholder patterns, empty implementations, or hardcoded empty returns found in any of the 5 modified/created files.

---

## Human Verification Required

None. All observable truths are mechanically verifiable and confirmed by code inspection, import checks, and a passing test suite. There are no visual/UI outputs in this phase (backend-only).

---

## Gaps Summary

No gaps. All 5 roadmap success criteria are verified against the actual codebase. All 9 requirement IDs (SUB-01 through SUB-04, PKG-01 through PKG-03, SAFE-01, SAFE-02) are satisfied. All 7 required artifacts exist and are substantive, wired, and data-flowing. All 14 unit tests pass. No anti-patterns detected.

---

_Verified: 2026-04-23T20:00:00Z_
_Verifier: Claude (gsd-verifier)_
