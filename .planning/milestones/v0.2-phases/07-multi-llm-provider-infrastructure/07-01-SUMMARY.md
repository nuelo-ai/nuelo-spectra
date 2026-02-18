---
phase: 07-multi-llm-provider-infrastructure
plan: 01
subsystem: infra
tags: [llm, multi-provider, langchain, ollama, openrouter, anthropic, openai, google, yaml, config]

# Dependency graph
requires:
  - phase: 03-ai-agents---orchestration
    provides: LangGraph agent system with LLM factory and YAML-externalized prompts
provides:
  - Central provider registry (llm_providers.yaml) defining 5 LLM providers with default flag
  - Extended LLM factory supporting ollama (ChatOllama) and openrouter (ChatOpenAI) providers
  - Per-agent provider/model/temperature config loading functions in agents/config.py
  - Settings with ollama_base_url and openrouter_api_key fields
  - All 4 agents configured with explicit provider/model/temperature (anthropic/sonnet-4/0.0 default)
affects: [07-02-agent-wiring, 07-03-validation, phase-08, phase-09, phase-10]

# Tech tracking
tech-stack:
  added: [langchain-ollama>=0.2.0]
  patterns: [provider registry pattern, per-agent LLM configuration, default provider fallback]

key-files:
  created:
    - backend/app/config/llm_providers.yaml
  modified:
    - backend/app/config.py
    - backend/app/agents/llm_factory.py
    - backend/app/agents/config.py
    - backend/app/config/prompts.yaml
    - backend/pyproject.toml

key-decisions:
  - "Anthropic (Claude Sonnet 4.0) as default provider per user decision LLM-05"
  - "Temperature defaults to 0.0 (deterministic) for all agents per CONFIG-03"
  - "Ollama base_url extracted from kwargs to avoid duplicate keyword argument"
  - "OpenRouter uses OpenAI-compatible API with https://openrouter.ai/api/v1 base_url"
  - "OpenRouter attribution headers (HTTP-Referer, X-Title) use https://spectra.app (updateable)"

patterns-established:
  - "Provider registry pattern: central YAML defines all providers with type and metadata"
  - "Per-agent override: agents can specify provider/model/temperature, falling back to registry default"
  - "Stateless factory: llm_factory.py has no settings dependency - agents pass provider-specific options"
  - "Lazy imports: LangChain provider libraries imported only when used (reduces startup cost)"

# Metrics
duration: 3min
completed: 2026-02-07
---

# Phase 7 Plan 1: Multi-LLM Provider Infrastructure Foundation Summary

**Central provider registry with 5 LLM providers (anthropic, openai, google, ollama, openrouter), extended factory, and per-agent configuration layer**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-07T19:04:21Z
- **Completed:** 2026-02-07T19:07:38Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Created central provider registry (llm_providers.yaml) with 5 providers and default flag
- Extended LLM factory with Ollama (ChatOllama) and OpenRouter (ChatOpenAI) support
- Added per-agent config loading functions: get_agent_provider(), get_agent_model(), get_agent_temperature(), get_default_provider(), load_provider_registry()
- Extended Settings with ollama_base_url and openrouter_api_key fields
- Configured all 4 agents with explicit provider/model/temperature fields (maintaining current behavior)
- Installed langchain-ollama dependency

## Task Commits

Each task was committed atomically:

1. **Task 1: Create provider registry and extend Settings** - `adbfed0` (feat)
2. **Task 2: Extend LLM factory and per-agent config loading** - `4884792` (feat)

## Files Created/Modified

### Created
- `backend/app/config/llm_providers.yaml` - Central provider registry defining 5 LLM providers (anthropic default)

### Modified
- `backend/app/config.py` - Added ollama_base_url and openrouter_api_key to Settings class
- `backend/app/agents/llm_factory.py` - Added ollama and openrouter provider support with lazy imports
- `backend/app/agents/config.py` - Added 5 new functions for per-agent config loading and provider registry access
- `backend/app/config/prompts.yaml` - Added provider/model/temperature fields to all 4 agents with explanatory comments
- `backend/pyproject.toml` - Added langchain-ollama>=0.2.0 dependency
- `backend/uv.lock` - Updated lockfile with langchain-ollama and ollama packages

## Decisions Made

**Provider Selection:**
- Anthropic (Claude Sonnet 4.0) marked as default provider per user decision LLM-05
- Temperature defaults to 0.0 (deterministic output) for all agents per CONFIG-03
- OpenRouter uses https://spectra.app for attribution headers (updateable if production domain changes)

**Technical Patterns:**
- Stateless factory: llm_factory.py doesn't import settings - agents pass provider-specific options (e.g., base_url for ollama)
- Lazy imports: LangChain provider libraries only imported when used, reducing startup cost
- Per-agent override: agents can specify provider/model/temperature, falling back to registry default if not specified

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed ollama base_url kwarg handling**
- **Found during:** Task 2 verification (factory testing)
- **Issue:** ChatOllama() got multiple values for keyword argument 'base_url' - base_url was passed both as named argument and in **kwargs
- **Fix:** Changed `ChatOllama(model=model, base_url=kwargs.get("base_url"), **kwargs)` to extract base_url from kwargs first: `base_url = kwargs.pop("base_url", None)` then `ChatOllama(model=model, base_url=base_url, **kwargs)`
- **Files modified:** backend/app/agents/llm_factory.py
- **Verification:** Factory instantiation test passed - both ollama and openrouter create instances without errors
- **Committed in:** 4884792 (part of Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Bug fix essential for ollama provider functionality. No scope creep.

## Issues Encountered

None - plan executed smoothly with one minor bug fix during verification.

## User Setup Required

None - no external service configuration required for this plan. Provider API keys will be configured per environment via existing ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY, OLLAMA_BASE_URL, and OPENROUTER_API_KEY environment variables (documented in Settings class).

## Next Phase Readiness

**Ready for:**
- Plan 07-02 (Agent Wiring): Infrastructure layer complete - agents can now read provider/model/temperature from prompts.yaml and instantiate correct LLM via factory
- Plan 07-03 (Validation): Provider registry and config functions ready for startup validation

**Configuration Layer Complete:**
- All 5 providers (anthropic, openai, google, ollama, openrouter) registered
- Factory supports all 5 providers with correct initialization
- Per-agent config loading functions available and tested
- Settings extended with new provider-specific fields
- All agents explicitly configured (no implicit behavior changes)

**No Blockers:**
- langchain-ollama dependency installed successfully
- All verification tests passed
- Provider registry YAML validated
- Config functions tested with all 4 agents

## Self-Check: PASSED

All claimed files and commits verified:
- ✓ backend/app/config/llm_providers.yaml created
- ✓ backend/app/config.py modified
- ✓ backend/app/agents/llm_factory.py modified
- ✓ backend/app/agents/config.py modified
- ✓ backend/app/config/prompts.yaml modified
- ✓ backend/pyproject.toml modified
- ✓ Commit adbfed0 (Task 1) exists
- ✓ Commit 4884792 (Task 2) exists

---
*Phase: 07-multi-llm-provider-infrastructure*
*Completed: 2026-02-07*
