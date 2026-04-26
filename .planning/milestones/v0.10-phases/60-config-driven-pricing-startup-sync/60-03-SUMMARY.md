---
phase: 60-config-driven-pricing-startup-sync
plan: 03
subsystem: backend
tags: [pricing, lifespan, monetization-guard, startup-sync]
dependency_graph:
  requires: [60-02]
  provides: [startup-pricing-sync, monetization-toggle-guard]
  affects: [main.py, billing_settings.py]
tech_stack:
  added: []
  patterns: [inline-import, fail-fast-startup, async-session-scoping]
key_files:
  created: []
  modified:
    - backend/app/main.py
    - backend/app/routers/admin/billing_settings.py
decisions:
  - "Pricing sync uses dedicated async_session_maker session (pricing_db) to avoid scope conflicts"
  - "Monetization guard uses 'is True' check to avoid false positives from None values"
  - "DB seeding is fail-fast (no try/except) per D-05 -- app should not start if pricing config cannot seed"
metrics:
  duration_seconds: 136
  completed: "2026-04-23T19:14:50Z"
  tasks_completed: 2
  tasks_total: 2
---

# Phase 60 Plan 03: Lifespan Wiring and Monetization Guard Summary

Wired pricing_sync engine into app entry points: startup seeding in lifespan() and monetization toggle guard in billing_settings PUT endpoint.

## Tasks Completed

| Task | Name | Commit | Files Modified |
|------|------|--------|----------------|
| 1 | Add pricing sync call to lifespan() | 24c70b0 | backend/app/main.py |
| 2 | Add monetization toggle guard to billing_settings PUT | a6957fd | backend/app/routers/admin/billing_settings.py |

## What Was Done

### Task 1: Lifespan Pricing Sync
- Inserted pricing sync block in `lifespan()` after SMTP validation and before PostgreSQL checkpointer initialization
- Uses `async_session_maker()` to create a dedicated `pricing_db` session
- Calls `seed_pricing_from_config(pricing_db)` then commits
- DB errors propagate (fail-fast per D-05) -- Stripe failures handled internally by pricing_sync
- Emits log message via `spectra.pricing` logger on success

### Task 2: Monetization Toggle Guard
- Added guard in `update_billing_settings()` PUT handler after field validation, before any DB writes
- When `monetization_enabled` is set to `True`, calls `check_stripe_readiness(db)`
- Returns 422 with structured detail including human-readable message and `missing` items list
- Uses `is True` (not truthy) to avoid false positives when field is not in update payload

## Deviations from Plan

None -- plan executed exactly as written.

## Verification Results

- Lifespan order verified: SMTP line < pricing line < checkpointer line
- `pricing_db.commit()` present in main.py
- Monetization guard order verified: validation line < guard line < current_settings line
- `check_stripe_readiness` and `Cannot enable monetization` present in billing_settings.py

## Known Stubs

None -- all code is fully wired to existing pricing_sync service functions.

## Threat Surface

No new threat surfaces beyond those documented in the plan's threat model (T-60-07 mitigated by guard, T-60-08 accepted by design).
