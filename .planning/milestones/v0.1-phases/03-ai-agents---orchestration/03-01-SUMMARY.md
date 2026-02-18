# Phase 3 Plan 1: Agent Foundation & Config Summary

**One-liner:** Installed LangGraph orchestration framework with multi-provider LLM support (Anthropic/OpenAI/Google), YAML-based agent prompts/allowlists, and TypedDict state schemas for all 4 agents.

---

## Metadata

**Phase:** 03-ai-agents---orchestration
**Plan:** 01
**Subsystem:** Agent Infrastructure
**Completed:** 2026-02-03
**Duration:** 172 seconds (~3 minutes)

**Tags:** langgraph, langchain, multi-agent, configuration, state-management, llm-providers

---

## What Was Built

### Core Deliverables

1. **LangGraph Dependencies** (Task 1)
   - Installed langgraph 1.0.7 (LTS release for production multi-agent orchestration)
   - Installed langgraph-checkpoint-postgres 3.0.4 (thread-scoped state persistence)
   - Installed langsmith 0.6.8 (zero-code observability and tracing)
   - Installed langchain-core 1.2.8 (foundation for LangChain ecosystem)
   - Installed pyyaml 6.0+ (YAML configuration parsing)

2. **Multi-Provider LLM Support** (Task 1 & 3)
   - Installed langchain-anthropic 1.3.1 (Claude models)
   - Installed langchain-openai 1.1.7 (GPT models)
   - Installed langchain-google-genai 4.2.0 (Gemini models)
   - Created provider-agnostic LLM factory with lazy imports
   - All providers return BaseChatModel interface for agent code reusability

3. **Configuration System** (Task 1)
   - Added LLM settings to app/config.py:
     - `llm_provider` (default: "anthropic") - selects provider
     - `anthropic_api_key`, `openai_api_key`, `google_api_key` - provider credentials
     - `agent_model` (default: "claude-sonnet-4-20250514") - configurable model
     - `agent_max_retries` (default: 3) - max retry steps for validation loop
   - Added LangSmith settings:
     - `langsmith_api_key`, `langsmith_project` ("spectra-agents"), `langsmith_tracing` (false by default)

4. **YAML Configuration Files** (Task 2)
   - Created `app/config/prompts.yaml` with system prompts for all 4 agents:
     - Onboarding Agent: Data profiling instructions (max_tokens: 1500)
     - Coding Agent: Python code generation rules (max_tokens: 800)
     - Code Checker Agent: Safety and correctness validation (max_tokens: 500)
     - Data Analysis Agent: Result interpretation guidelines (max_tokens: 1000)
   - Created `app/config/allowlist.yaml` with security policies:
     - allowed_libraries: pandas, numpy, datetime, math, statistics, collections, itertools, functools, re, json
     - unsafe_builtins: eval, exec, __import__, compile, execfile, globals, locals
     - unsafe_modules: os, sys, subprocess, shutil, socket, http, urllib, requests, pathlib, io, pickle, shelve
     - unsafe_operations: open, file, input, raw_input

5. **State Schemas** (Task 2)
   - Created `app/agents/state.py` with TypedDict definitions:
     - **OnboardingState**: file_id, file_path, user_context, data_profile, data_summary, sample_data, error
     - **ChatAgentState**: file_id, user_id, user_query, data_summary, user_context, generated_code, validation_result, validation_errors, error_count, max_steps, execution_result, analysis, messages, final_response, error

6. **Config Loader** (Task 2)
   - Created `app/agents/config.py` with LRU-cached loaders:
     - `load_prompts()` - parses prompts.yaml
     - `load_allowlist()` - parses allowlist.yaml
     - `get_agent_prompt(agent_name)` - returns system prompt for named agent
     - `get_agent_max_tokens(agent_name)` - returns max tokens for agent
     - `get_allowed_libraries()` - returns set of allowed library names
     - `get_unsafe_builtins()`, `get_unsafe_modules()`, `get_unsafe_operations()` - returns unsafe operation sets

7. **LLM Factory** (Task 3)
   - Created `app/agents/llm_factory.py` with `get_llm()` factory function
   - Takes provider name, model name, API key, and kwargs
   - Returns BaseChatModel interface (provider-agnostic)
   - Uses lazy imports to avoid requiring all provider SDKs
   - Easy to extend (add new providers by adding elif branches)

### Architecture Decisions

| Decision | Rationale | Impact |
|----------|-----------|--------|
| TypedDict for state (not Pydantic) | LangGraph requires TypedDict for state schemas | State definitions compatible with LangGraph StateGraph |
| Multi-provider LLM factory | Enable flexibility for users to choose provider based on cost/performance | Agents work with any provider without code changes |
| YAML for prompts/allowlists | Externalize configuration for fast iteration without deployment | Non-developers can tune prompts; security policies centralized |
| LRU cache on config loaders | YAML files loaded once and cached | Improved performance; no repeated file I/O |
| Lazy imports in LLM factory | Import provider SDKs only when used | Users only need SDK for their chosen provider |
| Default llm_provider="anthropic" | Claude Sonnet 4 offers best reasoning for code generation | Optimal out-of-box experience; users can override via env var |
| agent_max_retries=3 default | Prevents infinite retry loops and runaway costs | Circuit breaker for validation failures |
| langsmith_tracing=false default | Opt-in observability to avoid accidental data leakage | Production-safe default; enable when needed |

---

## Deviations from Plan

None - plan executed exactly as written.

---

## Key Files

### Created
- `backend/app/config/prompts.yaml` - Agent system prompts and max_tokens configuration
- `backend/app/config/allowlist.yaml` - Allowed libraries and unsafe operation lists
- `backend/app/agents/__init__.py` - Agent package initialization
- `backend/app/agents/state.py` - OnboardingState and ChatAgentState TypedDict schemas
- `backend/app/agents/config.py` - YAML configuration loader with caching
- `backend/app/agents/llm_factory.py` - Provider-agnostic LLM factory

### Modified
- `backend/pyproject.toml` - Added langgraph, langchain, langsmith, pyyaml, provider SDKs
- `backend/app/config.py` - Added llm_provider, API keys, agent_model, agent_max_retries, langsmith settings

---

## Technical Insights

### What Worked Well

1. **LangGraph 1.0 Stability**
   - LTS release (1.0.7) installed cleanly with no dependency conflicts
   - Official documentation patterns (TypedDict state, conditional routing) well-tested
   - PostgreSQL checkpointer available for production state persistence

2. **Multi-Provider Abstraction**
   - BaseChatModel interface provides clean abstraction across all providers
   - Lazy imports enable minimal dependency footprint (users install only what they use)
   - Factory pattern makes adding new providers (Cohere, Mistral, local Ollama) straightforward

3. **YAML Configuration Approach**
   - Prompts are readable and maintainable with multi-line strings
   - Comments enabled in YAML for documentation
   - LRU caching ensures config loaded once despite multiple agent invocations

4. **TypedDict for LangGraph State**
   - Native Python typing without Pydantic overhead
   - Compatible with LangGraph's StateGraph requirements
   - Clear field documentation via docstrings

### Challenges Overcome

1. **UV Virtual Environment Execution**
   - Issue: Dependencies installed via `uv pip install` not available to system Python
   - Solution: Use `uv run python` for all verification commands
   - Lesson: Always invoke Python through uv in this project

### Security Considerations

1. **Library Allowlist Design**
   - Whitelist approach: Only explicitly allowed libraries permitted
   - Covers common data analysis libraries (pandas, numpy, math, statistics)
   - Blocks unsafe modules (os, sys, subprocess, network, file I/O)
   - Blocks unsafe builtins (eval, exec, __import__, compile, globals)

2. **API Key Management**
   - All API keys loaded from environment variables (never hardcoded)
   - LangSmith tracing disabled by default to prevent accidental data leakage
   - Settings follow 12-factor app principles

3. **Retry Loop Circuit Breaker**
   - agent_max_retries=3 prevents infinite loops from validation failures
   - Bounds worst-case token costs (Coding Agent + Code Checker called max 3 times)
   - Hard limit prevents runaway costs even if LLM generates persistently bad code

### Performance Notes

- LRU cache on config loaders: YAML files loaded once per application lifetime
- Lazy imports: Provider SDKs imported only when factory called with that provider
- TypedDict vs Pydantic: Minimal overhead for state management (no validation on every field access)

---

## Dependencies

### Requires (Phases This Built Upon)
- Phase 1 (01-01): Database foundation with SQLAlchemy and PostgreSQL
- Phase 1 (01-02): Configuration system with pydantic-settings
- Phase 2 (02-01): File service for loading user datasets

### Provides (What Was Delivered)
- Multi-agent orchestration framework ready for agent implementation
- Provider-agnostic LLM abstraction for all 4 agents
- YAML-based prompt and allowlist configuration system
- Typed state schemas for Onboarding and Chat workflows
- Security foundation with library allowlists and unsafe operation blocks

### Affects (Future Plans That Depend on This)
- Phase 3 (03-02): Onboarding Agent implementation (uses OnboardingState, prompts.yaml, llm_factory)
- Phase 3 (03-03): Coding Agent implementation (uses ChatAgentState, prompts.yaml, llm_factory, allowlist.yaml)
- Phase 3 (03-04): Code Checker Agent implementation (uses ChatAgentState, config.py allowlist accessors)
- Phase 3 (03-05): Data Analysis Agent implementation (uses ChatAgentState, prompts.yaml, llm_factory)
- Phase 3 (03-06): LangGraph orchestration (uses StateGraph with state schemas)
- Phase 3 (03-07): Agent service layer (uses llm_factory with settings)

---

## Testing

### Verification Results

All verification checks passed:

1. ✓ All LangGraph dependencies import without error
2. ✓ YAML configs exist and parse correctly
3. ✓ State schemas are valid TypedDicts importable from app.agents.state
4. ✓ Config loader returns expected prompt and allowlist data
5. ✓ Settings has LLM and LangSmith configuration fields (including llm_provider)

### Manual Testing Performed

1. Verified multi-provider LLM factory:
   - Anthropic: Returns ChatAnthropic instance (BaseChatModel)
   - OpenAI: Returns ChatOpenAI instance (BaseChatModel)
   - Google: Returns ChatGoogleGenerativeAI instance (BaseChatModel)
   - Invalid provider: Raises ValueError with clear message

2. Verified YAML parsing:
   - prompts.yaml contains all 4 agent prompts with max_tokens
   - allowlist.yaml contains allowed_libraries, unsafe_builtins, unsafe_modules, unsafe_operations

3. Verified state schemas:
   - OnboardingState has file_id, file_path, user_context, data_profile, data_summary, sample_data, error
   - ChatAgentState has file_id, user_id, user_query, data_summary, user_context, generated_code, validation_result, validation_errors, error_count, max_steps, execution_result, analysis, messages, final_response, error

### Edge Cases Considered

- LLM factory with invalid provider name → ValueError with supported providers listed
- Config loader with missing YAML files → FileNotFoundError with clear path
- Config loader with malformed YAML → yaml.YAMLError with line number
- TypedDict fields accessed before set → KeyError (by design; agents must initialize all fields)

---

## Commits

| Commit | Type | Description |
|--------|------|-------------|
| 82fe6c5 | chore | Install LangGraph dependencies and LLM config |
| e76f69b | feat | Create YAML configs, state schemas, and config loader |
| 1a0d8ec | feat | Create LLM factory for provider-agnostic model initialization |

---

## Next Steps

### Immediate (Phase 3 Continuation)

1. **Plan 03-02: Onboarding Agent**
   - Implement pandas data profiling logic
   - Create LangGraph node for Onboarding Agent
   - Integrate with FileService to trigger on upload
   - Store data_summary in File model for chat context

2. **Plan 03-03: Coding Agent**
   - Implement code generation with LLM
   - Format data_summary and user_context into prompt
   - Use allowed_libraries from allowlist.yaml in prompt

3. **Plan 03-04: Code Checker Agent**
   - Implement AST-based validation (syntax, library allowlist, unsafe operations)
   - Add LLM-based logical correctness validation
   - Return structured validation results for retry loop

### Configuration Required Before Agent Execution

**LLM Provider Setup** (at least one required):

```bash
# Option 1: Anthropic (default)
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Option 2: OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...

# Option 3: Google
LLM_PROVIDER=google
GOOGLE_API_KEY=AIza...

# Agent Configuration (optional, defaults shown)
AGENT_MODEL=claude-sonnet-4-20250514  # or gpt-4, gemini-pro
AGENT_MAX_RETRIES=3
```

**LangSmith Observability** (optional but recommended):

```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_PROJECT=spectra-agents  # default
```

### Future Enhancements

1. **Additional LLM Providers**
   - Add Cohere, Mistral, Anthropic Legacy models
   - Add local Ollama support for offline/cost-sensitive deployments
   - Add OpenRouter for unified multi-provider API

2. **Prompt Versioning**
   - Version prompts in YAML (prompts_v1.yaml, prompts_v2.yaml)
   - A/B test different prompt strategies
   - Track prompt performance metrics in LangSmith

3. **Dynamic Allowlist**
   - Per-user or per-organization library allowlists
   - Database-backed allowlist configuration
   - Allowlist override for trusted power users

4. **Cost Monitoring**
   - Track token usage per agent
   - LangSmith cost tracking integration
   - Alert on budget thresholds

---

## Lessons Learned

1. **LangGraph TypedDict Requirement**
   - LangGraph state must be TypedDict, not Pydantic BaseModel
   - Use typing.TypedDict from standard library
   - Docstrings on fields for documentation

2. **Multi-Provider Complexity**
   - Each provider has slightly different kwargs (google uses google_api_key vs api_key)
   - Factory function normalizes interface for agent code
   - Lazy imports critical to avoid requiring all provider SDKs

3. **YAML Configuration Benefits**
   - Prompt engineering iterations don't require code deployment
   - Multi-line strings in YAML preserve formatting
   - Comments enable prompt documentation inline

4. **Security Layering**
   - Allowlist validation is first layer (AST-based in Phase 3)
   - OS-level sandboxing is second layer (Phase 5: gVisor/containers)
   - Never rely solely on language-level sandboxing (fundamentally insecure per CVE-2026-0863)

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Token cost blowup from 4-agent system | Medium | High | agent_max_retries=3 circuit breaker; LangSmith cost monitoring; max_tokens caps per agent |
| Prompt injection attacks | Medium | High | Library allowlist blocks dangerous operations; OS-level sandbox in Phase 5 |
| LLM provider API outages | Low | High | Multi-provider support enables failover; provider selection via env var |
| Invalid YAML configuration | Medium | Medium | Config loader raises clear exceptions; validation on startup recommended |
| Infinite retry loops | Low | High | Bounded retry loop with agent_max_retries=3; LangGraph recursion_limit=25 as backstop |

---

## Documentation

### For Developers

- **Adding New LLM Provider:**
  1. Install provider SDK: `pip install langchain-{provider}`
  2. Add elif branch in `llm_factory.py:get_llm()`
  3. Update ValueError message with new provider name
  4. Add {provider}_api_key field to Settings

- **Modifying Agent Prompts:**
  1. Edit `app/config/prompts.yaml`
  2. No code changes needed (config loaded with LRU cache)
  3. Restart app to clear cache

- **Updating Library Allowlist:**
  1. Edit `app/config/allowlist.yaml`
  2. Add library to `allowed_libraries` list
  3. Restart app to clear cache

### For Operations

- **LangSmith Setup:**
  1. Create account at https://smith.langchain.com
  2. Generate API key from Settings → API Keys
  3. Set LANGSMITH_API_KEY and LANGSMITH_TRACING=true in .env
  4. View traces at https://smith.langchain.com (project: spectra-agents)

- **Monitoring Token Costs:**
  1. Enable LangSmith tracing
  2. Check Monitoring → Usage dashboard
  3. Set up cost alerts in LangSmith Settings

---

**Phase Progress:** 1/7 plans complete (Agent Foundation ✓)
**Next Plan:** 03-02 (Onboarding Agent Implementation)
**Blockers:** None - foundation ready for agent implementation
