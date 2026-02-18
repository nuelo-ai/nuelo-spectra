---
status: diagnosed
trigger: "P29-T7 — User delete doesn't execute after challenge code confirmation (BLOCKER)"
created: 2026-02-17T00:00:00Z
updated: 2026-02-17T00:00:00Z
symptoms_prefilled: true
goal: find_root_cause_only
---

## Current Focus

hypothesis: CONFIRMED - Three compounding bugs prevent delete from ever working
test: Complete trace of frontend -> backend delete flow
expecting: N/A - diagnosis complete
next_action: Return diagnosis to caller

## Symptoms

expected: After confirming challenge code, user is hard-deleted with cascade
actual: Operation silently fails — user is NOT deleted
errors: No visible error shown to user (silent failure)
reproduction: Admin clicks delete on user -> challenge dialog appears -> enter code -> confirm -> nothing happens
started: Unknown

## Eliminated

## Evidence

- timestamp: 2026-02-17T00:00:00Z
  checked: ChallengeCodeDialog.tsx
  found: Challenge code is generated CLIENT-SIDE only (generateCode function, line 26). The component never calls the backend POST /{user_id}/delete-challenge endpoint. The code exists purely in React state (useMemo). The backend has no knowledge of what code was shown.
  implication: The challenge code the user types can never match what the backend expects, because the backend was never asked to generate one.

- timestamp: 2026-02-17T00:00:00Z
  checked: UserTable.tsx lines 114-120 and ChallengeCodeDialog.tsx onConfirm signature
  found: ChallengeCodeDialog.onConfirm is typed as () => void (no arguments). executeAction() calls deleteUser.mutateAsync with hardcoded challenge_code: "CLIENT". The verified client-side code is NEVER passed to the mutation — it is discarded.
  implication: Even if backend challenge generation were wired up, the real verified code would never reach the API call.

- timestamp: 2026-02-17T00:00:00Z
  checked: useUsers.ts useDeleteUser() lines 144-150
  found: useDeleteUser sends DELETE /api/admin/users/${userId}?challenge_code=${challenge_code} — passing the code as a QUERY PARAMETER.
  implication: The backend delete endpoint (admin/users.py line 436) reads challenge_code from body: DeleteConfirmRequest, not from query params. The backend never sees the query param code. FastAPI will return 422 Unprocessable Entity because the required body field is missing.

- timestamp: 2026-02-17T00:00:00Z
  checked: adminApiClient.delete() in admin-api-client.ts line 109-113
  found: The delete() method accepts NO body parameter — it only takes a path string and sends DELETE with no body.
  implication: Even if useDeleteUser were corrected to send a body, the current client has no mechanism to send a JSON body on DELETE requests.

- timestamp: 2026-02-17T00:00:00Z
  checked: backend/app/routers/admin/users.py line 436-455 and schemas/admin_users.py DeleteConfirmRequest
  found: Backend DELETE /{user_id} expects challenge_code in a JSON body (DeleteConfirmRequest schema, min_length=6, max_length=6). verify_challenge_code() does a timing-safe comparison against the server-stored code keyed by (admin_id, "delete_user_{user_id}").
  implication: Backend design is correct. The entire frontend integration is wrong — wrong code source, wrong transport, no body support.

## Resolution

root_cause: Three compounding bugs: (1) ChallengeCodeDialog generates its code client-side and never calls the backend challenge endpoint, so the backend has no stored code to verify against; (2) UserTable.executeAction passes hardcoded "CLIENT" as challenge_code instead of the actual verified code; (3) useDeleteUser sends the code as a query param and adminApiClient.delete() sends no body, but the backend requires the code in the JSON request body.

fix: (not applied - diagnose-only mode)
verification: (not applied)
files_changed: []
