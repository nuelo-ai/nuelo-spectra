---
status: complete
phase: 27-credit-system
source: 27-01-SUMMARY.md, 27-02-SUMMARY.md, 27-03-SUMMARY.md, 27-04-SUMMARY.md
started: 2026-02-16T23:10:00Z
updated: 2026-02-16T23:20:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Credit Deduction on Chat
expected: Sending a chat message deducts the configured credit cost from the user's balance. The deduction is atomic — two concurrent requests cannot overdraw below zero.
result: pass

### 2. Out-of-Credits Blocking
expected: A user with zero credits (or less than the cost of one message) sees an "out of credits" error and cannot send chat messages. The API returns HTTP 402.
result: issue
reported: "failed - the chat UI does not provide the out of credit error nor display the remaining credit"
severity: major

### 3. Admin Credit Balance View
expected: Admin can view any user's credit balance and full transaction history (date, cost, remaining balance, admin note) via admin API endpoints.
result: issue
reported: "failed - credit balance is shown but transaction history remains blank despite adjustment was made"
severity: major

### 4. Admin Credit Adjustment
expected: Admin can manually add or deduct credits for a user via admin API. The adjustment is logged as a credit transaction with admin note.
result: issue
reported: "failed - admin can add or deduct but no re-enter password as defined in 27-CONTEXT.md, and adjustment is not logged as transaction with admin note"
severity: major

### 5. Credit Initialization on Registration
expected: When a new user registers, a UserCredit row is created with the initial balance matching their tier allocation from user_classes.yaml.
result: pass

### 6. Public Credit Balance Endpoint
expected: Authenticated users can check their own credit balance via GET `/api/credits/balance`. Returns current balance and tier info.
result: pass

### 7. Scheduled Credit Reset
expected: The APScheduler job runs at the configured interval and resets user credits to their tier allocation. Uses idempotent processing (tracks last_reset_at) to prevent double-resets.
result: skipped

## Summary

total: 7
passed: 3
issues: 3
pending: 0
skipped: 1

## Gaps

- truth: "User sees out-of-credits error in chat UI and credit balance is visible"
  status: failed
  reason: "User reported: the chat UI does not provide the out of credit error nor display the remaining credit"
  severity: major
  test: 2
  artifacts: []
  missing: []

- truth: "Admin can view user's full transaction history"
  status: failed
  reason: "User reported: credit balance is shown but transaction history remains blank despite adjustment was made"
  severity: major
  test: 3
  artifacts: []
  missing: []

- truth: "Admin credit adjustment requires password re-entry and logs transaction with admin note"
  status: failed
  reason: "User reported: no re-enter password for credit adjustment, and adjustment is not logged as transaction with admin note"
  severity: major
  test: 4
  artifacts: []
  missing: []

- truth: "Settings page Default User Class dropdown shows all tiers from user_classes.yaml"
  status: failed
  reason: "User reported: dropdown hardcoded to Free/Standard/Premium, missing Free Trial and Internal tiers"
  severity: minor
  test: n/a (observed during testing)
  artifacts:
    - path: "admin-frontend/src/components/settings/SettingsForm.tsx"
      issue: "Hardcoded tier options at lines 145-147"
  missing: []
