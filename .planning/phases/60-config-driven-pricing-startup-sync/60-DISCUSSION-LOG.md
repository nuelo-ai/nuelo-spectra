# Phase 60: Config-Driven Pricing & Startup Sync - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-23
**Phase:** 60-config-driven-pricing-startup-sync
**Areas discussed:** Config file structure, Startup sync behavior, Stripe auto-provisioning, Reset-to-defaults contract

---

## Config File Structure

| Option | Description | Selected |
|--------|-------------|----------|
| In user_classes.yaml | Add credit_packages: top-level key alongside user_classes:. Single file for all pricing config. | ✓ |
| Separate credit_packages.yaml | New file in backend/app/config/. Cleaner separation but adds another config file. | |
| You decide | Claude picks best approach | |

**User's choice:** In user_classes.yaml
**Notes:** None

| Option | Description | Selected |
|--------|-------------|----------|
| Match existing pattern | has_plan: true and price_cents: 2900 directly in tier block. Maps to existing platform_settings keys. | ✓ |
| Nested pricing block | pricing: sub-block with monthly_price_cents, stripe_product_name. More structured but adds nesting. | |
| You decide | Claude picks field naming | |

**User's choice:** Match existing pattern
**Notes:** None

| Option | Description | Selected |
|--------|-------------|----------|
| Match CreditPackage model | name, price_cents, credit_amount, display_order — 1:1 with DB columns | ✓ |
| Minimal | Only name, price_cents, credit_amount. Derive display_order from list position. | |
| You decide | Claude picks detail level | |

**User's choice:** Match CreditPackage model
**Notes:** None

---

## Startup Sync Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| In lifespan, after LLM validation | Add seeding in lifespan() after LLM/SMTP validation. Idempotent, fills gaps only. | ✓ |
| In docker-entrypoint.sh | Standalone script between alembic and uvicorn. Runs once per container start. | |
| You decide | Claude picks best placement | |

**User's choice:** In lifespan, after LLM validation
**Notes:** User requested detailed explanation of DB empty vs populated behavior. Explanation provided covering first deploy, re-deploy with no edits, and re-deploy with admin edits scenarios.

| Option | Description | Selected |
|--------|-------------|----------|
| Graceful DB + fail-fast Stripe | DB seeding blocks startup on error. Stripe failures log warning and continue. | ✓ |
| Fail-fast everything | Any failure blocks startup. Stripe outages prevent deploys. | |
| Graceful everything | Log warnings, never block. Risk: no pricing data if DB seed fails. | |
| You decide | Claude picks failure strategy | |

**User's choice:** Graceful for DB seed (fail-fast), graceful for Stripe (log warning, continue)
**Notes:** User added requirement: monetization toggle must be gated by Stripe readiness check. If Stripe not configured, monetization can't be enabled. Also: monetization_enabled must default to false on first startup.

---

## Stripe Auto-Provisioning

| Option | Description | Selected |
|--------|-------------|----------|
| One Product per tier/package | "Spectra Standard Plan", "Spectra Starter Pack" — clean Stripe Dashboard organization | ✓ |
| Single Spectra Product | One Product, all Prices attached. Simpler but harder to distinguish. | |
| You decide | Claude picks structure | |

**User's choice:** One Product per tier/package
**Notes:** None

| Option | Description | Selected |
|--------|-------------|----------|
| Only dev and public modes | Stripe API calls only where checkout happens. DB seeding in all modes. | ✓ |
| All modes where key exists | If STRIPE_SECRET_KEY set, run regardless of mode. | |
| You decide | Claude picks scope | |

**User's choice:** Only dev and public modes
**Notes:** User initially didn't understand SPECTRA_MODE scoping. Explanation of 4 modes provided. User then confirmed dev+public only.

**Additional discussion:** User asked about v0.8.x → v0.10 upgrade path. Detailed migration scenario provided covering Alembic migrations, lifespan seeding, monetization_enabled=false safety, and Stripe skip behavior. User confirmed approach.

---

## Reset-to-Defaults Contract

| Option | Description | Selected |
|--------|-------------|----------|
| Overwrite DB with config values | Replace platform_settings values. Archive old Stripe Prices, create new ones. | ✓ |
| Delete DB rows and re-seed | Remove keys, re-run seeding. Same result but brief window with no data. | |
| You decide | Claude picks safest approach | |

**User's choice:** Overwrite DB values with config values
**Notes:** User asked about existing subscribers. Explanation of grandfathered pricing provided — existing subscribers keep their Stripe Price, only new subscribers get reset price. User confirmed.

| Option | Description | Selected |
|--------|-------------|----------|
| Overwrite DB rows with config | Update existing rows. Packages not in config deactivated, not deleted. | ✓ |
| Delete all and re-seed | Truncate and re-insert. Breaks payment_history FK references. | |
| You decide | Claude picks safest approach | |

**User's choice:** Overwrite DB rows with config values
**Notes:** None

## Claude's Discretion

- Stripe Product naming convention details
- Startup sync ordering between subscription pricing and credit packages
- Logging verbosity and format
- Internal idempotent check implementation

## Deferred Ideas

- Retroactive price updates for existing subscribers (separate admin action, not part of reset)
- Per-environment pricing overrides (out of scope per REQUIREMENTS.md)
