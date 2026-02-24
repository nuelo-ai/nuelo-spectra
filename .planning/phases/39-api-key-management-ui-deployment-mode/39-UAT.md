---
status: complete
phase: 39-api-key-management-ui-deployment-mode
source: 39-01-SUMMARY.md, 39-02-SUMMARY.md, 39-03-SUMMARY.md, 39-04-SUMMARY.md, 39-05-SUMMARY.md
started: 2026-02-24T15:00:00Z
updated: 2026-02-24T16:10:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

[testing complete]

## Tests

### 1. Health Endpoint at /api/v1/health
expected: GET /api/v1/health returns 200 JSON with status "healthy" and db_connected field. Accessible without authentication.
result: pass

### 2. Public Frontend API Key List Display
expected: On the public frontend Settings page, each API key shows: key name, key prefix, "Last used: Never" (or date if used), and "Credit Usage: 0.0" label. Never-used keys show "Never" instead of hiding the field.
result: pass (fixed inline: reverted router prefix to /v1, dual-mounted at /v1 and /api/v1)

### 3. Public Frontend Admin Badge
expected: API keys created by an admin show an "Admin" badge with Shield icon on the public frontend Settings page, distinguishing them from user-created keys.
result: pass

### 4. Admin API Keys Tab Visible
expected: In the admin portal, opening a user's detail view shows 5 tabs including "API Keys" as the 5th tab.
result: pass

### 5. Admin API Key List as Table
expected: Admin API Keys tab shows keys in a table with columns: Name, Key Prefix, Created, Last Used, Credits, Actions. Revoked keys appear dimmed with strikethrough names.
result: issue
reported: "Table layout works but column header says 'Credit' instead of 'Credit Usage'. Label needs to match public frontend."
severity: cosmetic

### 6. Admin Create API Key
expected: Clicking "Create API Key" opens a form for key name. After creation, the full API key is displayed once in a dialog with "I have copied my key" dismissal. Key cannot be retrieved again.
result: pass

### 7. Admin Revoke API Key
expected: Clicking "Revoke" shows confirmation dialog. After confirming, key is revoked immediately — list updates without page refresh, success toast shown, no error toast.
result: pass (fixed inline: proxy 204 null body)

### 8. API Mode CORS Headers
expected: When backend runs with SPECTRA_MODE=api, CORS allows any origin (Access-Control-Allow-Origin: *) without credentials. Bearer token auth works from any domain.
result: skipped
reason: Will test at milestone level

## Summary

total: 8
passed: 6
issues: 1
pending: 0
skipped: 1

## Gaps

- truth: "Public frontend API key list loads and displays key metadata"
  status: failed
  reason: "User reported: Not loaded. Backend log shows GET /v1/keys 404 Not Found. Router prefix change from /v1 to /api/v1 broke the keys endpoint — frontend still calls /v1/keys."
  severity: blocker
  test: 2
  artifacts: []
  missing: []
- truth: "Admin API key table column header says 'Credit Usage'"
  status: resolved
  reason: "User reported: Column header said 'Credit' instead of 'Credit Usage'. Fixed inline (a16477b)."
  severity: cosmetic
  test: 5
  artifacts: []
  missing: []
