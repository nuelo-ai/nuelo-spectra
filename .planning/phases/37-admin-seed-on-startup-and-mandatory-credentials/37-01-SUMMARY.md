---
phase: 37-admin-seed-on-startup-and-mandatory-credentials
plan: 01
subsystem: infra
tags: [pydantic, model_validator, docker, entrypoint, admin-seed, config]

# Dependency graph
requires:
  - phase: 36-dokploy-deployment
    provides: docker-entrypoint.sh and backend deployment infrastructure
  - phase: 34-docker-build
    provides: /app/.venv/bin/python entrypoint pattern and CLI seed-admin command
provides:
  - Pydantic model_validator that rejects missing admin credentials for dev/admin modes at startup
  - Conditional docker-entrypoint.sh seed block that runs seed-admin after migrations before uvicorn
  - Updated .env.docker.example documentation marking admin credentials as required for dev/admin
affects: [future backend deploys, Dokploy deployments, local Docker compose runs]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Fail-fast Pydantic validation: model_validator(mode='after') on Settings class for environment-specific requirements"
    - "Conditional docker-entrypoint seed: [ -n \"${ADMIN_EMAIL:-}\" ] gates seed-admin call between migrations and uvicorn"

key-files:
  created: []
  modified:
    - backend/app/config.py
    - backend/docker-entrypoint.sh
    - .env.docker.example

key-decisions:
  - "Raise ValueError (not SystemExit) in model_validator — Pydantic v2 wraps it in ValidationError which propagates at lru_cache construction"
  - "Keep admin_email/admin_password defaults as empty string — validator provides the explicit error; Pydantic field required= would break public mode"
  - "Use [ -n \"${ADMIN_EMAIL:-}\" ] with dash-empty fallback — handles both unset and empty string correctly under set -euo pipefail"
  - "Seed block placed after alembic upgrade head, before exec uvicorn — schema must exist before seed, admin must exist before first request"
  - "Comment-only update to .env.docker.example — ADMIN_EMAIL= and ADMIN_PASSWORD= values stay empty (template for operators to fill)"

patterns-established:
  - "Environment validation pattern: Use model_validator(mode='after') in Settings for mode-specific required fields"
  - "Entrypoint ordering: wait-for-db -> migrations -> conditional-seed -> exec uvicorn"

requirements-completed: [SEED-01, SEED-02, SEED-03]

# Metrics
duration: 2min
completed: 2026-02-21
---

# Phase 37 Plan 01: Admin Seed on Startup and Mandatory Credentials Summary

**Pydantic model_validator that fails-fast when admin credentials are missing in dev/admin modes, plus conditional docker-entrypoint.sh seed block that runs seed-admin after migrations before uvicorn starts**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-02-21T15:02:00Z
- **Completed:** 2026-02-21T15:03:46Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Added `model_validator(mode="after")` to Settings that fires at lru_cache construction, raising ValueError with named missing vars when SPECTRA_MODE is dev or admin
- Inserted conditional seed block in docker-entrypoint.sh between `alembic upgrade head` and `exec uvicorn`, gated on `[ -n "${ADMIN_EMAIL:-}" ]`
- Updated .env.docker.example to accurately document ADMIN_EMAIL/ADMIN_PASSWORD as REQUIRED for dev/admin modes, with auto-seed behavior and password-reset-on-restart warning

## Task Commits

Each task was committed atomically:

1. **Task 1: Add model_validator to Settings for fail-fast startup validation** - `42a1e84` (feat)
2. **Task 2: Add conditional admin seed block to docker-entrypoint.sh** - `f1d3655` (feat)
3. **Task 3: Update .env.docker.example admin credentials comment** - `22c5ee1` (docs)

## Files Created/Modified

- `backend/app/config.py` - Added `from pydantic import model_validator` import and `validate_admin_credentials_for_admin_modes()` method to Settings class
- `backend/docker-entrypoint.sh` - Inserted 9-line conditional seed block after migrations, before uvicorn exec
- `.env.docker.example` - Replaced 1-line optional comment with 5-line REQUIRED comment block including auto-seed explanation and password-reset warning

## Decisions Made

- **ValueError not SystemExit in validator:** Pydantic v2 validators must raise ValueError; Pydantic wraps it in ValidationError which propagates at module import time via lru_cache construction — no need for explicit sys.exit()
- **Empty string defaults preserved:** `admin_email: str = ""` and `admin_password: str = ""` intentionally kept — making them required= fields would break public mode; the validator handles the explicit error message
- **`${ADMIN_EMAIL:-}` dash-empty fallback:** Essential under `set -euo pipefail` — without it, referencing an unset var would abort the script before reaching the conditional check
- **Seed block ordering enforced by placement:** alembic (schema) must complete before seed (inserts rows); seed must complete before uvicorn (serves requests) — placement in entrypoint script enforces this naturally

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Verification test 2 (the final suite) initially appeared to fail because the backend `.env` file has real ADMIN_EMAIL/ADMIN_PASSWORD set — running `SPECTRA_MODE=dev` without explicitly overriding those vars to empty picks them up and the validator correctly passes. The plan's own Test 1 (which explicitly sets `ADMIN_EMAIL=""`) works correctly. Not a bug in the implementation — the validator works as intended.

## User Setup Required

None - no external service configuration required. Operators must set ADMIN_EMAIL and ADMIN_PASSWORD in their .env.docker file when using SPECTRA_MODE=dev or SPECTRA_MODE=admin.

## Next Phase Readiness

- Backend startup is now self-documenting: missing admin credentials cause immediate process exit with a clear error message naming the missing variables
- Docker container deployments automatically seed the admin user after migrations
- No further work needed for this phase — all three artifacts complete and verified

---
*Phase: 37-admin-seed-on-startup-and-mandatory-credentials*
*Completed: 2026-02-21*
