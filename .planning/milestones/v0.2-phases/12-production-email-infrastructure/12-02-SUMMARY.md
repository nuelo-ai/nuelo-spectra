---
phase: 12-production-email-infrastructure
plan: 02
subsystem: auth
tags: [password-reset, db-tokens, cooldown, smtp-validation, anti-enumeration, sha256]

# Dependency graph
requires:
  - phase: 12-production-email-infrastructure
    provides: SMTP email service, PasswordResetToken model, create_reset_token(), send_password_reset_email(), validate_smtp_connection()
  - phase: 01-foundation
    provides: Auth router, security.py JWT helpers, User model
provides:
  - DB-backed single-use password reset tokens replacing JWT tokens
  - 2-minute per-email cooldown on forgot-password requests
  - Previous token invalidation on new reset request
  - SMTP startup validation in app lifespan
  - Frontend expired/invalid token error page with "Request new reset" button
affects: [auth-endpoints, password-reset-flow, app-startup]

# Tech tracking
tech-stack:
  added: []
  patterns: [DB-backed single-use tokens with SHA-256 hash lookup, per-email in-memory cooldown, anti-enumeration (uniform 202 response), SMTP startup validation (non-blocking)]

key-files:
  created: []
  modified:
    - backend/app/routers/auth.py
    - backend/app/utils/security.py
    - backend/app/main.py
    - frontend/src/app/(auth)/reset-password/page.tsx

key-decisions:
  - "DB-backed tokens replace JWT for password reset (single-use, invalidatable, auditable)"
  - "In-memory dict cooldown (2 minutes per email) - simple, sufficient for single-process deployment"
  - "Generic error message for all token failures (expired, used, invalid) to prevent information leakage"
  - "SMTP validation non-blocking at startup - app starts regardless of SMTP status"
  - "Frontend error page with Request new reset button (not redirect to login, per locked decision)"

patterns-established:
  - "Token validation pattern: SHA-256 hash incoming token, look up in DB with is_active + is_used + expires_at checks"
  - "Anti-enumeration: forgot-password always returns 202, cooldown returns early without DB query"
  - "SMTP startup validation alongside LLM validation in lifespan"

# Metrics
duration: 2min
completed: 2026-02-09
---

# Phase 12 Plan 02: Wire Email into Auth Endpoints Summary

**DB-backed single-use password reset tokens with 2-minute cooldown, SMTP startup validation, and frontend expired-token error page**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-09T23:36:30Z
- **Completed:** 2026-02-09T23:38:59Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Replaced JWT password reset tokens with DB-backed single-use tokens (SHA-256 hash lookup)
- Added 2-minute per-email cooldown preventing reset spam without leaking email existence
- Previous tokens automatically invalidated when new reset requested for same email
- SMTP connection validated at startup alongside LLM validation (non-blocking)
- Frontend shows clear error state with red icon and "Request new reset" button for expired/invalid/missing tokens
- Removed JWT password reset functions from security.py (create_password_reset_token, verify_password_reset_token)

## Task Commits

Each task was committed atomically:

1. **Task 1: Rewrite auth endpoints with DB tokens, cooldown, and cleanup security.py** - `69bd982` (feat)
2. **Task 2: SMTP startup validation and frontend expired-token error page** - `b977658` (feat)

## Files Created/Modified
- `backend/app/routers/auth.py` - Rewritten forgot_password (DB tokens, cooldown, first_name) and reset_password (single-use DB tokens)
- `backend/app/utils/security.py` - Cleaned: removed JWT password reset functions, kept auth token functions
- `backend/app/main.py` - SMTP startup validation call in lifespan after LLM validation
- `frontend/src/app/(auth)/reset-password/page.tsx` - Error state for expired/invalid tokens with "Request new reset" button

## Decisions Made
- Used in-memory dict for cooldown tracking (sufficient for single-process, no DB overhead for rate limiting)
- Generic "Invalid or expired reset token" message for all failure modes (prevents information leakage)
- SMTP validation is non-blocking: logs status but doesn't prevent app startup
- Frontend shows error page with button (not toast + redirect) per locked decision from research phase
- Missing token on page load triggers error state immediately (better UX than showing empty form)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required. SMTP works in dev mode with console logging by default.

## Next Phase Readiness
- Phase 12 complete: full production email infrastructure operational
- Password reset flow: SMTP email -> DB token -> single-use validation -> password update
- Frontend handles all error states (expired, used, invalid, missing token)
- Ready for v0.2 milestone completion

## Self-Check: PASSED

All 4 modified files verified on disk. Both task commits (69bd982, b977658) verified in git log.

---
*Phase: 12-production-email-infrastructure*
*Completed: 2026-02-09*
