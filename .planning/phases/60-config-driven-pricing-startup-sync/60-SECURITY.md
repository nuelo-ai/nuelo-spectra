---
phase: 60-config-driven-pricing-startup-sync
auditor: gsd-secure-phase
asvs_level: 1
block_on: high
completed: 2026-04-23
verdict: SECURED
threats_open: 0
threats_total: 8
---

# Phase 60 Security Audit

**Phase:** 60 — config-driven-pricing-startup-sync
**Threats Closed:** 8/8
**ASVS Level:** 1
**Block On:** high severity open threats

## Threat Verification

| Threat ID | Category | Disposition | Status | Evidence |
|-----------|----------|-------------|--------|----------|
| T-60-01 | Tampering | accept | CLOSED | `yaml.safe_load()` confirmed at user_class.py:26. Config file is server-side only with no user upload path. |
| T-60-02 | Information Disclosure | accept | CLOSED | Pricing values (price_cents) are public-facing display data. No credentials or secrets stored in YAML. |
| T-60-03 | Elevation of Privilege | mitigate | CLOSED | `check_stripe_readiness()` called at billing_settings.py:90 before any DB writes. 422 returned with structured `missing` list if Stripe not ready. |
| T-60-04 | Denial of Service | mitigate | CLOSED | Stripe failures wrapped in try/except at pricing_sync.py:312 (`_sync_stripe_prices`) and pricing_sync.py:342 (`_sync_stripe_packages`). App starts without Stripe. Warning logged on failure. |
| T-60-05 | Tampering | accept | CLOSED | All seeding calls use `admin_id=None` (system actor). Seeding is fill-gap-only: `if existing is None:` guards at pricing_sync.py:238 and pricing_sync.py:263. Admin PUT endpoint gated by `CurrentAdmin` dependency at billing_settings.py:64. |
| T-60-06 | Information Disclosure | accept | CLOSED | Stripe key accessed via `get_settings().stripe_secret_key` (env var) at pricing_sync.py:64. Not stored in YAML or DB. |
| T-60-07 | Elevation of Privilege | mitigate | CLOSED | Guard at billing_settings.py:88 uses `is True` (strict check). `check_stripe_readiness(db)` called at billing_settings.py:90. 422 raised with `message` + `missing` fields before any upsert runs. |
| T-60-08 | Denial of Service | accept | CLOSED | DB seeding is fail-fast by design: no try/except wraps `seed_pricing_from_config()` call in main.py:233. If DB is unreachable, app does not start. Stripe failures are graceful (handled inside pricing_sync.py). |

## Mitigation Detail

### T-60-03 / T-60-07 — Elevation of Privilege: monetization_enabled toggle

The guard at `billing_settings.py:88-98` uses `is True` (not truthy) to avoid false positives when the field is absent from the request payload. `check_stripe_readiness()` inspects:
1. `STRIPE_SECRET_KEY` env var presence
2. Non-empty `stripe_price_{tier}_monthly` in platform_settings for every `has_plan: true` tier
3. Non-empty `stripe_price_id` for every active credit package row

The 422 response includes a machine-readable `missing` list for UI consumption. No DB writes occur if the guard fires.

### T-60-04 — Denial of Service: Stripe API on startup

Both `_sync_stripe_prices()` and `_sync_stripe_packages()` wrap each Stripe call in `try/except Exception` with `logger.warning()`. The outer `seed_pricing_from_config()` has no catch block for Stripe — failures propagate only from DB operations (intentional fail-fast). Stripe sync itself is also mode-gated: only runs when `spectra_mode in ("dev", "public")` and `stripe_secret_key` is set (pricing_sync.py:42).

## Accepted Risks Log

| Threat ID | Risk Accepted | Rationale |
|-----------|---------------|-----------|
| T-60-01 | YAML tampering via filesystem | Config deployed with code. No runtime upload path. `yaml.safe_load()` prevents code execution even if file is modified on disk. |
| T-60-02 | Price values visible in config | Pricing is intentionally public (shown on plan selection UI). No secrets co-located in user_classes.yaml. |
| T-60-05 | System-actor DB writes during seeding | `admin_id=None` is the documented pattern for system-initiated upserts. Seeding never overwrites existing admin-set values. |
| T-60-06 | Stripe secret key exposure | Key sourced from env var only. Never written to YAML or DB. Standard 12-factor pattern. |
| T-60-08 | DB unreachability blocks startup | Accepted by design (D-05). Pricing config must seed successfully for the app to be in a valid state. |

## Unregistered Threat Flags

No unregistered threat flags were raised in any SUMMARY.md file across plans 01, 02, or 03. The 60-03-SUMMARY.md explicitly states "No new threat surfaces beyond those documented in the plan's threat model."
