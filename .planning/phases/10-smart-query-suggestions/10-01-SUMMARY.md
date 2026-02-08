---
phase: 10-smart-query-suggestions
plan: 01
subsystem: api, agents, database
tags: [langchain, llm, json-parsing, alembic, suggestions, streaming]

# Dependency graph
requires:
  - phase: 09-manager-agent-with-intelligent-query-routing
    provides: "Manager Agent routing, ChatAgentState, agent pipeline"
  - phase: 07-multi-llm-provider-infrastructure
    provides: "Per-agent LLM config, YAML prompts, get_llm factory"
provides:
  - "query_suggestions JSON column on files table"
  - "OnboardingResult.query_suggestions from single LLM call"
  - "GET /files/{id}/summary returns query_suggestions and suggestion_auto_send"
  - "Data Analysis Agent follow_up_suggestions in state and stream events"
  - "follow_up_suggestions persisted in chat_messages.metadata_json"
affects: [10-02-PLAN, frontend-suggestions-ui, data-card-follow-ups]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "JSON-structured LLM responses with graceful fallback on parse failure"
    - "Single LLM call producing multiple outputs (summary + suggestions)"

key-files:
  created:
    - backend/alembic/versions/a0f950162812_add_query_suggestions_to_files.py
  modified:
    - backend/app/models/file.py
    - backend/app/schemas/file.py
    - backend/app/agents/onboarding.py
    - backend/app/agents/data_analysis.py
    - backend/app/agents/state.py
    - backend/app/services/agent_service.py
    - backend/app/config/prompts.yaml
    - backend/app/config.py
    - backend/app/routers/files.py

key-decisions:
  - "JSON-structured LLM output with fallback: both onboarding and data_analysis prompts request JSON, with json.JSONDecodeError fallback preserving original text"
  - "Single LLM call for summary + suggestions: no separate API call, onboarding prompt extended to produce both in one response"
  - "Suggestion categories are LLM-decided per dataset, not fixed templates (per CONTEXT.md override of REQUIREMENTS.md)"
  - "follow_up_suggestions as list[str] in ChatAgentState: simple array, not categorized like initial suggestions"
  - "MEMORY_SUFFICIENT mode returns empty follow_up_suggestions (no follow-ups for memory-only responses)"

patterns-established:
  - "JSON LLM response parsing: try json.loads() -> extract fields -> except JSONDecodeError -> fallback to raw content"
  - "Extending agent output via prompt restructuring: wrap existing prompt in JSON schema request, parse structured response"

# Metrics
duration: 4min
completed: 2026-02-08
---

# Phase 10 Plan 01: Backend Query Suggestions Infrastructure Summary

**LLM-generated query suggestions via JSON-structured onboarding and data_analysis prompts with database persistence and stream event wiring**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-08T21:01:20Z
- **Completed:** 2026-02-08T21:05:31Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- Onboarding Agent generates categorized query suggestions alongside data summary in a single LLM call
- Data Analysis Agent returns 2-3 follow-up suggestions with each analysis result
- Both agents use JSON-structured prompts with graceful fallback for non-JSON responses
- All suggestion data flows through API responses and stream events to frontend
- All 99 existing tests pass with zero regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Database migration, model, schema, onboarding prompt, and agent_service** - `d20193a` (feat)
2. **Task 2: Data Analysis Agent follow-up suggestions and stream event wiring** - `2bfef2b` (feat)

## Files Created/Modified
- `backend/alembic/versions/a0f950162812_add_query_suggestions_to_files.py` - Alembic migration adding query_suggestions JSON column
- `backend/app/models/file.py` - File model with query_suggestions mapped column
- `backend/app/schemas/file.py` - FileDetailResponse with query_suggestions field
- `backend/app/agents/onboarding.py` - Extended OnboardingResult, JSON parsing in generate_summary() with fallback
- `backend/app/agents/data_analysis.py` - JSON parsing for follow_up_suggestions in standard mode, empty list in memory mode
- `backend/app/agents/state.py` - ChatAgentState with follow_up_suggestions field
- `backend/app/services/agent_service.py` - Saves query_suggestions in onboarding, follow_up_suggestions in stream allowlist and metadata
- `backend/app/config/prompts.yaml` - Extended onboarding and data_analysis prompts for JSON output with suggestions
- `backend/app/config.py` - Added suggestion_auto_send setting (default: True)
- `backend/app/routers/files.py` - FileSummaryResponse with query_suggestions and suggestion_auto_send

## Decisions Made
- JSON-structured LLM output with graceful fallback: both agents request JSON, fall back to raw text on parse failure
- Single LLM call for summary + suggestions in onboarding (no additional API call overhead)
- LLM-decided categories per dataset (not fixed General/Benchmarking/Trend per CONTEXT.md)
- follow_up_suggestions is a flat list[str] (not categorized) since Data Cards show only 2-3 items
- MEMORY_SUFFICIENT mode skips follow-up suggestions entirely (no code execution context to suggest next steps from)
- Cleaned autogenerated migration to only include query_suggestions column (excluded LangGraph checkpoint table operations detected by Alembic)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Cleaned Alembic autogenerate migration**
- **Found during:** Task 1 (Database migration)
- **Issue:** Alembic autogenerate detected LangGraph checkpoint tables (managed by AsyncPostgresSaver) and added DROP TABLE operations to the migration
- **Fix:** Manually cleaned migration to only include the query_suggestions column addition, removing all checkpoint table operations
- **Files modified:** backend/alembic/versions/a0f950162812_add_query_suggestions_to_files.py
- **Verification:** Migration applies and rolls back cleanly
- **Committed in:** d20193a (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Essential fix to prevent accidental destruction of LangGraph checkpoint tables. No scope creep.

## Issues Encountered
None beyond the migration cleanup noted above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Backend infrastructure complete: query_suggestions stored in DB, served via API, streamed to frontend
- Follow-up suggestions flow through stream events and persist in chat metadata
- Ready for Plan 02: Frontend UI for displaying suggestion chips and handling click interactions

## Self-Check: PASSED

- All 11 key files verified present on disk
- Commit d20193a (Task 1) verified in git log
- Commit 2bfef2b (Task 2) verified in git log
- Migration applies and rolls back cleanly
- All 99 tests pass with zero regressions

---
*Phase: 10-smart-query-suggestions*
*Completed: 2026-02-08*
