---
phase: 07-multi-llm-provider-infrastructure
plan: 03
subsystem: infra
tags: [llm, validation, health-check, logging, error-handling, fail-fast, httpx]

# Dependency graph
requires:
  - phase: 07-multi-llm-provider-infrastructure
    plan: 01
    provides: Provider registry and LLM factory for multi-provider support
provides:
  - Fail-fast startup validation refusing to start on invalid LLM config or unreachable providers
  - Structured LLM call logging (JSON metadata, no full prompts/responses)
  - /health/llm endpoint testing active providers with lightweight calls (60-second cache)
  - Error classification distinguishing 5 failure types (network/auth/rate_limit/model_not_found/provider)
  - User-friendly error messages with actionable hints for temporary vs permanent failures
affects: [phase-08, phase-09, phase-10, all-agent-execution]

# Tech tracking
tech-stack:
  added: []
  patterns: [fail-fast validation, structured logging, health checks, error classification]

key-files:
  created: []
  modified:
    - backend/app/main.py
    - backend/app/routers/health.py
    - backend/app/agents/llm_factory.py

key-decisions:
  - "Fail-fast at startup with connectivity tests for all active providers (not just config validation)"
  - "5-second timeout per provider connectivity test to prevent hanging on unreachable providers"
  - "60-second cache for health check results to avoid quota consumption on frequent polling"
  - "Structured JSON logging for LLM calls (metadata only, not full content - LangSmith handles that)"

patterns-established:
  - "Startup validation pattern: config validation → collect active providers → test connectivity with lightweight calls"
  - "Error classification pattern: distinguish temporary (retry) vs permanent (fix config) failures"
  - "Health check pattern: cached results, lightweight calls (model listing not inference), per-provider status"

# Metrics
duration: 2min
completed: 2026-02-07
---

# Phase 7 Plan 3: Provider Validation & Observability Summary

**Fail-fast LLM startup validation with structured logging, 5-category error classification, and cached /health/llm endpoint**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-07T19:19:32Z
- **Completed:** 2026-02-07T19:21:45Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Backend refuses to start if any agent-configured provider is unreachable or has invalid credentials
- Startup validation displays clear error messages identifying which agent, which provider, and what went wrong
- GET /health/llm returns status of each configured provider without consuming inference quota (60-second cache)
- LLM calls logged with metadata (provider, model, agent, latency, status) but not full prompts/responses
- Error messages distinguish temporary failures (network, rate limit) from permanent failures (invalid key, wrong model)

## Task Commits

Each task was committed atomically:

1. **Task 1: Fail-fast startup validation and error classification** - `eb24c10` (feat)
2. **Task 2: Structured LLM logging and /health/llm endpoint** - `6657432` (feat)

## Files Created/Modified

### Modified

- `backend/app/main.py` - Added validate_llm_configuration() in lifespan with two-phase validation (config + connectivity)
- `backend/app/routers/health.py` - Added /health/llm endpoint testing active providers with lightweight calls and 60-second cache
- `backend/app/agents/llm_factory.py` - Added invoke_with_logging() and classify_llm_error() for structured LLM call logging

## Decisions Made

**Validation Strategy:**
- Fail-fast at startup (not on first agent run) per user decision CONFIG-04
- Test connectivity for all active providers (not just config validation) to catch invalid credentials before accepting requests
- 5-second timeout per provider to prevent hanging on unreachable providers
- Lazy imports inside lifespan function to avoid circular import issues (per Research pitfall #3)

**Error Classification:**
- 5 categories: network_error, auth_error, rate_limit, model_not_found, provider_error
- User-facing messages with actionable hints (e.g., "Check your ANTHROPIC_API_KEY setting or get a new key from...")
- Technical logging with full diagnostic details for engineer debugging

**Observability:**
- Health check endpoint uses same lightweight calls as startup validation (model listing, not inference)
- 60-second cache to avoid quota consumption on frequent polling
- Structured JSON logging for LLM call metadata only (LangSmith handles full request/response tracing)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - plan executed smoothly.

## User Setup Required

None - no external service configuration required for this plan. Validation uses existing provider API keys configured via environment variables (ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.).

## Next Phase Readiness

**Ready for:**
- Phase 8 (Session Memory): LLM infrastructure stable with observability and error handling
- Phase 9 (Query Suggestions): Can rely on fail-fast validation and structured logging
- Phase 10 (Web Search): LLM infrastructure mature with health checks and error classification

**Validation Complete:**
- Startup validation catches misconfigurations before system accepts requests
- Health check endpoint provides diagnostics for monitoring and CI/CD
- Structured logging enables LLM call tracking and debugging
- Error classification guides users toward correct resolution (retry vs fix config)

**No Blockers:**
- All validation tests passed
- Backend starts successfully with valid config
- Health endpoint returns provider status
- LLM call logging captures metadata correctly
- Error classification correctly identifies 5 failure types

## Self-Check: PASSED

All claimed files and commits verified:
- backend/app/main.py modified (validate_llm_configuration in lifespan)
- backend/app/routers/health.py modified (/health/llm endpoint)
- backend/app/agents/llm_factory.py modified (invoke_with_logging, classify_llm_error)
- Commit eb24c10 (Task 1) exists
- Commit 6657432 (Task 2) exists

Verification tests:
- validate_llm_configuration() function exists and executes
- Error classification correctly identifies network/auth/rate_limit/model_not_found/provider errors
- /health/llm endpoint exists in router
- Structured JSON logging present in llm_factory.py
- User-friendly error messages with actionable hints

---
*Phase: 07-multi-llm-provider-infrastructure*
*Completed: 2026-02-07*
