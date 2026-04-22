---
gsd_state_version: 1.0
milestone: v0.10
milestone_name: Streamline Pricing Configuration
status: Defining requirements
stopped_at: Milestone started
last_updated: "2026-04-22"
progress:
  total_phases: 0
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-22)

**Core value:** Accurate data analysis through correct, safe Python code generation
**Current focus:** v0.10 Streamline Pricing Configuration

## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: 2026-04-22 — Milestone v0.10 started

## Performance Metrics

**Velocity (v0.8):**

- Total plans completed: 20 (Phases 47-52.1, 8 phases)
- Timeline: 4 days (2026-03-06 → 2026-03-09)
- 144 commits, 168 files changed (+23,418 / -345 lines)

## Accumulated Context

### Decisions

See PROJECT.md Key Decisions table for full decision log.

- [Pre-Phase 55]: Tier restructure + dual-balance credit model must precede all Stripe code
- [Pre-Phase 55]: Existing `free` tier user migration path needs owner decision (grace period vs. immediate On Demand)
- [Phase 55-01]: TIER-03 no data migration needed -- owner confirmed no free-tier users in production
- [Phase 55-01]: TIER-08 scheduler skip via reset_policy=none config change (no code changes)
- [Phase 55-01]: Alembic migration down_revision corrected to 357a798917d0 (actual head)
- [Pre-Phase 57]: Webhook URL routing (direct to FastAPI vs. Next.js proxy) — verify against Dokploy config
- [Phase 55-02]: Refund LIFO: all refunds go to purchased_balance
- [Phase 55-02]: Admin adjust targets subscription pool only (balance_pool=subscription)
- [Phase 55-02]: is_low calculation uses total (subscription + purchased) for accuracy
- [Phase 56-01]: Trial check extracted to _check_trial_expiration helper shared by get_current_user and get_authenticated_user
- [Phase 56-01]: 402 interception placed before 401 handler to prevent token refresh loops on expired trials
- [Phase 56-02]: TrialExpiredOverlay uses usePathname to self-hide on /settings/* paths
- [Phase 56-02]: Banner shows immediately without waiting for credit balance (null-safe rendering)
- [Phase 56-02]: Credits router prefix corrected from /api/credits to /credits (proxy strips /api)
- [Phase 57-01]: Stripe SDK pinned to v14.x (>=14.0.0,<15.0) for API stability
- [Phase 57-02]: SubscriptionService uses private helpers for checkout dispatch clarity
- [Phase 57-02]: Webhook router uses async for db in get_db() for session lifecycle
- [Phase 57]: Webhook router registered globally (all modes) since Stripe calls directly
- [Phase 58]: Upgrade uses proration_behavior=always_invoice (immediate charge), downgrade uses none (Stripe best practice)
- [Phase 58]: Cancel uses subscriptions.update(cancel_at_period_end=True), not subscriptions.cancel()
- [Phase 58]: Stripe SDK v14 requires client.v1 namespace; period dates on items.data[0], not subscription top-level
- [Phase 58]: Preview proration via client.v1.invoices.create_preview (not deprecated upcoming)
- [Phase 58]: Router endpoints must explicitly db.commit() — get_db() only closes session, does not auto-commit
- [Phase 58]: Hosted Stripe Checkout redirect (not embedded) — owner decision, no @stripe/stripe-js needed
- [Phase 59]: Force-set-tier uses immediate Stripe subscription cancel for admin overrides
- [Phase 59]: Refund credit deduction is proportional using Decimal arithmetic
- [Phase 59]: Billing settings PUT auto-creates Stripe Price objects when price changes
- [Phase 59]: Stripe Coupon duration: forever for percent_off, once for amount_off
- [Phase 59]: allow_promotion_codes: True in both subscription and top-up checkout sessions
- [Phase 59]: Billing tab placed as 6th tab in UserDetailTabs; refund button only for succeeded payments with Stripe ID

### Pending Todos

- [ ] Create Dokploy Docker deployment package for spectra-api service (deployment)
- [ ] Query safety filter in Manager Agent (security)
- [ ] Show suggestions in Data Summary sidebar panel (ui)
- [ ] Use Pydantic structured output for agent JSON responses (consistency)
- [ ] Plan production environment variable cleanup and validation (deployment)

### Blockers/Concerns

- ~~**Migration decision needed (Phase 55):** Resolved -- owner confirmed no free-tier users in production, no migration needed (TIER-03).~~
- **Stripe Dashboard setup (Phase 57):** Products, Prices, and webhook endpoint must be manually configured in Stripe Dashboard before Phase 57 can be tested.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 5 | update the query suggestion on the chat dashboard design and style to make it beautiful. use a nice card (Similar to Signal card item on the Signal view). Sort it as multiple columns grouped by the Category. | 2026-03-10 | 43343e9 | [5-update-the-query-suggestion-on-the-chat-](./quick/5-update-the-query-suggestion-on-the-chat-/) |
| 6 | Fix bug on the signal list panel where the spacing between signal cards is too wide on Safari (h-screen -> h-full, space-y -> flex gap) | 2026-03-14 | 492c7b8 | [6-fix-bug-on-the-signal-list-panel-where-t](./quick/6-fix-bug-on-the-signal-list-panel-where-t/) |
| 7 | update requirements docs: move Reporting to v0.8, drop Guided Investigation, keep What-If, create v2 of Spectra-Pulse-Requirement.md | 2026-03-14 | 2eaa15d | [7-update-requirements-docs-move-reporting-](./quick/7-update-requirements-docs-move-reporting-/) |
| h7i | Add hero screenshot to README.md — insert spectra-screenshot.png between What is Spectra? and ## Features | 2026-03-16 | c854db5 | [260316-h7i-add-hero-screenshot-to-readme-md](./quick/260316-h7i-add-hero-screenshot-to-readme-md/) |
| Phase 55 P02 | 6min | 2 tasks | 6 files |
| Phase 57-01 P01 | 3min | 2 tasks | 12 files |
| Phase 57 P03 | 3min | 2 tasks | 6 files |
| Phase 58-01 | 4min | 3 tasks | 8 files |
| Phase 59 P01 | 4min | 2 tasks | 11 files |
| Phase 59 P02 | 4min | 2 tasks | 5 files |
| Phase 59 P03 | 4min | 2 tasks | 7 files |

## Session Continuity

Last session: 2026-03-24T19:18:17.587Z
Stopped at: Completed 59-03-PLAN.md
Resume with: /gsd:plan-phase 59 (Admin Billing Tools)
