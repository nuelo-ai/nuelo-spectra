---
status: complete
phase: 28-platform-config
source: 28-01-SUMMARY.md, 28-02-SUMMARY.md
started: 2026-02-16T23:20:00Z
updated: 2026-02-17T00:00:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Platform Settings API
expected: Admin can GET `/api/admin/settings` to view all platform settings (allow_public_signup, default_user_class, invite_expiry_days, credit_reset_policy, default_credit_cost). Admin can PATCH to update any setting, changes are persisted in the platform_settings table with 30-second TTL cache.
result: issue
reported: "All settings work correctly except the Default User Class dropdown is missing tiers — only Free/Standard/Premium, missing Free Trial and Internal from user_classes.yaml"
severity: minor

### 2. Tier Summary Endpoint
expected: GET `/api/admin/tiers` returns all tiers defined in user_classes.yaml with display_name, credits, reset_policy, and live user counts from the database.
result: pass

### 3. Admin Tier Change
expected: Admin can change a user's tier via PUT `/api/admin/tiers/users/{user_id}`. The change atomically updates user_class and resets the user's credit balance to the new tier's allocation.
result: pass

### 4. Signup Gating — Invite Only Mode
expected: When `allow_public_signup` is set to false, the public signup endpoint rejects new registrations with an "invite-only" message. Only users with a valid invite token can complete registration. Takes effect immediately without server restart.
result: pass

### 5. Frontend Invite-Only Message
expected: When signup is disabled, the frontend registration page shows a branded "invite-only" message instead of the registration form. Frontend fails open on fetch error (shows form rather than blocking).
result: pass

### 6. Runtime Configurable Credit Cost
expected: Changing `default_credit_cost` in platform settings takes effect on the next chat message (within 30s TTL). No server restart needed.
result: pass

### 7. Runtime Configurable Default Tier
expected: Changing `default_user_class` in platform settings affects newly registered users — they get the updated tier. Existing users are unaffected.
result: pass

## Summary

total: 7
passed: 6
issues: 1
pending: 0
skipped: 0

## Gaps

- truth: "Settings page Default User Class dropdown shows all tiers from user_classes.yaml"
  status: failed
  reason: "User reported: dropdown hardcoded to Free/Standard/Premium, missing Free Trial and Internal tiers"
  severity: minor
  test: 1
  artifacts:
    - path: "admin-frontend/src/components/settings/SettingsForm.tsx"
      issue: "Hardcoded tier options at lines 145-147"
  missing: []
