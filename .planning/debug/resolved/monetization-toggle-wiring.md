---
status: awaiting_human_verify
trigger: "Monetization toggle in admin Billing Settings saves to platform_settings DB but public frontend never reads it. Plan/Billing tabs and trial banner always show regardless of toggle state."
created: 2026-03-25T00:00:00Z
updated: 2026-03-25T00:00:00Z
---

## Current Focus

hypothesis: CONFIRMED - monetization_enabled exists only in admin billing_settings endpoint (admin-only), no public endpoint exposes it, frontend has zero references
test: traced full data flow
expecting: n/a - root cause confirmed
next_action: implement minimal fix - add monetization_enabled to CreditBalanceResponse, read it in frontend hook, conditionally filter tabs

## Symptoms

expected: When admin disables monetization_enabled, the public frontend should hide billing UI (Plan tab, Billing tab in settings, trial upgrade CTA). Existing subscribers keep their plan.
actual: Toggle saves correctly to DB but nothing on the public frontend reads monetization_enabled. SettingsNav.tsx always shows Plan/Billing tabs unconditionally.
errors: None — missing feature wiring, not a crash.
reproduction: Admin -> Billing Settings -> toggle monetization off -> save. Public frontend still shows Plan and Billing tabs.
started: Never worked — toggle created in Phase 59 but consumption path was never wired.

## Eliminated

## Evidence

- timestamp: 2026-03-25T00:01:00Z
  checked: backend/app/services/platform_settings.py
  found: monetization_enabled is a valid key with default true, stored as JSON bool in platform_settings table
  implication: backend storage works correctly

- timestamp: 2026-03-25T00:01:00Z
  checked: backend/app/routers/admin/billing_settings.py
  found: admin GET/PUT /billing-settings reads/writes monetization_enabled, requires CurrentAdmin auth
  implication: admin toggle works, but endpoint is admin-only, inaccessible to public frontend

- timestamp: 2026-03-25T00:01:00Z
  checked: backend/app/routers/credits.py GET /credits/balance
  found: returns CreditBalanceResponse which has no monetization_enabled field
  implication: the closest public endpoint that frontend already calls does not carry the flag

- timestamp: 2026-03-25T00:01:00Z
  checked: frontend/src/components/settings/SettingsNav.tsx
  found: TABS array is hardcoded with Plan and Billing, no conditional logic whatsoever
  implication: tabs always render regardless of any flag

- timestamp: 2026-03-25T00:01:00Z
  checked: frontend/src/components/trial/TrialBanner.tsx
  found: "Choose Plan" button always rendered when isTrial && !isExpired, no monetization check
  implication: trial CTA shows unconditionally

- timestamp: 2026-03-25T00:01:00Z
  checked: frontend/src/hooks/useTrialState.ts
  found: hook only checks user.user_class and trial_expires_at, no platform settings awareness
  implication: no existing mechanism to pass platform flags to frontend components

## Resolution

root_cause: monetization_enabled flag is only accessible via admin-only endpoint. No public API endpoint exposes it. Frontend SettingsNav.tsx and TrialBanner.tsx have no conditional logic to check it.
fix: (1) Add monetization_enabled field to CreditBalanceResponse and populate from platform_settings in CreditService.get_balance. (2) Create useMonetization hook reading from /credits/balance response. (3) Filter Plan/Billing tabs in SettingsNav when monetization disabled. (4) Hide TrialBanner CTA when monetization disabled.
verification: Python syntax OK. TypeScript compiles with zero errors. All 8 credit dual-balance tests pass (with patched platform_setting). All 11 trial tests pass.
files_changed:
  - backend/app/schemas/credit.py
  - backend/app/services/credit.py
  - backend/tests/test_credit_dual_balance.py
  - frontend/src/hooks/useCredits.ts
  - frontend/src/components/settings/SettingsNav.tsx
  - frontend/src/components/trial/TrialBanner.tsx
