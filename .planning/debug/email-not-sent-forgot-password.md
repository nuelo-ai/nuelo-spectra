---
status: diagnosed
trigger: "Email not sent in forgot password flow - UAT Test 7"
created: 2026-02-04T00:00:00Z
updated: 2026-02-04T00:15:00Z
symptoms_prefilled: true
goal: find_root_cause_only
---

## Current Focus

hypothesis: CONFIRMED - EMAIL_SERVICE_API_KEY="dev-api-key" prevents dev mode, code attempts Mailgun API with fake key
test: Logic analysis complete - dev mode check is falsy check, .env has non-empty value
expecting: Root cause identified - need to remove or comment EMAIL_SERVICE_API_KEY to enable dev mode
next_action: Document root cause for UAT gaps section

## Symptoms

expected: Password reset link appears in console logs (dev mode) or sent via email (production mode with EMAIL_SERVICE_API_KEY)
actual: "email not sent. likely email provider is not set correctly. can be solved later"
errors: Unknown - need to check logs
reproduction: Trigger forgot-password endpoint during UAT Test 7
started: Discovered during UAT testing

## Eliminated

## Evidence

- timestamp: 2026-02-04T00:05:00Z
  checked: /Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/backend/.env
  found: EMAIL_SERVICE_API_KEY=dev-api-key (non-empty string)
  implication: Dev mode console logging will NOT trigger (line 32: if not settings.email_service_api_key)

- timestamp: 2026-02-04T00:06:00Z
  checked: /Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/backend/app/services/email.py
  found: Dev mode only triggers when email_service_api_key is falsy (empty, None, etc.)
  implication: With "dev-api-key" set, code attempts Mailgun API call on lines 42-100

- timestamp: 2026-02-04T00:07:00Z
  checked: /Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/backend/app/config.py
  found: email_service_api_key defaults to "" (empty string) but can be set from .env
  implication: If .env has any value (even fake), it's treated as production mode

- timestamp: 2026-02-04T00:08:00Z
  checked: /Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/backend/app/routers/auth.py
  found: forgot_password endpoint calls send_password_reset_email at line 213
  implication: Email service is correctly invoked, but returns bool that's not checked

- timestamp: 2026-02-04T00:10:00Z
  checked: Logic flow in email.py send_password_reset_email
  found: Line 32 checks "if not settings.email_service_api_key" - Python falsy check
  implication: Only empty string, None, or False trigger dev mode. "dev-api-key" is truthy.

- timestamp: 2026-02-04T00:11:00Z
  checked: .env.example template
  found: Shows placeholder "your-email-api-key" for EMAIL_SERVICE_API_KEY
  implication: Template doesn't indicate that empty/missing enables dev mode

- timestamp: 2026-02-04T00:12:00Z
  checked: Phase 1 verification document line 45
  found: "send_password_reset_email with Mailgun integration, dev mode fallback to console logging"
  implication: Dev mode feature was verified but not tested during verification

## Resolution

root_cause: |
  Dev mode console logging is not activating because EMAIL_SERVICE_API_KEY is set to "dev-api-key" in .env file.

  The email service (backend/app/services/email.py:32) uses a falsy check to determine dev mode:
  `if not settings.email_service_api_key:`

  With "dev-api-key" set in .env, this evaluates to False (the string is truthy), so the code attempts
  to send email via Mailgun API (lines 42-100) using the fake API key, which fails.

  To enable dev mode console logging, EMAIL_SERVICE_API_KEY must be:
  - Removed from .env entirely, OR
  - Set to empty string: EMAIL_SERVICE_API_KEY=
  - Commented out: # EMAIL_SERVICE_API_KEY=dev-api-key

fix: Not applied (diagnosis-only mode)
verification: Not applicable (diagnosis-only mode)
files_changed: []
