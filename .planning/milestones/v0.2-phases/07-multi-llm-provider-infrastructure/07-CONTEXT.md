# Phase 7: Multi-LLM Provider Infrastructure - Context

**Gathered:** 2026-02-07
**Status:** Ready for planning

<domain>
## Phase Boundary

System supports multiple LLM providers (Ollama, OpenRouter) with per-agent configuration, enabling cost optimization and vendor flexibility. Each of the 4 agents (Onboarding, Coding, Code Checker, Data Analysis) can independently specify which provider and model to use.

</domain>

<decisions>
## Implementation Decisions

### Provider selection & fallback
- **Agent's configured preference only** - Each agent specifies its provider in YAML config. No automatic fallback chain.
- **Fail immediately on provider failure** - If configured provider fails (network, API down, quota), surface error to user immediately. No retries, no fallback.
- **Distinguish failure types** - Provide specific error messages for different failures:
  - Network errors (connection timeout, DNS failure)
  - Authentication errors (invalid API key)
  - Quota/rate limit exceeded
  - Invalid model name
  - Provider-specific errors
- **Fail-fast startup validation** - Validate provider connectivity at system startup, not on first agent run. Backend refuses to start if any configured provider is unreachable or has invalid credentials. Forces fix before system runs.

### Per-agent configuration
- **LLM config in agent's existing YAML** - Add `provider` and `model` fields to each agent's existing YAML prompt file (e.g., `onboarding_agent.yaml` gets `provider: ollama, model: llama3`).
- **No runtime overrides** - Agent's LLM config is fixed in YAML. Users must edit config file to change provider/model. No per-request overrides.
- **Fully independent agents** - Different agents can use different providers simultaneously (e.g., Onboarding uses Ollama while Coding uses OpenRouter). System handles multiple provider connections.
- **Global default provider** - Agents without explicit `provider` field use the default provider marked in central registry (see Configuration management).

### Configuration management
- **Environment variables for credentials** - All sensitive credentials (API keys, tokens) stored in `.env` file only. Never in YAML config files.
  - `ANTHROPIC_API_KEY`
  - `GOOGLE_API_KEY`
  - `OPENAI_API_KEY`
  - `OLLAMA_BASE_URL`
  - `OPENROUTER_API_KEY`
- **Direct specification in YAML** - Agent YAML specifies provider and model directly (e.g., `provider: openrouter, model: anthropic/claude-3.5-sonnet`). No abstraction or alias system.
- **Central provider registry** - Single YAML file (`backend/config/llm_providers.yaml`) defines all available providers with their configuration:
  - **Existing providers:** Anthropic, Google, OpenAI
  - **New providers (Phase 7):** Ollama, OpenRouter
  - Each provider entry specifies: type, endpoint URL (from env), auth method
  - One provider marked with `default: true` flag as system-wide fallback
  - Agents reference providers by name from this registry
- **Fail-fast startup validation** - System performs comprehensive validation at startup:
  - **Config validation:** All agent-referenced providers must exist in registry
  - **Connectivity validation:** All configured providers must be reachable with valid credentials
  - **Failure behavior:** Backend refuses to start if any validation fails
  - **Error reporting:** Display detailed error message (which agent, which provider, what's wrong) and log full diagnostics for investigation

### Error handling & validation
- **User-friendly errors with detailed logs**
  - **User sees:** Friendly error messages with actionable hints (e.g., "Ollama not reachable. Check your OLLAMA_BASE_URL setting.")
  - **Logs contain:** Full technical details (status codes, stack traces, raw API responses) for engineer debugging
- **Balanced request logging** - Log metadata for all LLM calls but not full content:
  - Log: timestamp, provider, model, agent, token count, latency, status
  - Don't log: full prompts, full responses (saves resources)
  - Rationale: LangChain tracing handles detailed request/response inspection
- **Fail-fast startup validation** - If any agent has invalid provider config at startup:
  - Refuse to start backend
  - Display detailed error (which agent, which provider, what's wrong)
  - Log full diagnostic details for investigation
- **Classify failures** - Distinguish between temporary and permanent failures:
  - **Temporary failures:** Network timeout, rate limit → suggest "Try again" or auto-retry
  - **Permanent failures:** Invalid API key, wrong model name → suggest "Fix your configuration"
  - Different error messages guide users appropriately
- **Dedicated health check endpoint** - Implement `/health/llm` endpoint that tests each configured provider (lightweight call) and returns status. Useful for monitoring, debugging, and CI/CD validation.

### Claude's Discretion
- Log rotation configuration (file size limits, retention period)
- Exact structure of provider registry YAML schema
- Provider connection pooling and lifecycle management
- Health check lightweight call implementation (what to test without consuming quota)

</decisions>

<specifics>
## Specific Ideas

**Central registry example structure:**
```yaml
# backend/config/llm_providers.yaml
providers:
  anthropic:
    type: anthropic
    default: true  # System-wide fallback
    # API key from env: ANTHROPIC_API_KEY

  google:
    type: google

  openai:
    type: openai

  ollama:
    type: ollama
    base_url: ${OLLAMA_BASE_URL}

  openrouter:
    type: openrouter
```

**Agent YAML example:**
```yaml
# onboarding_agent.yaml
provider: anthropic
model: claude-3-5-sonnet-20241022
system_prompt: |
  You are an onboarding agent...
```

**Logging approach:**
- Use Python's standard `logging` module (already in use)
- Structured JSON logs for LLM calls
- LangChain tracing for detailed request/response inspection (not duplicated in logs)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 07-multi-llm-provider-infrastructure*
*Context gathered: 2026-02-07*
