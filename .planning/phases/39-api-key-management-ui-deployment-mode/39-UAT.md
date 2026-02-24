---
status: diagnosed
phase: 39-api-key-management-ui-deployment-mode
source: 39-01-SUMMARY.md, 39-02-SUMMARY.md, 39-03-SUMMARY.md
started: 2026-02-24T14:00:00Z
updated: 2026-02-24T14:15:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Health Endpoint
expected: GET /api/v1/health returns JSON with status "healthy" and db_connected field. Accessible without authentication.
result: issue
reported: "http://localhost:8000/api/v1/health returns 404 Not Found. Route is mounted at /v1/health instead of /api/v1/health because api_v1_router has prefix='/v1' but app.include_router doesn't add '/api' prefix."
severity: major

### 2. Public Frontend API Key Credit Display
expected: On the public frontend Settings page, each API key in the list shows "Credits: 0.0" (or the actual usage amount) in the key metadata row alongside prefix and creation date.
result: issue
reported: "Missing 'Last Used' date in metadata row. Label says 'Credits' but should say 'Credit Usage'."
severity: minor

### 3. Admin Frontend API Keys Tab Visible
expected: In the admin portal, opening a user's detail view shows 5 tabs: Overview, Credits, Activity, Sessions, API Keys. The "API Keys" tab is the 5th tab.
result: pass

### 4. Admin Can List User API Keys
expected: Clicking the "API Keys" tab for a user shows a list of that user's API keys with name, key prefix, creation date, and credit usage. Revoked keys appear dimmed with strikethrough and show revocation date.
result: issue
reported: "Works but should be displayed as a table instead of stacked cards."
severity: minor

### 5. Admin Can Create API Key for User
expected: Clicking "Create API Key" in the admin API Keys tab opens a form to enter a key name. After creation, the full API key is displayed once in a dialog with an explicit "I have copied my key" dismissal. The key cannot be retrieved again after closing.
result: pass

### 6. Admin Can Revoke User API Key
expected: Clicking "Revoke" on an active API key shows an AlertDialog confirmation. After confirming, the key is revoked immediately — it appears dimmed with strikethrough in the list and shows the revocation timestamp.
result: issue
reported: "Backend returns 204 No Content successfully but UI shows error toast 'String does not match expected pattern'. Key list doesn't update until page refresh. Cache invalidation or response handling broken."
severity: major

### 7. Admin-Created Keys Show Badge
expected: API keys created by an admin (on behalf of a user) display an "Admin" badge in the admin API Keys tab to distinguish them from user-created keys.
result: issue
reported: "Admin badge shows correctly in admin frontend. But no badge shown on the public frontend for admin-created keys."
severity: minor

### 8. API Mode CORS Headers
expected: When backend runs with SPECTRA_MODE=api, CORS headers allow any origin (Access-Control-Allow-Origin: *) but do NOT include Access-Control-Allow-Credentials. Bearer token auth works from any domain.
result: skipped
reason: Will test at milestone level after all phases complete

## Summary

total: 8
passed: 2
issues: 5
pending: 0
skipped: 1

## Gaps

- truth: "GET /api/v1/health returns JSON with status healthy and db_connected field"
  status: failed
  reason: "User reported: http://localhost:8000/api/v1/health returns 404 Not Found. Route mounted at /v1/health instead of /api/v1/health."
  severity: major
  test: 1
  root_cause: "api_v1_router has prefix='/v1' but app.include_router() has no prefix argument. Actual route is /v1/health, missing /api segment."
  artifacts:
    - path: "backend/app/routers/api_v1/__init__.py"
      issue: "APIRouter prefix is '/v1' instead of '/api/v1'"
  missing:
    - "Change prefix from '/v1' to '/api/v1' in api_v1_router"
  debug_session: ".planning/debug/health-endpoint-404.md"
- truth: "API key metadata row shows credit usage and last used date"
  status: failed
  reason: "User reported: Missing 'Last Used' date in metadata row. Label says 'Credits' but should say 'Credit Usage'."
  severity: minor
  test: 2
  root_cause: "last_used_at is NULL (no usage yet, Phase 40 not implemented) and UI hides null values instead of showing 'Never'. Label text is 'Credits:' instead of 'Credit Usage:'."
  artifacts:
    - path: "frontend/src/components/settings/ApiKeySection.tsx"
      issue: "Conditional render hides Last Used when null; label says 'Credits' not 'Credit Usage'"
  missing:
    - "Show 'Last used: Never' when last_used_at is null instead of hiding"
    - "Change 'Credits:' label to 'Credit Usage:'"
  debug_session: ""
- truth: "Admin API key list displays as table format"
  status: failed
  reason: "User reported: Works but should be displayed as a table instead of stacked cards."
  severity: minor
  test: 4
  root_cause: "UserApiKeysTab renders keys as stacked bordered divs (space-y-3 with rounded-lg border p-3) instead of a Table component."
  artifacts:
    - path: "admin-frontend/src/components/users/UserApiKeysTab.tsx"
      issue: "Key list rendered as stacked card divs instead of Table"
  missing:
    - "Replace card layout with Table/TableBody/TableRow from shadcn/ui with columns: Name, Status, Key Prefix, Created, Last Used, Credits, Actions"
  debug_session: ""
- truth: "Revoking API key updates UI immediately without page refresh"
  status: failed
  reason: "User reported: Backend returns 204 successfully but UI shows error toast 'String does not match expected pattern'. Key list doesn't update until page refresh."
  severity: major
  test: 6
  root_cause: "useRevokeUserApiKey mutationFn calls res.json() unsafely on error path (throws on empty body). adminApiClient sets Content-Type: application/json on DELETE with no body. Cache invalidation only in onSuccess, never fires on error."
  artifacts:
    - path: "admin-frontend/src/hooks/useApiKeys.ts"
      issue: "Unsafe res.json() in error path; cache invalidation only in onSuccess"
    - path: "admin-frontend/src/lib/admin-api-client.ts"
      issue: "Unconditional Content-Type: application/json on body-less DELETE"
  missing:
    - "Guard res.json() with try/catch in error path"
    - "Handle 204 No Content explicitly (no body to parse)"
    - "Move cache invalidation to onSettled so it fires on success AND error"
    - "Only set Content-Type: application/json when request has a body"
  debug_session: ".planning/debug/admin-apikey-revoke-error.md"
- truth: "Admin-created keys show badge on public frontend"
  status: failed
  reason: "User reported: Admin badge shows correctly in admin frontend but no badge shown on the public frontend for admin-created keys."
  severity: minor
  test: 7
  root_cause: "Full-stack data omission: ApiKeyListItem schema excludes created_by_admin_id (only AdminApiKeyListItem has it). Frontend TS interface and component have no awareness of the field."
  artifacts:
    - path: "backend/app/schemas/api_key.py"
      issue: "ApiKeyListItem missing created_by_admin_id field"
    - path: "frontend/src/hooks/useApiKeys.ts"
      issue: "ApiKeyListItem interface missing created_by_admin_id"
    - path: "frontend/src/components/settings/ApiKeySection.tsx"
      issue: "No Admin badge rendering logic"
  missing:
    - "Add created_by_admin_id to ApiKeyListItem schema"
    - "Add created_by_admin_id to frontend TS interface"
    - "Add Admin badge rendering in ApiKeySection when created_by_admin_id is not null"
  debug_session: ""
