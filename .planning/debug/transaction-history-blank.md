---
status: diagnosed
trigger: "P27-T3 + P29-T2 — Transaction history blank despite adjustments"
created: 2026-02-17T00:00:00Z
updated: 2026-02-17T00:00:00Z
---

## Current Focus

hypothesis: Frontend calls wrong URL for credit transaction history — /api/admin/users/{id}/credits/transactions but backend serves this at /api/admin/credits/users/{id}/transactions
test: Trace URL from hook -> backend router registration
expecting: 404 on every fetch, silently returns [] due to error swallowing in hook
next_action: DIAGNOSED — no action needed, research-only mode

## Symptoms

expected: Transaction history table shows credit transactions after admin adjustments
actual: Transaction history section shows "No credit transactions yet" even after adjustments
errors: No visible error — hook swallows non-ok responses and returns empty array
reproduction: Navigate to Users -> any user -> Credits tab; make an adjustment; table stays blank
started: From initial implementation

## Eliminated

- hypothesis: CreditService.admin_adjust does not write CreditTransaction rows
  evidence: CreditService.admin_adjust (credit.py lines 194-201) creates CreditTransaction and flushes it before commit
  timestamp: 2026-02-17

- hypothesis: CreditTransaction model is missing fields
  evidence: Model has all required fields: id, user_id, amount, balance_after, transaction_type, reason, admin_id, created_at
  timestamp: 2026-02-17

- hypothesis: get_transaction_history service method is broken
  evidence: CreditService.get_transaction_history (credit.py lines 284-295) correctly queries and returns transactions
  timestamp: 2026-02-17

- hypothesis: Backend endpoint GET /api/admin/credits/users/{user_id}/transactions is missing
  evidence: Endpoint exists in backend/app/routers/admin/credits.py lines 44-73, registered under /credits router with /credits prefix
  timestamp: 2026-02-17

- hypothesis: Next.js rewrites prevent API calls from reaching backend
  evidence: next.config.ts rewrites /api/:path* to http://localhost:8000/api/:path* — works for all paths
  timestamp: 2026-02-17

## Evidence

- timestamp: 2026-02-17
  checked: backend/app/services/credit.py — admin_adjust method
  found: Creates CreditTransaction row with user_id, amount, balance_after, transaction_type="admin_adjustment", reason, admin_id; calls db.add and db.flush
  implication: Backend writes transactions correctly on every adjustment

- timestamp: 2026-02-17
  checked: backend/app/routers/admin/credits.py
  found: Router has prefix="/credits"; transaction endpoint path is "/users/{user_id}/transactions"; full route is GET /api/admin/credits/users/{user_id}/transactions
  implication: Correct backend URL = /api/admin/credits/users/{user_id}/transactions

- timestamp: 2026-02-17
  checked: backend/app/routers/admin/users.py
  found: Users router has prefix="/users"; there is NO /credits/transactions sub-route on this router; only /credits/adjust (POST) exists at /{user_id}/credits/adjust
  implication: /api/admin/users/{user_id}/credits/transactions does NOT exist on the backend — would return 404

- timestamp: 2026-02-17
  checked: admin-frontend/src/hooks/useUsers.ts — useUserCreditTransactions (lines 72-84)
  found: Calls GET /api/admin/users/${userId}/credits/transactions; on non-ok response returns [] (silently swallows error)
  implication: Every fetch hits a 404, hook returns [] silently, table shows "No credit transactions yet"

- timestamp: 2026-02-17
  checked: admin-frontend/src/hooks/useUsers.ts — useAdjustCredits (lines 135-142)
  found: Calls POST /api/admin/users/${userId}/credits/adjust — this URL DOES exist on the users router (line 470 of users.py)
  implication: Adjustments succeed and transactions ARE written to DB; only the read endpoint URL is wrong

## Resolution

root_cause: useUserCreditTransactions hook calls the wrong URL. It calls /api/admin/users/{userId}/credits/transactions which does not exist on the backend. The actual endpoint is /api/admin/credits/users/{userId}/transactions (mounted under the credits router). The hook silently swallows the 404 and returns an empty array, making the table permanently blank.

fix: NOT APPLIED (research-only mode)

verification: NOT PERFORMED

files_changed: []
