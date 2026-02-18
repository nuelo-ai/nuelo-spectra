---
status: diagnosed
phase: 26-foundation
source: 26-01-SUMMARY.md, 26-02-SUMMARY.md, 26-03-SUMMARY.md
started: 2026-02-16T23:00:00Z
updated: 2026-02-16T23:10:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Database Migration
expected: Running `alembic upgrade head` in the backend directory creates 5 new tables (admin_audit_log, platform_settings, user_credits, credit_transactions, invitations) and adds `is_admin` and `user_class` columns to the users table. Existing users get backfilled with is_admin=false, user_class=free, and credit records created.
result: pass

### 2. Split-Horizon Mode Gating
expected: Starting backend with `SPECTRA_MODE=public` exposes zero `/api/admin/` routes. Starting with `SPECTRA_MODE=admin` exposes only admin routes. `SPECTRA_MODE=dev` exposes both public and admin routes.
result: issue
reported: "Catch-all /api/admin/{path} routes visible in OpenAPI /docs in public mode - they return Admin Route Not Found but shouldn't appear in docs at all"
severity: minor

### 3. Admin Seed CLI
expected: Running `python -m app.cli seed-admin` creates an admin user in the database with is_admin=true. The command prompts for or accepts email/password.
result: pass

### 4. Admin Login
expected: POST to `/api/admin/auth/login` with the seeded admin credentials returns a JWT token. A regular (non-admin) user hitting the same endpoint gets a 403 Forbidden.
result: pass

### 5. Admin Session Timeout
expected: An admin JWT expires after the configured inactivity timeout (default 30 minutes). After expiry, admin API calls are rejected requiring re-login. The sliding window token reissue extends the session on active use (X-Admin-Token header in response).
result: skipped

### 6. Login Lockout
expected: After 5 consecutive failed login attempts to the admin auth endpoint, the account is locked out for 15 minutes. Further attempts are rejected even with correct credentials until the lockout expires.
result: issue
reported: "No indicator to user that account is locked. Error message only shows [object Object] text in toast notification instead of a readable lockout message."
severity: major

### 7. Audit Logging
expected: Every admin API call creates a row in the `admin_audit_log` table with admin_id, action name, target, timestamp, and details JSON.
result: pass

## Summary

total: 7
passed: 4
issues: 2
pending: 0
skipped: 1

## Gaps

- truth: "Starting backend with SPECTRA_MODE=public exposes zero /api/admin/ routes in OpenAPI docs"
  status: failed
  reason: "User reported: Catch-all /api/admin/{path} routes visible in OpenAPI /docs in public mode - they return Admin Route Not Found but shouldn't appear in docs at all"
  severity: minor
  test: 2
  root_cause: "Catch-all @app.api_route in main.py line 326 missing include_in_schema=False"
  artifacts:
    - path: "backend/app/main.py"
      issue: "Line 326: @app.api_route missing include_in_schema=False"
  missing:
    - "Add include_in_schema=False to the catch-all decorator"

- truth: "Login lockout shows clear error message to admin user"
  status: failed
  reason: "User reported: No indicator to user that account is locked. Error message only shows [object Object] text in toast notification instead of a readable lockout message."
  severity: major
  test: 6
  root_cause: "useAdminAuth.tsx passes errorData.detail (which can be an array for 422) directly to new Error(), producing [object Object]; also lockout 429 message lacks minutes remaining"
  artifacts:
    - path: "admin-frontend/src/hooks/useAdminAuth.tsx"
      issue: "Lines 78-82: no guard against detail being array/object"
    - path: "backend/app/routers/admin/auth.py"
      issue: "Lockout 429 message lacks remaining minutes"
  missing:
    - "Check typeof errorData.detail before passing to Error()"
    - "Include minutes_remaining in lockout response"
