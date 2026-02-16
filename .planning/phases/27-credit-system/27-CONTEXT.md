# Phase 27: Credit System - Context

**Gathered:** 2026-02-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Atomic credit deduction per message, balance tracking, transaction history, admin controls for individual user adjustments, and scheduled auto-resets. Backend API only -- no frontend UI in this phase (frontend is Phase 31). Bulk credit operations are deferred.

</domain>

<decisions>
## Implementation Decisions

### Out-of-credits experience
- User can type but hitting send is blocked with an error message
- Error message: "You're out of credits. Credits reset on [date]." (simple + reset date, no upsell for now; will add upgrade option when paid tiers are available)
- User retains full read access to existing chat history, results, and files when out of credits -- only sending new messages is blocked
- Credit balance always visible in the sidebar/nav area of the public app
- Low-credit warning shown when credits drop below a threshold (e.g., <20% or <3 credits remaining)
- Silent deduction per message -- balance updates without showing per-message cost

### Reset scheduling
- Reset cadence is per-class, defined by `reset_policy` in user_classes.yaml (weekly, monthly, none, unlimited) -- not a global default
- Rolling reset relative to each user's signup date (not a global fixed day). If a user signed up on Wednesday, credits reset every Wednesday
- No carry-over: balance resets to tier allocation regardless of remaining credits
- Admin manual reset restarts the user's credit cycle from today (next auto-reset is 1 week/month from the manual reset date)
- In-app notice when credits refresh: brief toast/banner "Your credits have been refreshed!" shown when user opens the app after a reset

### Admin credit operations
- Individual user adjustments only (bulk operations deferred)
- Admin must re-enter their password to confirm any manual credit adjustment (accountability measure)
- Admin must provide a reason/note for every credit adjustment -- shown in transaction history and audit log
- Auto-reset always sets balance to tier allocation, regardless of admin-granted bonuses. Admin bonuses are one-time grants consumed during the current period
- Transaction types are explicitly typed: 'usage' (message sent), 'admin_adjustment', 'auto_reset', 'manual_reset'

### Credit models (user_classes.yaml)
- Three credit models supported via `reset_policy` field:
  - `weekly` / `monthly` -- recurring reset, credits refresh to tier allocation on user's cycle date
  - `none` -- one-time grant (e.g., free trial). Credits given once at assignment, no resets. User blocked permanently when depleted until admin intervenes
  - `unlimited` -- no credit limit. Transactions logged for analytics but balance never decreases
- For one-time grant classes: credits never expire, user blocked when depleted
- For unlimited classes: still create transaction records (log but don't deduct) for audit/analytics
- YAML config structure:
  ```yaml
  user_classes:
    free_trial:
      display_name: "Free Trial"
      credits: 20
      reset_policy: none
    free:
      display_name: "Free"
      credits: 10
      reset_policy: weekly
    standard:
      display_name: "Standard"
      credits: 100
      reset_policy: weekly
    premium:
      display_name: "Premium"
      credits: 500
      reset_policy: monthly
    internal:
      display_name: "Internal"
      credits: 0
      reset_policy: unlimited
  ```

### Tier assignment on registration
- Self-registered users → assigned the default class configured in platform_settings (admin-configurable, e.g., "free" or "free_trial")
- Invite-based users → admin selects the class at invite creation time (required field)

### Claude's Discretion
- Low-credit threshold exact value (percentage or absolute)
- Toast/banner implementation for credit refresh notification
- Scheduler implementation details (APScheduler configuration)
- How to represent "unlimited" balance in the database (sentinel value vs null)
- Credit balance API endpoint design

</decisions>

<specifics>
## Specific Ideas

- Credits reset on a rolling basis per user (signup-date anchored), not a global reset day
- The `reset_policy` field in user_classes.yaml is the key differentiator between recurring, one-time, and unlimited credit models
- Out-of-credits message will evolve: currently shows reset date only, will add "Upgrade" CTA when paid tiers are available
- `stripe_price_id` field in YAML config is forward-compatible hook for future self-service tier upgrades

</specifics>

<deferred>
## Deferred Ideas

- Bulk credit adjustments (grant X credits to all users in a tier) -- removed from v0.5 scope, revisit in future milestone
- Self-service tier upgrade/downgrade (user-initiated) -- future monetization milestone with Stripe integration
- Per-model credit costs (different cost for Opus vs Sonnet vs Haiku) -- deferred until multi-model selection is available to users
- User-facing transaction history endpoint -- Phase 27 exposes balance + next reset only; full history viewing is a future enhancement

</deferred>

---

*Phase: 27-credit-system*
*Context gathered: 2026-02-16*
