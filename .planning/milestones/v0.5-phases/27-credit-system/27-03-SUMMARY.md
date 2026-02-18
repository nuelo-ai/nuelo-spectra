---
phase: 27-credit-system
plan: 03
subsystem: api
tags: [credits, chat, deduction, registration, fastapi, decimal]

# Dependency graph
requires:
  - phase: 27-credit-system-01
    provides: "CreditService with atomic deduction, UserClassService with get_class_config/get_default_class"
provides:
  - "Credit deduction gate on all 4 chat query endpoints (file/session, stream/non-stream)"
  - "UserCredit row creation during user registration with tier-based initial balance"
affects: [27-04, 31-credit-ui]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Pre-send credit gate pattern: deduct + commit before agent execution", "Registration-time credit initialization from YAML tier config"]

key-files:
  created: []
  modified:
    - backend/app/routers/chat.py
    - backend/app/services/auth.py

key-decisions:
  - "Shared _deduct_credits_or_raise helper for all 4 query endpoints (DRY)"
  - "Credit deduction applied to session-based endpoints too (not just file-based)"
  - "db.flush() before UserCredit creation to get user.id for FK"

patterns-established:
  - "Pre-send gate: deduct credit, commit, then run agent -- deduction independent of agent success"
  - "HTTP 402 with structured detail (error, message, balance, next_reset) for insufficient credits"

requirements-completed: [CREDIT-03, CREDIT-04]

# Metrics
duration: 4min
completed: 2026-02-16
---

# Phase 27 Plan 03: Chat Integration Summary

**Credit deduction gate on all chat query endpoints with HTTP 402 blocking, plus UserCredit initialization on user registration from YAML tier config**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-16T19:27:39Z
- **Completed:** 2026-02-16T19:31:38Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Added credit deduction before agent execution in all 4 chat endpoints (file query, file stream, session query, session stream)
- HTTP 402 with structured error detail (error, message, balance, next_reset) when credits insufficient
- Credit deduction committed independently before agent runs (no refund on agent failure)
- New user registration creates UserCredit row with balance from tier config (free tier gets credit allocation, unlimited gets sentinel -1)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add credit deduction gate to chat query endpoints** - `175efaa` (feat)
2. **Task 2: Create UserCredit row during user registration** - `f73a671` (feat)

## Files Created/Modified
- `backend/app/routers/chat.py` - Added CreditService import, _deduct_credits_or_raise helper, credit gate in all 4 query endpoints
- `backend/app/services/auth.py` - Added UserCredit/UserClassService imports, credit row creation in create_user with tier-based initial balance

## Decisions Made
- Created shared `_deduct_credits_or_raise` helper function instead of duplicating deduction logic in each endpoint
- Applied credit deduction to session-based endpoints (sessions/{session_id}/query and stream) in addition to file-based endpoints -- consistent billing regardless of query mode
- Used `db.flush()` before UserCredit creation in registration to ensure user.id is available for the foreign key

## Deviations from Plan

None - plan executed exactly as written. Session-based endpoints were not explicitly mentioned in the plan but were naturally included as they are the same query flow.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Credit system is now functional end-to-end: deduction on chat, initialization on signup
- Plan 04 (scheduler) will add automatic credit resets via APScheduler
- Frontend credit display (Phase 31) can use the public /api/credits/balance endpoint from Plan 02

## Self-Check: PASSED

- FOUND: backend/app/routers/chat.py
- FOUND: backend/app/services/auth.py
- FOUND: 175efaa (Task 1 commit)
- FOUND: f73a671 (Task 2 commit)

---
*Phase: 27-credit-system*
*Completed: 2026-02-16*
