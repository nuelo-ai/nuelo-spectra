---
phase: 61-admin-pricing-management-ui
plan: 02
subsystem: backend-pricing-config
tags: [config-driven, pricing, subscriptions, refactor]
dependency_graph:
  requires: []
  provides: [config-driven-features, dynamic-plan-building]
  affects: [frontend-plan-selection]
tech_stack:
  added: []
  patterns: [config-driven-features, dynamic-tier-iteration]
key_files:
  created: []
  modified:
    - backend/app/config/user_classes.yaml
    - backend/app/routers/subscriptions.py
decisions:
  - "Features lists added only to plan-displayed tiers (on_demand, standard, premium)"
  - "Credits/month and max_active_collections bullets generated dynamically from config values, not stored in features list"
  - "on_demand handled as special case before dynamic tier loop to maintain first position"
  - "get_class_config import retained since it is used in preview_plan_change endpoint"
metrics:
  duration_seconds: 112
  completed: "2026-04-24T01:17:22Z"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 2
---

# Phase 61 Plan 02: Config-Driven Plan Features and Dynamic Plan Building Summary

Config-driven feature bullets added to user_classes.yaml for 3 tiers; /subscriptions/plans endpoint refactored to dynamically iterate config tiers instead of hardcoding 3 PlanInfo objects.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add features lists to user_classes.yaml | c8fc4c8 | backend/app/config/user_classes.yaml |
| 2 | Refactor /subscriptions/plans to build dynamically | 414b8ec | backend/app/routers/subscriptions.py |

## Key Changes

### Task 1: Config-driven feature lists
- Added `features:` list to `on_demand` tier: "No monthly commitment", "Purchase credits as needed", "Full feature access"
- Added `features:` list to `standard` tier: "Priority support", "Full feature access"
- Added `features:` list to `premium` tier: "Priority support", "Full feature access", "Unlimited active collections", "Advanced analytics"
- `free_trial` and `internal` tiers intentionally excluded (not shown in plan selection)

### Task 2: Dynamic plan building
- Replaced hardcoded 3-plan PlanInfo list with dynamic iteration over config tiers
- `on_demand` tier handled as special case (has_plan: false but displayed first)
- Tiers with `has_plan: true` dynamically discovered and appended
- Features read from config YAML `features:` list instead of hardcoded strings
- Credits/month and max_active_collections bullets generated dynamically from config values
- Price reads from platform_settings with fallback to config `price_cents`
- No hardcoded feature strings remain in Python code

## Verification Results

- 3 tiers have `features:` lists in YAML (on_demand, standard, premium)
- `free_trial` and `internal` do not have `features:` key
- `get_user_classes()` call present in refactored endpoint
- `has_plan` filter present in dynamic tier loop
- `tier_config.get("features", [])` reads features from config
- Zero hardcoded feature strings remain in subscriptions.py
- UI-02: Billing page has no hardcoded credit package data (grep check passed)

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None identified.

## Self-Check: PASSED
