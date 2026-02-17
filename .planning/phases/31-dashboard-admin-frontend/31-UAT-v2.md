---
status: testing
phase: 31-dashboard-admin-frontend
source: 31-06-SUMMARY.md, 31-07-SUMMARY.md, 31-08-SUMMARY.md
started: 2026-02-17T18:00:00Z
updated: 2026-02-17T18:00:00Z
---

## Current Test

number: 1
name: Admin Login Lockout Message
expected: |
  After 5 failed admin login attempts, the 429 error toast shows a human-readable message like "Too many login attempts. Try again in 15 minutes." — not [object Object].
awaiting: user response

## Tests

### 1. Admin Login Lockout Message
expected: After 5 failed admin login attempts, the 429 error toast shows a readable message like "Too many login attempts. Try again in 15 minutes." — not [object Object].
result: [pending]

### 2. Dashboard Active Today Metric
expected: After logging in via the admin portal, the "Active Today" card on the dashboard shows at least 1 (reflecting your login).
result: [pending]

### 3. Dashboard Credit Used Metric
expected: If any user has sent chat messages (consuming credits), the "Credit Used" metric on the dashboard shows a non-zero value. If no messages sent, it shows 0 — but NOT a wrong number.
result: [pending]

### 4. OpenAPI Docs in Public Mode
expected: When backend runs with SPECTRA_MODE=public, visiting /docs shows zero /api/admin/ routes. The catch-all is hidden from the schema.
result: [pending]

### 5. User Table Sorting
expected: On the Users page, clicking column headers (Name, Email, Tier, Created, Last Login, Credits) sorts the table. An arrow indicator shows sort direction.
result: [pending]

### 6. User Table Credit Balance Column
expected: The Users table has a "Credits" column showing each user's credit balance as a number (e.g., "100.0").
result: [pending]

### 7. Bulk Checkbox Selection
expected: On the Users page, clicking the header checkbox selects all rows. Individual row checkboxes are clickable. Selected count updates correctly.
result: [pending]

### 8. Bulk Delete with Challenge Code
expected: Select user(s), click bulk Delete. A dialog appears showing a challenge code fetched from the backend (with loading spinner). Type the code to enable Confirm. Deletion succeeds.
result: [pending]

### 9. Single User Delete with Challenge Code
expected: On user detail page, click Delete. Dialog fetches and displays a challenge code from backend. Type the code to confirm. User is deleted.
result: [pending]

### 10. Transaction History
expected: On user detail Credits tab, transaction history table loads with data (if any transactions exist). No blank page or 404 error.
result: [pending]

### 11. Credit Adjustment with Password
expected: On user detail Credits tab, the credit adjustment form has Amount, Reason, and Admin Password fields. Submitting without password shows validation error. With valid password, adjustment succeeds.
result: [pending]

### 12. Settings Tier Dropdown
expected: On Settings page, the "Default User Class" dropdown shows tier names fetched from the API (e.g., Free, Standard, Premium) — not hardcoded values.
result: [pending]

### 13. Settings Credit Reset Policy Display
expected: On Settings page, credit reset policy is shown as a read-only per-tier table (Tier | Reset Policy | Credits) — not a global dropdown.
result: [pending]

### 14. Audit Log Column Sorting
expected: On Audit Log page, clicking column headers (Date, Action, Admin, Target Type) sorts the table server-side. Sort arrows appear.
result: [pending]

### 15. Credit Balance in Public Sidebar
expected: In the public frontend sidebar, below your email, your credit balance is shown (e.g., "100.0 credits"). If balance is low, it appears in red.
result: [pending]

### 16. Chat Credit Error Message
expected: When a user with zero credits sends a chat message, the chat shows a specific "out of credits" error message — not a generic "Something went wrong."
result: [pending]

### 17. Invite Registration Page Access
expected: The /invite/[token] page loads even when another user is already logged in. It is not redirected to /dashboard.
result: [pending]

### 18. Invite Registration Form Fields
expected: The invite registration form has First Name, Last Name, and Password fields — not a single "Display Name" field.
result: [pending]

### 19. Password Reset Page Access
expected: The /reset-password page loads even when a user is already logged in. It is not redirected to /dashboard.
result: [pending]

## Summary

total: 19
passed: 0
issues: 0
pending: 19
skipped: 0

## Gaps

[none yet]
