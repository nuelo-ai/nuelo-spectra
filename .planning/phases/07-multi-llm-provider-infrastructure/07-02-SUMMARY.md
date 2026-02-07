---
phase: 07-multi-llm-provider-infrastructure
plan: 02
subsystem: ai-agents
tags: [llm, multi-provider, per-agent-config, yaml-config, anthropic, openai, google, ollama, openrouter]

# Dependency graph
requires:
  - phase: 07-01
    provides: get_agent_provider, get_agent_model, get_agent_temperature helper functions in agents/config.py
provides:
  - All 4 agents (onboarding, coding, code_checker, data_analysis) using per-agent LLM provider/model/temperature from YAML
  - Shared get_api_key_for_provider() function supporting all 5 providers
  - Temperature passed to get_llm() for all agents
  - Zero dependencies on global settings.llm_provider or settings.agent_model in agent code
affects: [08-session-memory, 09-query-suggestions, 10-web-search]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Per-agent LLM config pattern: each agent reads provider/model/temperature from prompts.yaml"
    - "Shared API key resolution: get_api_key_for_provider() maps provider names to settings fields"
    - "Provider-specific kwargs pattern: temperature and base_url passed via kwargs to get_llm()"

key-files:
  created: []
  modified:
    - backend/app/agents/config.py
    - backend/app/agents/onboarding.py
    - backend/app/agents/coding.py
    - backend/app/agents/graph.py
    - backend/app/agents/data_analysis.py

key-decisions:
  - "Shared get_api_key_for_provider() in agents/config.py instead of duplicated logic in each agent"
  - "Temperature passed to get_llm() via kwargs for all agents (CONFIG-03)"
  - "Ollama base_url passed via kwargs when provider is ollama"

patterns-established:
  - "Agent LLM initialization: provider/model/temperature from YAML, API key from shared helper, kwargs for provider-specific options"

# Metrics
duration: 2min
completed: 2026-02-07
---

# Phase 7 Plan 2: Agent Wiring Summary

**All 4 agents migrated to per-agent YAML config (provider/model/temperature), enabling independent LLM provider selection per agent**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-07T19:12:22Z
- **Completed:** 2026-02-07T19:14:45Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- All 4 agents (onboarding, coding, code_checker, data_analysis) now read provider/model/temperature from prompts.yaml
- Shared API key resolution function supporting all 5 providers (anthropic, openai, google, ollama, openrouter)
- Temperature parameter integrated into all agent LLM calls
- Removed all global LLM settings references (settings.llm_provider, settings.agent_model) from agent code
- Maintained backward compatibility: default behavior unchanged (all agents use anthropic/sonnet-4/temperature=0.0)

## Task Commits

Each task was committed atomically:

1. **Task 1: Migrate onboarding and coding agents to per-agent config** - `2d9039a` (feat)
2. **Task 2: Migrate code_checker and data_analysis agents to per-agent config** - `66f604d` (feat)

## Files Created/Modified
- `backend/app/agents/config.py` - Added get_api_key_for_provider() function for API key resolution
- `backend/app/agents/onboarding.py` - Migrated to per-agent config, removed _get_api_key() method
- `backend/app/agents/coding.py` - Migrated to per-agent config, removed _get_api_key() function
- `backend/app/agents/graph.py` - Migrated code_checker to per-agent config, removed _get_api_key() function
- `backend/app/agents/data_analysis.py` - Migrated to per-agent config, removed _get_api_key() function

## Decisions Made

**1. Shared API key helper in agents/config.py**
- Rationale: Avoid code duplication across 4 agents, centralize provider-to-setting mapping
- Implementation: get_api_key_for_provider(provider, settings) supports all 5 providers
- Benefit: Single source of truth, easier to add new providers in future

**2. Temperature via kwargs to get_llm()**
- Rationale: Fulfill CONFIG-03 requirement from 07-CONTEXT.md
- Implementation: Build kwargs dict with temperature + provider-specific options (e.g., Ollama base_url)
- Benefit: Flexible per-agent temperature settings (e.g., data_analysis could use 0.7 for varied interpretations)

**3. Remove all _get_api_key() functions**
- Rationale: Eliminate duplication, use shared helper
- Implementation: Replaced 4 separate implementations with single get_api_key_for_provider()
- Benefit: Reduced maintenance burden, consistent error handling

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for Wave 2 (Plan 3: Provider Validation):**
- All agents using per-agent config infrastructure
- Temperature support in place
- API key resolution working for all providers
- System ready for provider validation at startup

**Blockers:** None

**Next Steps:** Plan 3 will add provider configuration validation at startup (fail-fast pattern for both config and connectivity issues).

## Self-Check: PASSED

All files verified:
- backend/app/agents/config.py - FOUND
- backend/app/agents/onboarding.py - FOUND
- backend/app/agents/coding.py - FOUND
- backend/app/agents/graph.py - FOUND
- backend/app/agents/data_analysis.py - FOUND

All commits verified:
- 2d9039a - FOUND
- 66f604d - FOUND

---
*Phase: 07-multi-llm-provider-infrastructure*
*Completed: 2026-02-07*
