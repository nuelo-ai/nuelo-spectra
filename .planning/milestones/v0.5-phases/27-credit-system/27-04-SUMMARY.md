---
phase: 27-credit-system
plan: 04
subsystem: api
tags: [apscheduler, scheduler, credits, reset, cron, idempotent]

# Dependency graph
requires:
  - phase: 27-credit-system-01
    provides: "CreditService with execute_reset, is_reset_due; UserClassService with get_user_classes"
provides:
  - "APScheduler-based credit reset job running every 15 minutes"
  - "Env var gating (ENABLE_SCHEDULER) to prevent multi-instance double-runs"
  - "Idempotent reset with SELECT FOR UPDATE and double-check-after-lock pattern"
affects: []

# Tech tracking
tech-stack:
  added: ["APScheduler>=3.11.0,<4.0"]
  patterns: ["Env var gating for singleton scheduler", "Double-check-after-lock for idempotent scheduled jobs", "AsyncIOScheduler with IntervalTrigger"]

key-files:
  created:
    - backend/app/scheduler.py
  modified:
    - backend/pyproject.toml
    - backend/uv.lock
    - backend/app/main.py
    - backend/app/config.py

key-decisions:
  - "Used pyproject.toml (uv) instead of requirements.txt for dependency management (matches project structure)"
  - "next_run_time=None prevents immediate execution at startup, waits for first 15-min interval"
  - "Single commit at end of batch for efficiency rather than per-user commits"

patterns-established:
  - "Scheduler integration: conditional start/stop in FastAPI lifespan via settings flag"
  - "Background job pattern: own session via async_session_maker (not request-scoped)"

requirements-completed: [CREDIT-05, CREDIT-13]

# Metrics
duration: 2min
completed: 2026-02-16
---

# Phase 27 Plan 04: Scheduled Credit Reset Summary

**APScheduler credit reset job running every 15 minutes with SELECT FOR UPDATE double-check-after-lock for idempotent rolling per-user resets**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-16T19:27:34Z
- **Completed:** 2026-02-16T19:29:34Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Installed APScheduler 3.11.2 and created scheduler.py with 15-minute interval credit reset job
- Implemented idempotent reset processing with SELECT FOR UPDATE and double-check-after-lock pattern
- Integrated scheduler into FastAPI lifespan with conditional start/stop based on ENABLE_SCHEDULER env var
- Added enable_scheduler setting to pydantic Settings class

## Task Commits

Each task was committed atomically:

1. **Task 1: Install APScheduler and create scheduler module** - `b202708` (feat)
2. **Task 2: Integrate scheduler into FastAPI lifespan** - `9261a73` (feat)

## Files Created/Modified
- `backend/app/scheduler.py` - APScheduler setup with process_credit_resets job, is_scheduler_enabled check, double-check-after-lock pattern
- `backend/pyproject.toml` - Added APScheduler dependency
- `backend/uv.lock` - Updated lockfile with APScheduler and tzlocal
- `backend/app/main.py` - Scheduler start/stop in lifespan, conditional on settings.enable_scheduler
- `backend/app/config.py` - Added enable_scheduler: bool = False setting

## Decisions Made
- Adapted plan from requirements.txt to pyproject.toml/uv since that is the project's actual dependency management system
- next_run_time=None on the job means the scheduler waits a full 15-minute interval before first run (avoids unnecessary reset check on every restart)
- Scheduler uses its own database session via async_session_maker() since it runs outside HTTP request context
- Single db.commit() at end of full batch for efficiency (not per-user)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Adapted dependency management from requirements.txt to pyproject.toml**
- **Found during:** Task 1 (Install APScheduler)
- **Issue:** Plan specified adding to requirements.txt which does not exist; project uses pyproject.toml with uv
- **Fix:** Used `uv add` to install APScheduler and update pyproject.toml instead
- **Files modified:** backend/pyproject.toml, backend/uv.lock
- **Verification:** `uv run python -c "import apscheduler"` succeeds, pyproject.toml contains dependency
- **Committed in:** b202708 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Trivial adaptation to actual project tooling. No scope creep.

## Issues Encountered
None

## User Setup Required
None - scheduler is disabled by default. Set `ENABLE_SCHEDULER=true` in .env to activate.

## Next Phase Readiness
- All Phase 27 plans complete (01: core service, 02: API endpoints, 03: chat integration, 04: scheduler)
- Credit system fully operational with automatic rolling resets when ENABLE_SCHEDULER=true
- Ready for Phase 31 (credit UI) frontend integration

## Self-Check: PASSED

- FOUND: backend/app/scheduler.py
- FOUND: backend/app/config.py
- FOUND: backend/app/main.py
- FOUND: b202708 (Task 1 commit)
- FOUND: 9261a73 (Task 2 commit)

---
*Phase: 27-credit-system*
*Completed: 2026-02-16*
