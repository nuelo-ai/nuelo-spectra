---
phase: 49-pulse-agent
plan: 01
subsystem: agents
tags: [pulse, pydantic, yaml, alembic, e2b, profiling, sandbox]

requires:
  - phase: 47-pulse-models
    provides: PulseRun, Signal, Collection, Report models and migration

provides:
  - PULSE_SANDBOX_TIMEOUT_SECONDS=300 config setting
  - pulse_config.yaml with externalized detection thresholds
  - PulseAgentOutput/SignalOutput/SignalEvidence Pydantic schemas
  - deep_profile JSON column on files table
  - user_context Text column on pulse_runs table
  - pulse_agent entry in prompts.yaml
  - PROFILING_SCRIPT deterministic profiler for E2B sandbox
  - profile_files_in_sandbox async wrapper with cache support
  - load_pulse_config cached YAML loader

affects: [49-02-pulse-pipeline, pulse-agent-service]

tech-stack:
  added: []
  patterns:
    - "Externalized YAML config for tunable thresholds (pulse_config.yaml)"
    - "Deep profiling cache on File.deep_profile to avoid re-profiling"
    - "Async E2B wrapper with asyncio.to_thread for synchronous SDK calls"

key-files:
  created:
    - backend/app/config/pulse_config.yaml
    - backend/app/schemas/pulse.py
    - backend/app/agents/pulse_profiler.py
    - backend/alembic/versions/d3b8cf781e1e_add_deep_profile_and_user_context.py
    - backend/tests/test_pulse_agent.py
  modified:
    - backend/app/config.py
    - backend/app/config/prompts.yaml
    - backend/app/models/file.py
    - backend/app/models/pulse_run.py

key-decisions:
  - "Externalized severity thresholds to YAML for post-launch tuning without code changes"
  - "deep_profile cached on File model to avoid redundant E2B sandbox executions"

patterns-established:
  - "pulse_config.yaml: YAML-based config for detection parameters, loaded with @lru_cache"
  - "profile_files_in_sandbox: cache-first pattern — skip E2B if File.deep_profile is not None"

requirements-completed: [PULSE-02, PULSE-03]

duration: 4min
completed: 2026-03-07
---

# Phase 49 Plan 01: Pulse Agent Foundation Summary

**Pulse config, Pydantic schemas, Alembic migration (deep_profile + user_context), deterministic E2B profiling script with cache support**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-07T02:35:26Z
- **Completed:** 2026-03-07T02:39:00Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- PULSE_SANDBOX_TIMEOUT_SECONDS=300 added to Settings, separate from chat sandbox's 60s
- PulseAgentOutput/SignalOutput/SignalEvidence Pydantic v2 schemas with Literal validation for severity and chartType
- pulse_config.yaml with externalized z-score, p-value, correlation thresholds
- deep_profile JSON column on files table and user_context Text column on pulse_runs table (Alembic migration applied)
- Comprehensive PROFILING_SCRIPT for E2B: per-column stats, correlations, missing patterns, outlier detection
- profile_files_in_sandbox with deep_profile cache-first pattern
- All 11 unit tests green

## Task Commits

Each task was committed atomically:

1. **Task 1: Config, schemas, migration, and prompts.yaml entry**
   - `19ad769` (test: failing tests for config, schemas, prompts)
   - `51b0022` (feat: pulse config, schemas, migration, prompts entry)
2. **Task 2: Deterministic deep profiling script and E2B wrapper**
   - `14d73aa` (test: failing tests for profiling script and E2B wrapper)
   - `751a725` (feat: profiling script and E2B wrapper)

_TDD tasks have RED (test) + GREEN (feat) commits._

## Files Created/Modified
- `backend/app/config.py` - Added pulse_sandbox_timeout_seconds=300
- `backend/app/config/pulse_config.yaml` - Externalized detection thresholds
- `backend/app/config/prompts.yaml` - Added pulse_agent entry
- `backend/app/schemas/pulse.py` - PulseAgentOutput, SignalOutput, SignalEvidence, PulseRunCreate, PulseRunResponse schemas
- `backend/app/models/file.py` - Added deep_profile JSON column
- `backend/app/models/pulse_run.py` - Added user_context Text column
- `backend/alembic/versions/d3b8cf781e1e_add_deep_profile_and_user_context.py` - Migration for new columns
- `backend/app/agents/pulse_profiler.py` - PROFILING_SCRIPT, profile_files_in_sandbox, load_pulse_config
- `backend/tests/test_pulse_agent.py` - 11 unit tests

## Decisions Made
- Externalized severity thresholds to YAML (pulse_config.yaml) for post-launch tuning without code changes
- deep_profile cached on File model to avoid redundant E2B sandbox executions
- Used asyncio.to_thread for synchronous E2B SDK calls in async wrapper

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All contracts (schemas, config, DB columns) ready for Plan 02 (LangGraph pipeline)
- PROFILING_SCRIPT ready for E2B execution in pipeline
- pulse_agent prompts entry ready for LLM reasoning node

---
*Phase: 49-pulse-agent*
*Completed: 2026-03-07*
