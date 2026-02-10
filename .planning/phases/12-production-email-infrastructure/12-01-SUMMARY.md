---
phase: 12-production-email-infrastructure
plan: 01
subsystem: email
tags: [smtp, aiosmtplib, jinja2, email-templates, password-reset, sha256, sqlalchemy]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: SQLAlchemy Base model, Alembic migration setup, Settings/config pattern
provides:
  - PasswordResetToken SQLAlchemy model with SHA-256 hashed tokens
  - Async SMTP email service via aiosmtplib with dev-mode console fallback
  - Jinja2 HTML and plain text email templates for password reset
  - Token generation (secrets.token_urlsafe) and verification (constant-time comparison)
  - SMTP connection validation helper for startup health checks
  - SMTP config settings (smtp_host/port/user/pass/from_email/from_name)
affects: [12-02-PLAN, auth-endpoints, password-reset-flow]

# Tech tracking
tech-stack:
  added: [aiosmtplib, jinja2]
  patterns: [SMTP email with dev-mode fallback, SHA-256 token hashing, Jinja2 email templates with inline CSS, multipart MIME (text + HTML)]

key-files:
  created:
    - backend/app/models/password_reset.py
    - backend/app/templates/email/password_reset.html
    - backend/app/templates/email/password_reset.txt
    - backend/alembic/versions/9c47b2cc24f2_add_password_reset_tokens_table.py
  modified:
    - backend/app/config.py
    - backend/app/models/__init__.py
    - backend/alembic/env.py
    - backend/app/services/email.py
    - backend/pyproject.toml
    - backend/.env.example

key-decisions:
  - "aiosmtplib with start_tls=True for SMTP transport (replaces Mailgun HTTP API)"
  - "SHA-256 hashing of reset tokens with secrets.compare_digest for constant-time verification"
  - "Dev mode console logging when SMTP_HOST is empty (no config needed for local dev)"
  - "Inline CSS only in HTML template for maximum email client compatibility"

patterns-established:
  - "Email dev-mode fallback: is_smtp_configured() gate with console logging"
  - "Token pattern: secrets.token_urlsafe(32) raw + SHA-256 hash stored in DB"
  - "Jinja2 FileSystemLoader from backend/app/templates/email/ directory"

# Metrics
duration: 4min
completed: 2026-02-09
---

# Phase 12 Plan 01: SMTP Email Infrastructure Summary

**Async SMTP email service via aiosmtplib with Jinja2 templates, database-backed PasswordResetToken model, and SHA-256 token hashing**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-09T23:30:03Z
- **Completed:** 2026-02-09T23:33:54Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- SMTP email infrastructure replacing Mailgun HTTP API with aiosmtplib async sending
- PasswordResetToken model with SHA-256 hashed tokens, composite index, and Alembic migration
- Professional HTML email template with Spectra branding, styled reset button, and inline CSS
- Plain text email fallback for maximum compatibility
- Dev-mode console logging when SMTP not configured (zero-config local development)
- Cryptographically secure token generation with constant-time hash verification

## Task Commits

Each task was committed atomically:

1. **Task 1: SMTP config, PasswordResetToken model, migration, and dependency** - `8fb1062` (feat)
2. **Task 2: Email service rewrite and Jinja2 templates** - `e20d21a` (feat)

## Files Created/Modified
- `backend/app/models/password_reset.py` - PasswordResetToken SQLAlchemy model (token_hash, is_used, is_active, expires_at)
- `backend/app/services/email.py` - Full rewrite: aiosmtplib SMTP sending, Jinja2 templates, token helpers, SMTP validation
- `backend/app/templates/email/password_reset.html` - Professional HTML email with Spectra branding, styled reset button
- `backend/app/templates/email/password_reset.txt` - Plain text email fallback
- `backend/alembic/versions/9c47b2cc24f2_add_password_reset_tokens_table.py` - Migration creating password_reset_tokens table
- `backend/app/config.py` - Replaced email_service_api_key/email_from with SMTP settings
- `backend/app/models/__init__.py` - Added PasswordResetToken import and __all__ entry
- `backend/alembic/env.py` - Added password_reset model import for autogenerate
- `backend/pyproject.toml` - Added aiosmtplib>=3.0.0 and jinja2>=3.1.0 dependencies
- `backend/.env.example` - Replaced email config section with SMTP settings and provider examples

## Decisions Made
- Used aiosmtplib with start_tls=True for SMTP transport (standard, provider-agnostic)
- SHA-256 hashing of reset tokens stored in DB; raw token sent via email only
- secrets.compare_digest for constant-time hash comparison (prevents timing attacks)
- Dev mode auto-detected when SMTP_HOST is empty (no manual flag needed)
- Inline CSS only in HTML email (no style block) for maximum email client compatibility
- 10-minute token expiry hardcoded (will be configurable in future if needed)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated .env file to match new SMTP config**
- **Found during:** Task 1 (Migration generation)
- **Issue:** Alembic migration failed because `.env` still contained old `EMAIL_FROM` setting which is now an extra/forbidden field in pydantic Settings after removing `email_from`
- **Fix:** Replaced `EMAIL_SERVICE_API_KEY` and `EMAIL_FROM` in `.env` with new SMTP settings
- **Files modified:** backend/.env
- **Verification:** `uv run alembic revision --autogenerate` succeeded
- **Committed in:** 8fb1062 (part of Task 1 commit, .env not committed as it contains secrets)

**2. [Rule 3 - Blocking] Cleaned migration to exclude LangGraph checkpoint tables**
- **Found during:** Task 1 (Migration generation)
- **Issue:** Alembic autogenerate detected LangGraph checkpoint tables (managed externally) and added DROP TABLE operations
- **Fix:** Removed all checkpoint_blobs/checkpoints/checkpoint_writes/checkpoint_migrations operations from migration
- **Files modified:** backend/alembic/versions/9c47b2cc24f2_add_password_reset_tokens_table.py
- **Verification:** Migration applies cleanly, only creates password_reset_tokens table
- **Committed in:** 8fb1062 (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both auto-fixes necessary for correct migration generation. No scope creep.

## Issues Encountered
None beyond the auto-fixed blocking issues documented above.

## User Setup Required
None - no external service configuration required. SMTP works in dev mode with console logging by default.

## Next Phase Readiness
- Email infrastructure complete, ready for Plan 02 to wire into auth endpoints
- PasswordResetToken model provides: create_reset_token(), verify_token_hash(), is_used/is_active flags
- Email service provides: send_password_reset_email() with first_name personalization
- validate_smtp_connection() ready for Plan 02 to call during app startup

## Self-Check: PASSED

All 5 created files verified on disk. Both task commits (8fb1062, e20d21a) verified in git log.

---
*Phase: 12-production-email-infrastructure*
*Completed: 2026-02-09*
