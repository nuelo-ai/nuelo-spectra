---
phase: 61-admin-pricing-management-ui
plan: 01
subsystem: backend-admin-api
tags: [admin, billing, credit-packages, api, password-verification]
dependency_graph:
  requires: [pricing_sync.py, user_class.py, platform_settings.py]
  provides: [admin-billing-settings-extended, admin-credit-packages-router]
  affects: [admin-router-init]
tech_stack:
  added: []
  patterns: [password-verification-on-mutations, config-defaults-in-response, stripe-price-recreation]
key_files:
  created:
    - backend/app/routers/admin/credit_packages.py
  modified:
    - backend/app/schemas/admin_billing.py
    - backend/app/routers/admin/billing_settings.py
    - backend/app/routers/admin/__init__.py
decisions:
  - "Password required only for price changes, not monetization toggle (D-09, D-17)"
  - "403 status code for wrong password (not 401) per established codebase pattern"
  - "Config defaults built dynamically from user_classes.yaml tiers with has_plan flag"
metrics:
  duration: 2m
  completed: 2026-04-24T01:18:25Z
  tasks_completed: 3
  tasks_total: 3
  files_created: 1
  files_modified: 3
---

# Phase 61 Plan 01: Admin Pricing API Endpoints Summary

Backend API layer for admin pricing management with password-verified mutations, config defaults in responses, and credit package CRUD.

## What Was Done

### Task 1: Extend Pydantic schemas (af83576)
- Added `config_defaults` and `stripe_readiness` fields to `BillingSettingsResponse`
- Added `password` field to `BillingSettingsUpdateRequest`
- Created `BillingSettingsResetRequest` schema
- Created `AdminCreditPackageConfigDefaults`, `AdminCreditPackageResponse`, `CreditPackageUpdateRequest`, `CreditPackageResetRequest` schemas

### Task 2: Extend billing_settings router (03095fb)
- GET endpoint now returns `config_defaults` (from user_classes.yaml tiers) and `stripe_readiness` (from pricing_sync)
- PUT endpoint requires password for price changes (422 if missing, 403 if wrong)
- Added POST `/reset` endpoint calling `reset_subscription_pricing()` with password verification
- Password excluded from updates dict via `model_dump(exclude={"password"})`

### Task 3: Create credit_packages router (1d8d85e)
- Created `backend/app/routers/admin/credit_packages.py` with 3 endpoints:
  - GET "" -- returns all packages (including inactive) with config defaults from YAML
  - PUT "/{package_id}" -- updates package with password verification and Stripe Price recreation on price change
  - POST "/reset" -- resets all packages to config defaults with password verification
- Registered router in `backend/app/routers/admin/__init__.py`

## Deviations from Plan

None -- plan executed exactly as written.

## Commits

| Task | Commit  | Description                                                  |
|------|---------|--------------------------------------------------------------|
| 1    | af83576 | Extend Pydantic schemas for admin billing and credit packages |
| 2    | 03095fb | Extend billing_settings router with password, defaults, reset |
| 3    | 1d8d85e | Create admin credit_packages router and register it           |

## Self-Check: PASSED
