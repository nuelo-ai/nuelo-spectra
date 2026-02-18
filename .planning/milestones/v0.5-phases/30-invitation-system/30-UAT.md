---
status: diagnosed
phase: 30-invitation-system
source: 30-01-SUMMARY.md, 30-02-SUMMARY.md, 30-03-SUMMARY.md
started: 2026-02-17T00:15:00Z
updated: 2026-02-17T00:25:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Create Invitation
expected: Admin enters an email address and the system generates a unique time-limited invite link (default 7 days, configurable via invite_expiry_days setting). A branded invitation email is sent via SMTP. The invite token is stored as SHA-256 hash in the invitations table.
result: pass

### 2. Invitation List and Management
expected: Admin can view all invitations (pending/accepted/expired) with status filter. Admin can revoke pending invitations and resend expired or pending invitations (with cooldown).
result: pass

### 3. Invite Token Validation
expected: GET `/auth/invite-validate?token=...` returns the email for a valid pending token. Returns error for invalid, expired, or already-used tokens.
result: pass

### 4. Invite Registration Flow
expected: Invited user clicks the link, sees a registration form with pre-filled locked email, sets their password and display name, and completes registration. The invite token is invalidated (single-use). User is auto-logged in after registration.
result: issue
reported: "1) Registration page doesn't show when another user is logged in (auth guard issue). 2) User NOT auto-logged in after registration — redirects to login page. 3) Invite registration shows 'Display Name' instead of 'First Name'/'Last Name' fields — inconsistent with normal registration page."
severity: major

### 5. Invite Registration When Signup Disabled
expected: Even when `allow_public_signup` is false, invited users can still register through the invite link. The invite bypasses the signup gate.
result: pass

## Summary

total: 5
passed: 4
issues: 1
pending: 0
skipped: 0

## Gaps

- truth: "Invite registration auto-logs in user and has consistent form fields with normal registration"
  status: failed
  reason: "User reported: 1) Registration page doesn't show when another user is logged in. 2) User NOT auto-logged in — redirects to login page. 3) Shows 'Display Name' instead of 'First Name'/'Last Name' fields, inconsistent with normal registration."
  severity: major
  test: 4
  root_cause: "Three sub-issues: (1) invite page in (auth) route group inherits auth guard redirect, (2) setTokens() without setUser() — AuthContext not updated so dashboard redirects to login, (3) form uses single displayName field instead of firstName/lastName"
  artifacts:
    - path: "frontend/src/app/(auth)/layout.tsx"
      issue: "Auth guard redirects authenticated users from invite page"
    - path: "frontend/src/app/(auth)/invite/[token]/page.tsx"
      issue: "setTokens without fetching /auth/me and setUser; single displayName field"
    - path: "backend/app/schemas/auth.py"
      issue: "InviteRegisterRequest uses display_name instead of first_name/last_name"
    - path: "backend/app/routers/auth.py"
      issue: "Maps display_name to first_name, hardcodes last_name=None"
  missing:
    - "Move invite page out of (auth) route group"
    - "After setTokens, fetch /auth/me and call setUser before redirect"
    - "Replace displayName with firstName/lastName in form, schema, and endpoint"
