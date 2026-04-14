# Phase 55: Tier Restructure & Data Foundation - Context

**Gathered:** 2026-03-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Restructure the tier model to support 4 consumer tiers (Free Trial, On Demand, Standard/Basic, Premium) plus Internal. Add dual-balance credit tracking (subscription + purchased), create all billing database tables (Subscription, PaymentHistory, CreditPackage, StripeEvent), add `trial_expires_at` to User model, and update APScheduler to skip subscription-tier users. No Stripe integration, no UI changes, no trial enforcement — those are Phase 56-58.

</domain>

<decisions>
## Implementation Decisions

### Free tier migration
- No `free` tier users exist in production — skip data migration entirely
- Drop the `free` key from `user_classes.yaml`
- Keep `standard` as the DB key (do NOT rename to `basic` in DB) — display name can be "Basic" in UI later if desired
- No Alembic data migration for user rows needed

### On Demand tier design
- Add `on_demand` key to `user_classes.yaml`
- `reset_policy: none` — no auto-reset, APScheduler skips these users
- `credits: 0` — On Demand starts at zero by default
- When a user transitions to On Demand: inherit remaining balance from previous tier if not expired, otherwise 0
- `workspace_access` and `max_active_collections` configurable in YAML like any other tier

### Dual-balance behavior
- `UserCredit` model gets a new `purchased_balance` field alongside existing `balance` (which becomes subscription balance)
- Credit deduction: consume subscription credits first, purchased credits second
- Refunds: reverse deduction order — refund to purchased first, then subscription (last-out-first-in)
- Subscription credit reset: subscription balance resets to tier allocation (leftovers discarded), purchased balance untouched
- Purchased credits persist across billing cycles — never reset, never expire
- Frontend display: single combined number (subscription + purchased), detail view breaks it down — but display is Phase 58 scope

### New user default flow
- Update `get_default_class()` to return `"free_trial"` instead of `"free"`
- Update `User` model default for `user_class` field to `"free_trial"`
- Add `trial_expires_at` field to `User` model (DateTime, nullable) — set during registration to `now + trial_duration_days`
- `trial_duration_days` added as platform setting (default: 7 days)
- Free trial config in YAML: `credits: 100`, `trial_duration_days: 7`
- Trial enforcement (middleware, banners, blocking overlay) deferred to Phase 56

### APScheduler scoping
- `process_credit_resets()` must skip users on subscription tiers (standard/premium) — Stripe handles their resets via `invoice.paid` webhook in Phase 57
- On Demand users (reset_policy: none) already skipped by existing logic
- Free Trial users (reset_policy: none) already skipped by existing logic
- Only `internal` users with reset_policy: unlimited need the existing skip

### Claude's Discretion
- Exact column types and constraints for new billing tables (Subscription, PaymentHistory, CreditPackage, StripeEvent)
- Alembic migration ordering and dependency chain
- Whether to split the `balance` field rename or keep as-is and add `purchased_balance` alongside
- Default values for On Demand workspace_access and max_active_collections in YAML

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Tier & Credit Requirements
- `.planning/REQUIREMENTS.md` — TIER-01 through TIER-08, DATA-01 through DATA-06 (all Phase 55 requirements)

### Existing Code
- `backend/app/config/user_classes.yaml` — Current tier definitions (free_trial, free, standard, premium, internal)
- `backend/app/models/user.py` — User model with `user_class` field (default "free")
- `backend/app/models/user_credit.py` — UserCredit model with single `balance` field
- `backend/app/services/credit.py` — CreditService with single-balance deduction, reset, refund logic
- `backend/app/services/user_class.py` — `get_default_class()` hardcoded to "free", `get_user_classes()` YAML loader
- `backend/app/scheduler.py` — APScheduler credit reset job, processes all users with recurring policies

### Roadmap
- `.planning/ROADMAP.md` — Phase 55 success criteria, dependency chain to Phase 56-59

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `CreditService` (`backend/app/services/credit.py`): Existing deduction, refund, reset, admin_adjust methods — need dual-balance refactor
- `UserCredit` model (`backend/app/models/user_credit.py`): Add `purchased_balance` field alongside existing `balance`
- `get_user_classes()` / `get_class_config()` (`backend/app/services/user_class.py`): YAML-based tier config with 30s cache — reusable as-is
- `CreditTransaction` model (`backend/app/models/credit_transaction.py`): Existing transaction logging — may need a field to track which balance pool was affected

### Established Patterns
- Alembic migrations in `backend/alembic/versions/` — all schema changes via migrations
- SQLAlchemy mapped_column with type hints — consistent model pattern
- `NUMERIC(10, 1)` for balance fields
- `SELECT FOR UPDATE` locking pattern in CreditService for atomic operations
- Platform settings via `backend/app/services/platform_settings.py` for configurable values

### Integration Points
- `backend/app/services/auth.py` — Registration flow sets user_class and creates UserCredit row
- `backend/app/dependencies.py` — May reference user_class for access control
- `backend/app/scheduler.py` — Credit reset job needs subscription-tier skip logic
- `backend/app/routers/admin/` — Admin endpoints for tier/credit management

</code_context>

<specifics>
## Specific Ideas

- Owner confirmed: no free tier users in production, no standard-to-basic DB rename needed
- On Demand balance inheritance: "If user upgrades before free_trial expires, use the last balance. If expired, start from 0. If from subscription, use the last balance. If fresh start, always 0."
- Trial: 100 credits, 7 days (not the 14-day default from requirements — owner chose 7)
- Keep `standard` as DB key — terminology change to "Basic" is UI-only, deferred

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 55-tier-restructure-data-foundation*
*Context gathered: 2026-03-18*
