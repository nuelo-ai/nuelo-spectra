---
status: diagnosed
trigger: "P27-T4 — Credit adjustment missing password re-entry and transaction logging"
created: 2026-02-17T00:00:00Z
updated: 2026-02-17T00:00:00Z
symptoms_prefilled: true
goal: find_root_cause_only
---

## Current Focus

hypothesis: The frontend CreditsTab calls a different endpoint (users.py /{user_id}/credits/adjust) that has no password field, instead of the correct endpoint in credits.py (/credits/users/{user_id}/adjust) which requires password re-entry. The CreditAdjustRequest schema in admin_users.py also lacks the password field.
test: Confirmed by reading all four files.
expecting: confirmed
next_action: return diagnosis

## Symptoms

expected: Admin must re-enter password before adjusting credits; each adjustment creates a credit_transactions row with admin_note
actual: No password prompt shown in UI; adjustments still call CreditService.admin_adjust (so transactions ARE created) but no password verification occurs
errors: None visible — silently skips password check
reproduction: Navigate to User detail -> Credits tab -> adjust credits
started: Always (feature was never fully wired end-to-end)

## Eliminated

- hypothesis: CreditService.admin_adjust does not create a transaction record
  evidence: Lines 194-202 of credit.py clearly create a CreditTransaction with transaction_type="admin_adjustment", reason=reason, admin_id=admin_id
  timestamp: 2026-02-17

- hypothesis: The backend credits.py router endpoint is missing
  evidence: credits.py line 76 defines POST /credits/users/{user_id}/adjust with password verification at line 89
  timestamp: 2026-02-17

## Evidence

- timestamp: 2026-02-17
  checked: backend/app/routers/admin/users.py line 470
  found: A SECOND adjust endpoint exists at POST /{user_id}/credits/adjust using CreditAdjustRequest from admin_users.py — which has NO password field
  implication: Frontend hits this endpoint, bypassing the password check

- timestamp: 2026-02-17
  checked: backend/app/schemas/admin_users.py line 89
  found: CreditAdjustRequest has only amount and reason — no password field
  implication: Even if frontend sent a password, this endpoint would ignore it

- timestamp: 2026-02-17
  checked: admin-frontend/src/hooks/useUsers.ts line 136
  found: useAdjustCredits sends to /api/admin/users/{userId}/credits/adjust with only {amount, reason} — no password field
  implication: Frontend never collects or sends a password

- timestamp: 2026-02-17
  checked: admin-frontend/src/types/user.ts line 57
  found: CreditAdjustRequest TypeScript type has only {amount, reason} — password field absent
  implication: The TypeScript contract does not include password

- timestamp: 2026-02-17
  checked: admin-frontend/src/components/users/UserDetailTabs.tsx CreditsTab (lines 285-433)
  found: Form has Amount and Reason inputs only — no password input field whatsoever
  implication: UI never prompts for password

- timestamp: 2026-02-17
  checked: backend/app/routers/admin/credits.py line 76
  found: The CORRECT endpoint (POST /credits/users/{user_id}/adjust) exists, uses CreditAdjustmentRequest (which includes password), calls verify_password, then CreditService.admin_adjust
  implication: The full secure flow already exists but is never called from the frontend

- timestamp: 2026-02-17
  checked: backend/app/schemas/credit.py line 48
  found: CreditAdjustmentRequest has {amount, reason, password} — password: str = Field(min_length=1)
  implication: The correct schema is already complete

## Resolution

root_cause: The admin frontend calls the wrong endpoint. There are two credit adjustment endpoints: (1) the correct, secure one in admin/credits.py (POST /api/admin/credits/users/{user_id}/adjust) that verifies admin password, and (2) a second, insecure endpoint in admin/users.py (POST /api/admin/users/{user_id}/credits/adjust) that has no password field and no password verification. The frontend useAdjustCredits hook calls path #2, bypassing the password gate entirely. The CreditsTab UI also has no password input field.

fix: N/A (diagnose only)
verification: N/A
files_changed: []
