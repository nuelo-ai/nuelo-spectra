---
phase: 60-config-driven-pricing-startup-sync
plan: 01
subsystem: backend/config
tags: [config, pricing, yaml, loader]
dependency_graph:
  requires: []
  provides:
    - "user_classes.yaml with has_plan, price_cents, credit_packages"
    - "get_credit_packages() loader function"
  affects:
    - "backend/app/services/user_class.py"
    - "backend/app/config/user_classes.yaml"
tech_stack:
  added: []
  patterns:
    - "Shared YAML cache via _load_yaml() private function"
key_files:
  created: []
  modified:
    - "backend/app/config/user_classes.yaml"
    - "backend/app/services/user_class.py"
decisions:
  - "Refactored cache to store full YAML dict instead of just user_classes key"
metrics:
  duration: "108s"
  completed: "2026-04-23T19:02:51Z"
  tasks: 2
  files_modified: 2
---

# Phase 60 Plan 01: Extend YAML Config with Pricing Fields Summary

Config-driven pricing source of truth: added has_plan/price_cents to all 5 tiers and credit_packages with 3 default packages, plus get_credit_packages() loader sharing the same 30s TTL cache.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Extend user_classes.yaml with pricing fields and credit packages | 1fe943e | backend/app/config/user_classes.yaml |
| 2 | Add get_credit_packages() loader and update cache | 6e3b2f2 | backend/app/services/user_class.py |

## Changes Made

### Task 1: YAML Config Extension
- Added `has_plan: false` to free_trial, on_demand, internal tiers
- Added `has_plan: true` and `price_cents: 2900` to standard tier
- Added `has_plan: true` and `price_cents: 7900` to premium tier
- Added `credit_packages` top-level key with 3 packages:
  - Starter Pack: 50 credits / $5.00
  - Value Pack: 200 credits / $15.00
  - Pro Pack: 500 credits / $35.00

### Task 2: Loader Refactor
- Renamed `_user_classes_cache` to `_yaml_cache` to store full parsed YAML
- Extracted `_load_yaml()` private function with shared 30s TTL cache logic
- Added `get_credit_packages() -> list[dict]` function
- Updated `invalidate_cache()` to clear unified cache
- `get_user_classes()` and `get_class_config()` unchanged in behavior

## Deviations from Plan

None - plan executed exactly as written.

## Decisions Made

1. **Shared cache stores full YAML dict** - Both `get_user_classes()` and `get_credit_packages()` index into the same cached dict, avoiding double file reads.

## Self-Check: PASSED
