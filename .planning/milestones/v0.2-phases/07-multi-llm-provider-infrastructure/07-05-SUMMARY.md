---
phase: 07-multi-llm-provider-infrastructure
plan: 05
subsystem: api
tags: [openai, reasoning-models, llm-validation, error-handling, langchain]

# Dependency graph
requires:
  - phase: 07-multi-llm-provider-infrastructure (plans 01-04)
    provides: LLM factory, per-agent config, provider registry, test infrastructure
provides:
  - EmptyLLMResponseError exception and validate_llm_response() helper in llm_factory.py
  - Empty content validation at all 5 LLM invocation sites across agents
  - Reasoning model auto-detection with reasoning_effort=low for OpenAI o-series and gpt-5-nano/mini
  - 11 new tests covering empty response validation and reasoning model config
affects: [all agents, UAT, data-analysis, coding, onboarding, code-checker]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Centralized LLM response validation via validate_llm_response() helper"
    - "Reasoning model auto-detection with configurable reasoning_effort"
    - "User-friendly error messages on empty LLM responses (no silent empty strings)"

key-files:
  created: []
  modified:
    - backend/app/agents/llm_factory.py
    - backend/app/agents/onboarding.py
    - backend/app/agents/coding.py
    - backend/app/agents/data_analysis.py
    - backend/app/agents/graph.py
    - backend/tests/test_llm_providers.py

key-decisions:
  - "Centralized validate_llm_response in llm_factory.py for import from all agents"
  - "reasoning_effort=low as default for reasoning models (o1, o3, o4-mini, gpt-5-nano, gpt-5-mini)"
  - "Empty response in coding_agent returns empty code to trigger retry via code_checker"
  - "Empty response in da_with_tools_node skipped when tool_calls are present (normal for tool-calling mode)"

patterns-established:
  - "validate_llm_response pattern: all LLM invocation sites must call validate_llm_response before using response content"
  - "Reasoning model detection pattern: model name prefix matching against known reasoning model families"

# Metrics
duration: 3min
completed: 2026-02-09
---

# Phase 7 Plan 5: Empty Response Validation and Reasoning Model Config Summary

**Centralized LLM empty response validation with EmptyLLMResponseError, reasoning_effort auto-config for OpenAI reasoning models, and 11 new tests closing UAT Test 2 gap**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-10T03:04:32Z
- **Completed:** 2026-02-10T03:07:52Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments
- Added validate_llm_response() helper and EmptyLLMResponseError to llm_factory.py for centralized empty content validation
- All 5 LLM invocation sites now validate for empty content with user-friendly error messages (zero silent empty-string storage)
- OpenAI reasoning models (o1, o3, o4-mini, gpt-5-nano, gpt-5-mini) automatically receive reasoning_effort=low to prevent token budget exhaustion
- 11 new tests: 5 for empty response validation, 6 for reasoning model config. 106 total tests pass with zero regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Add empty response validation and reasoning model config to llm_factory** - `8b7dc42` (feat)
2. **Task 2: Add empty content validation to all agent LLM invocation sites** - `69b6a81` (feat)
3. **Task 3: Add tests for empty response validation and reasoning model config** - `e99290f` (test)

## Files Created/Modified
- `backend/app/agents/llm_factory.py` - Added EmptyLLMResponseError, validate_llm_response(), reasoning model detection in get_llm()
- `backend/app/agents/onboarding.py` - validate_llm_response in generate_summary(), returns error message on empty
- `backend/app/agents/coding.py` - validate_llm_response in coding_agent(), returns empty code on empty (triggers retry)
- `backend/app/agents/data_analysis.py` - validate in da_with_tools_node() and _generate_analysis_with_search()
- `backend/app/agents/graph.py` - validate in code_checker_node(), routes to retry/halt on empty response
- `backend/tests/test_llm_providers.py` - 11 new tests (TestEmptyResponseValidation + TestReasoningModelConfig)

## Decisions Made
- Centralized validate_llm_response in llm_factory.py rather than duplicating validation logic in each agent
- reasoning_effort defaults to "low" for reasoning models -- user can override by passing model_kwargs={"reasoning_effort": "high"}
- Empty responses in coding_agent return empty code string to leverage existing retry infrastructure in code_checker
- da_with_tools_node skips validation when tool_calls are present (empty content is expected during tool-calling)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 7 gap closure complete. All UAT Test 2 findings addressed.
- OpenAI reasoning models now safe to use across all agents.
- All existing tests pass with zero regressions (106 total).

## Self-Check: PASSED

All 6 files verified present. All 3 task commits verified in git log.

---
*Phase: 07-multi-llm-provider-infrastructure*
*Completed: 2026-02-09*
