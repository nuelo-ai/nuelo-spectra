---
status: diagnosed
phase: 29-user-management
source: 29-01-SUMMARY.md, 29-02-SUMMARY.md, 29-03-SUMMARY.md
started: 2026-02-17T00:00:00Z
updated: 2026-02-17T00:15:00Z
---

## Current Test

[testing complete]

## Tests

### 1. User Listing with Search and Filter
expected: Admin can list all users with pagination (20/page). Can search by email or name. Can filter by active/inactive status, user class, and signup date. Can sort by signup date, last login, name, or credit balance.
result: issue
reported: "Search OK, filter OK (user class missing tiers), sorting not available, Last Login field shows empty, Credit Balance not listed"
severity: major

### 2. User Detail View
expected: Admin can view a user's full profile: name, email, signup date, last login, active/inactive status, tier, credit balance, file count, chat session count, and message count.
result: issue
reported: "Transaction history not shown after manual adjustment, last login not shown"
severity: major

### 3. User Activity Timeline
expected: Admin can view a user's monthly activity timeline showing messages and sessions by month.
result: issue
reported: "Activity not shown"
severity: major

### 4. Deactivate User Account
expected: Admin can deactivate a user. The user's active sessions are immediately invalidated (in-memory token revocation). The deactivated user cannot access the platform until reactivated.
result: pass

### 5. Activate User Account
expected: Admin can reactivate a previously deactivated user. The user can log in and use the platform again.
result: pass

### 6. Trigger Password Reset
expected: Admin can trigger a password reset email for any user. The user receives the standard password reset email with a valid token link.
result: issue
reported: "Email sent successfully but password reset link redirects to /chat when browser has active session instead of showing reset form. Reset page should load regardless of login state as browser might have different user logged in."
severity: minor

### 7. User Delete with Challenge Code
expected: Admin requests a delete challenge code, then confirms deletion with the code. The user is hard-deleted with cascade (files, sessions, credits). Audit logs are anonymized (target_id replaced with deleted_user_XXXX).
result: issue
reported: "Challenge code dialog appears but user was not deleted after confirming the code"
severity: blocker

### 8. Bulk Operations
expected: Admin can perform bulk actions on multiple users: activate, deactivate, tier change, credit adjustment, and delete (with challenge code). Each bulk operation is capped at 100 users.
result: issue
reported: "Checkboxes on user rows cannot be selected, preventing any bulk operations"
severity: blocker

## Summary

total: 8
passed: 2
issues: 6
pending: 0
skipped: 0

## Gaps

- truth: "User listing supports sorting, shows last login and credit balance"
  status: failed
  reason: "User reported: sorting not available, Last Login field shows empty, Credit Balance not listed"
  severity: major
  test: 1
  root_cause: "Three sub-issues: (1) UserTable has no TanStack sort config, (2) login handler calls db.flush() without db.commit() so last_login_at is never persisted, (3) credit_balance column definition missing from UserTable"
  artifacts:
    - path: "admin-frontend/src/components/users/UserTable.tsx"
      issue: "No getSortedRowModel, no sorting state, no sort handlers; no credit_balance column"
    - path: "backend/app/routers/auth.py"
      issue: "Line 153: db.flush() without db.commit() — last_login_at never saved"
  missing:
    - "Add TanStack Table sorting config to UserTable"
    - "Change db.flush() to db.commit() in login handler"
    - "Add credit_balance column to UserTable"

- truth: "User detail shows transaction history and last login"
  status: failed
  reason: "User reported: transaction history not shown after manual adjustment, last login not shown"
  severity: major
  test: 2
  root_cause: "Transaction history: same URL mismatch as P27-T3. Last login: same db.flush() bug as P29-T1"
  artifacts:
    - path: "admin-frontend/src/hooks/useUsers.ts"
      issue: "Line 77: wrong URL for transaction history"
    - path: "backend/app/routers/auth.py"
      issue: "db.flush() without commit"
  missing:
    - "Fix transaction history URL (covered by P27-T3 fix)"
    - "Fix db.commit() (covered by P29-T1 fix)"

- truth: "User activity timeline displays monthly messages and sessions"
  status: failed
  reason: "User reported: Activity not shown"
  severity: major
  test: 3
  root_cause: "NOT A BUG — feature is fully implemented end-to-end. Test user had no ChatMessage/ChatSession records. Timeline correctly shows 'No activity data available' for users without chat history."
  artifacts: []
  missing:
    - "Test with user that has chat history to verify"

- truth: "Password reset link shows reset form regardless of login state"
  status: failed
  reason: "User reported: reset link redirects to /chat when browser has active session instead of showing reset form"
  severity: minor
  test: 6
  root_cause: "(auth)/layout.tsx unconditionally redirects authenticated users to /dashboard — reset-password inherits this guard"
  artifacts:
    - path: "frontend/src/app/(auth)/layout.tsx"
      issue: "Lines 19-28: blanket auth guard redirects all (auth) pages including reset-password"
  missing:
    - "Move reset-password (and invite) out of (auth) route group, or skip redirect for those paths"

- truth: "User delete executes after challenge code confirmation"
  status: failed
  reason: "User reported: challenge code dialog appears but user was not deleted after confirming the code"
  severity: blocker
  test: 7
  root_cause: "Three compounding bugs: (1) ChallengeCodeDialog generates code client-side, never calls backend, (2) hardcoded 'CLIENT' sent as challenge_code, (3) code sent as query param not JSON body + adminApiClient.delete() has no body support"
  artifacts:
    - path: "admin-frontend/src/components/shared/ChallengeCodeDialog.tsx"
      issue: "Generates code client-side; onConfirm takes no argument"
    - path: "admin-frontend/src/components/users/UserTable.tsx"
      issue: "Passes hardcoded 'CLIENT' as challenge_code"
    - path: "admin-frontend/src/hooks/useUsers.ts"
      issue: "useDeleteUser sends code as query param not body"
    - path: "admin-frontend/src/lib/admin-api-client.ts"
      issue: "delete() method has no body parameter"
  missing:
    - "Rewrite delete flow: fetch challenge from backend, display in dialog, pass code back, send as JSON body"
    - "Add body support to adminApiClient.delete()"

- truth: "Bulk operation checkboxes are selectable on user rows"
  status: failed
  reason: "User reported: checkboxes on user rows cannot be selected, preventing any bulk operations"
  severity: blocker
  test: 8
  root_cause: "rowSelection built with numeric index keys but getRowId returns UUIDs — row.getIsSelected() always false; onRowSelectionChange reverse-maps UUID keys via Number() producing NaN"
  artifacts:
    - path: "admin-frontend/src/components/users/UserTable.tsx"
      issue: "Lines 275-283: rowSelection uses String(i) keys; lines 294-301: maps UUID keys through Number()"
  missing:
    - "Use user.id (UUID) as rowSelection keys"
    - "Map UUID keys directly in onRowSelectionChange"
