# Phase 60: Config-Driven Pricing & Startup Sync - Context

**Gathered:** 2026-04-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Subscription pricing and credit packages are fully defined in config files and automatically provisioned in both the database and Stripe on first startup — zero manual setup required. This phase covers config file changes, startup seeding logic, Stripe auto-provisioning, and the reset-to-defaults backend contract. No admin UI changes (that's Phase 61).

</domain>

<decisions>
## Implementation Decisions

### Config File Structure
- **D-01:** Credit packages are defined in `user_classes.yaml` under a new `credit_packages:` top-level key alongside the existing `user_classes:` key — single config file for all pricing
- **D-02:** Tier pricing uses flat fields directly in each tier block: `has_plan: true` and `price_cents: 2900` — matches existing platform_settings key naming pattern
- **D-03:** Credit package entries use fields matching the CreditPackage model: `name`, `price_cents`, `credit_amount`, `display_order` — 1:1 mapping with DB columns. `is_active` defaults to true, `stripe_price_id` is auto-created at runtime

### Startup Sync Behavior
- **D-04:** Config-to-DB seeding runs in the `lifespan()` function in `main.py`, after LLM/SMTP validation but before the scheduler. Uses async DB session already available. Runs on every startup but is idempotent (fills gaps only, never overwrites existing values)
- **D-05:** DB seeding failures are fail-fast (block startup — can't run without pricing config). Stripe API failures are graceful (log warning, continue — app works without Stripe Price IDs, admin can trigger creation later)
- **D-06:** `monetization_enabled` defaults to `false` on first startup (change existing DEFAULTS from `True` to `False`). Admin must explicitly enable after Stripe is configured
- **D-07:** A Stripe readiness check utility function is added in Phase 60. It validates that all subscription tiers with `has_plan: true` have non-empty `stripe_price_id` in platform_settings AND all active credit packages have non-empty `stripe_price_id` in the credit_packages table AND `STRIPE_SECRET_KEY` is configured. This function blocks `monetization_enabled=true` in the billing settings PUT endpoint (returns 422 with specifics on what's missing). Phase 61 wires this into the admin UI

### Stripe Auto-Provisioning
- **D-08:** One Stripe Product per tier/package — e.g., "Spectra Standard Plan", "Spectra Starter Pack". Each Product gets one Price attached. Clean organization in Stripe Dashboard
- **D-09:** Stripe auto-provisioning only runs in `dev` and `public` SPECTRA_MODEs. DB seeding runs in all modes. Admin/API deploys without Stripe keys won't error
- **D-10:** v0.8.x → v0.10 upgrade path: Alembic migrations create v0.9 tables, lifespan seeds pricing defaults from config, `monetization_enabled=false` protects existing users. Stripe sync skipped if no `STRIPE_SECRET_KEY`. Admin enables billing when ready — no disruption to existing users

### Reset-to-Defaults Contract
- **D-11:** Subscription pricing reset: overwrite DB values in platform_settings with config-file values. Old Stripe Price IDs are deactivated in Stripe, new Stripe Prices created for config values. Existing subscribers are grandfathered — they keep their current Stripe Price. Only new subscribers get the reset price
- **D-12:** Credit package reset: overwrite existing DB rows to match config values (name, price, credits, display_order). Archive old Stripe Prices, create new ones. Packages not in config are deactivated (`is_active=false`), never deleted — preserves payment_history foreign key references

### Claude's Discretion
- Stripe Product naming convention details (exact prefix, metadata fields)
- Startup sync ordering between subscription pricing and credit packages
- Logging verbosity and format for sync operations
- Internal implementation of the idempotent "fill gaps" check (e.g., SELECT EXISTS vs COUNT)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Pricing Config
- `backend/app/config/user_classes.yaml` — Current tier definitions, will be extended with `has_plan`, `price_cents`, and `credit_packages:` section

### Billing Infrastructure (v0.9)
- `backend/app/services/platform_settings.py` — DEFAULTS dict, get_all(), upsert() functions. Contains current hardcoded pricing defaults that will be replaced by config-driven values
- `backend/app/services/subscription.py` — SubscriptionService (1,272 lines). Stripe checkout, webhook handling, subscription management. Stripe Product/Price creation patterns exist in billing_settings.py
- `backend/app/models/credit_package.py` — CreditPackage model with stripe_price_id field
- `backend/app/models/platform_setting.py` — PlatformSetting key-value model

### Startup & Deployment
- `backend/app/main.py` — `lifespan()` function where seeding will be added (line 210)
- `backend/docker-entrypoint.sh` — Container startup sequence (migrations → seed → uvicorn)

### Admin Billing
- `backend/app/routers/admin/billing_settings.py` — GET/PUT billing settings. PUT already auto-creates Stripe Prices on price change. Monetization toggle guard (D-07) will be added to PUT validation

### Frontend (read-only context for Phase 60)
- `frontend/src/app/(dashboard)/settings/plan/page.tsx` — Plan Selection page (Phase 61 will make this dynamic)
- `backend/app/routers/credits.py` — Credit packages endpoint serving frontend

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `platform_settings.py` `upsert()` function — already handles insert-or-update for platform_settings keys
- `platform_settings.py` DEFAULTS dict pattern — config-driven defaults merged with DB values via TTL cache
- `billing_settings.py` Stripe Price creation logic — already creates Products/Prices when price changes, can be extracted into a shared utility
- `user_class.py` YAML loading pattern — `get_user_classes()` loads and caches `user_classes.yaml`

### Established Patterns
- TTL cache (30s) for platform_settings — new seeded values are visible within 30 seconds
- JSON-encoded string values in platform_settings table
- Stripe client via `SubscriptionService._get_stripe_client()` — singleton pattern
- Alembic for all DB schema changes

### Integration Points
- `lifespan()` in main.py — new seeding step added here
- `user_classes.yaml` loader in `user_class.py` — needs to parse new `has_plan`, `price_cents`, `credit_packages` fields
- `billing_settings.py` PUT endpoint — monetization toggle guard added here
- DEFAULTS dict in `platform_settings.py` — `monetization_enabled` default changes from `True` to `False`

</code_context>

<specifics>
## Specific Ideas

- The v0.8.x → v0.10 upgrade path must be seamless: monetization off by default, Stripe skipped if no key, admin enables when ready
- Monetization toggle is the safety gate — can't be turned on without all Stripe Price IDs provisioned
- Reset-to-defaults follows "grandfathered pricing" pattern for existing subscribers — only new subscribers get the reset price

</specifics>

<deferred>
## Deferred Ideas

- **Retroactive price updates for existing subscribers** — Apply new pricing to all active subscriptions. Needs proration handling and subscriber notification. Separate admin action, not part of reset.
- **Per-environment pricing overrides** — Single config per deploy; admin UI handles customization (out of scope per REQUIREMENTS.md)

None — discussion stayed within phase scope

</deferred>

---

*Phase: 60-config-driven-pricing-startup-sync*
*Context gathered: 2026-04-23*
