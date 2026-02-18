---
status: complete
phase: 31-dashboard-admin-frontend
source: 31-06-SUMMARY.md, 31-07-SUMMARY.md, 31-08-SUMMARY.md
started: 2026-02-17T18:00:00Z
updated: 2026-02-18T00:00:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Admin Login Lockout Message
expected: After 5 failed admin login attempts, the 429 error toast shows a readable message like "Too many login attempts. Try again in 15 minutes." — not [object Object].
result: pass

### 2. Dashboard Active Today Metric
expected: After logging in via the admin portal, the "Active Today" card on the dashboard shows at least 1 (reflecting your login).
result: pass

### 3. Dashboard Credit Used Metric
expected: If any user has sent chat messages (consuming credits), the "Credit Used" metric on the dashboard shows a non-zero value. If no messages sent, it shows 0 — but NOT a wrong number.
result: pass

### 4. OpenAPI Docs in Public Mode
expected: When backend runs with SPECTRA_MODE=public, visiting /docs shows zero /api/admin/ routes. The catch-all is hidden from the schema.
result: pass

### 5. User Table Sorting
expected: On the Users page, clicking column headers (Name, Email, Tier, Created, Last Login, Credits) sorts the table. An arrow indicator shows sort direction.
result: pass

### 6. User Table Credit Balance Column
expected: The Users table has a "Credits" column showing each user's credit balance as a number (e.g., "100.0").
result: pass

### 7. Bulk Checkbox Selection
expected: On the Users page, clicking the header checkbox selects all rows. Individual row checkboxes are clickable. Selected count updates correctly.
result: pass

### 8. Bulk Delete with Challenge Code
expected: Select user(s), click bulk Delete. A dialog appears showing a challenge code fetched from the backend (with loading spinner). Type the code to enable Confirm. Deletion succeeds.
result: pass

### 9. Single User Delete with Challenge Code
expected: On user detail page, click Delete. Dialog fetches and displays a challenge code from backend. Type the code to confirm. User is deleted.
result: pass

### 10. Transaction History
expected: On user detail Credits tab, transaction history table loads with data (if any transactions exist). No blank page or 404 error.
result: pass

### 11. Credit Adjustment with Password
expected: On user detail Credits tab, the credit adjustment form has Amount, Reason, and Admin Password fields. Submitting without password shows validation error. With valid password, adjustment succeeds.
result: pass

### 12. Settings Tier Dropdown
expected: On Settings page, the "Default User Class" dropdown shows tier names fetched from the API (e.g., Free, Standard, Premium) — not hardcoded values.
result: pass

### 13. Settings Credit Reset Policy Display
expected: On Settings page, credit reset policy is shown as a read-only per-tier table (Tier | Reset Policy | Credits) — not a global dropdown.
result: pass

### 14. Audit Log Column Sorting
expected: On Audit Log page, clicking column headers (Date, Action, Admin, Target Type) sorts the table server-side. Sort arrows appear.
result: pass

### 15. Credit Balance in Public Sidebar
expected: In the public frontend sidebar, below your email, your credit balance is shown (e.g., "100.0 credits"). If balance is low, it appears in red.
result: pass

### 16. Chat Credit Error Message
expected: When a user with zero credits sends a chat message, the chat shows a specific "out of credits" error message — not a generic "Something went wrong."
result: issue
reported: "when I exhaust the credit, and try to send a message, a generic error message shown 'Error Something went wrong. Please try again.' it should say that user ran out of credit"
severity: major

### 17. Invite Registration Page Access
expected: The /invite/[token] page loads even when another user is already logged in. It is not redirected to /dashboard.
result: pass

### 18. Invite Registration Form Fields
expected: The invite registration form has First Name, Last Name, and Password fields — not a single "Display Name" field.
result: pass

### 19. Password Reset Page Access
expected: The /reset-password page loads even when a user is already logged in. It is not redirected to /dashboard.
result: pass

## Summary

total: 19
passed: 18
issues: 1
pending: 0
skipped: 0

## Gaps

- truth: "When a user with zero credits sends a chat message, the chat shows a specific 'out of credits' error message"
  status: fixed
  reason: "User reported: generic 'Error Something went wrong. Please try again.' shown instead of out-of-credits message"
  severity: major
  test: 16
  root_cause: "errorBody.detail is an object {error, message, ...}, not a string — new Error(object) produces '[object Object]' so credits check never matches"
  artifacts:
    - path: "frontend/src/hooks/useSSEStream.ts"
      issue: "line 122: errorBody?.detail is object, needs errorBody?.detail?.message"
    - path: "frontend/src/components/chat/ChatInterface.tsx"
      issue: "lines 600-602: credits check correct but never triggered due to upstream bug"
  missing:
    - "Extract string from nested detail object before throwing Error"
  debug_session: ".planning/debug/p31-t16-chat-credit-error-message.md"
