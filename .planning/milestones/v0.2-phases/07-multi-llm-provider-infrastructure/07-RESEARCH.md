# Phase 7: Multi-LLM Provider Infrastructure - Research

**Researched:** 2026-02-07
**Domain:** LangChain multi-provider integration, YAML configuration management, FastAPI startup validation
**Confidence:** HIGH

## Summary

Phase 7 adds Ollama (local/remote) and OpenRouter gateway support to the existing multi-provider LLM infrastructure (Anthropic, OpenAI, Google), enabling per-agent provider/model configuration via YAML. The system already has provider-agnostic foundations (`llm_factory.py`, `get_llm()` factory pattern) that cleanly extend to new providers. LangChain's provider-agnostic `BaseChatModel` interface means agent code remains unchanged - only factory and configuration expand.

Implementation centers on three areas: (1) extending `llm_factory.py` with `langchain-ollama` and OpenAI-compatible OpenRouter support, (2) migrating from global LLM config to per-agent YAML configuration with central provider registry, (3) adding fail-fast startup validation, structured logging, and health check endpoints. The existing codebase already uses Pydantic settings, YAML config loading, and LangChain patterns - Phase 7 builds on proven foundations rather than introducing new paradigms.

**Primary recommendation:** Extend existing patterns (factory, YAML config, Pydantic validation) rather than reimplementing. Use LangChain's built-in provider packages, leverage FastAPI lifespan events for startup validation, and implement structured JSON logging for LLM call metadata.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Provider selection & fallback:**
- Agent's configured preference only - Each agent specifies its provider in YAML config. No automatic fallback chain.
- Fail immediately on provider failure - If configured provider fails (network, API down, quota), surface error to user immediately. No retries, no fallback.
- Distinguish failure types - Provide specific error messages for different failures (network errors, authentication errors, quota/rate limit, invalid model name, provider-specific errors).
- Fail-fast startup validation - Validate provider connectivity at system startup, not on first agent run. Backend refuses to start if any configured provider is unreachable or has invalid credentials.

**Per-agent configuration:**
- LLM config in agent's existing YAML - Add `provider` and `model` fields to each agent's existing YAML prompt file (e.g., `onboarding_agent.yaml` gets `provider: ollama, model: llama3`).
- No runtime overrides - Agent's LLM config is fixed in YAML. Users must edit config file to change provider/model. No per-request overrides.
- Fully independent agents - Different agents can use different providers simultaneously. System handles multiple provider connections.
- Global default provider - Agents without explicit `provider` field use the default provider marked in central registry.

**Configuration management:**
- Environment variables for credentials - All sensitive credentials stored in `.env` file only. Never in YAML config files: `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `OPENAI_API_KEY`, `OLLAMA_BASE_URL`, `OPENROUTER_API_KEY`.
- Direct specification in YAML - Agent YAML specifies provider and model directly (e.g., `provider: openrouter, model: anthropic/claude-3.5-sonnet`). No abstraction or alias system.
- Central provider registry - Single YAML file (`backend/config/llm_providers.yaml`) defines all available providers with configuration (type, endpoint URL, auth method). One provider marked with `default: true` flag.
- Fail-fast startup validation - System performs comprehensive validation at startup (config validation, connectivity validation). Backend refuses to start if any validation fails with detailed error message.

**Error handling & validation:**
- User-friendly errors with detailed logs - User sees friendly error messages with actionable hints. Logs contain full technical details for debugging.
- Balanced request logging - Log metadata for all LLM calls (timestamp, provider, model, agent, token count, latency, status) but not full content. LangChain tracing handles detailed request/response inspection.
- Classify failures - Distinguish temporary failures (network timeout, rate limit) from permanent failures (invalid API key, wrong model name). Different error messages guide users appropriately.
- Dedicated health check endpoint - Implement `/health/llm` endpoint that tests each configured provider with lightweight call and returns status.

### Claude's Discretion

- Log rotation configuration (file size limits, retention period)
- Exact structure of provider registry YAML schema
- Provider connection pooling and lifecycle management
- Health check lightweight call implementation (what to test without consuming quota)

### Deferred Ideas (OUT OF SCOPE)

None - discussion stayed within phase scope.

</user_constraints>

## Standard Stack

### Core LLM Provider Packages

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| langchain-ollama | Latest stable | Ollama chat model integration | Official LangChain integration package for Ollama. Supports local and remote instances via `base_url` parameter. |
| langchain-openai | Already installed | OpenRouter (via OpenAI compatibility) | OpenRouter uses OpenAI-compatible API. Existing `langchain-openai` package works with `base_url="https://openrouter.ai/api/v1"` override. No separate package needed. |
| langchain-anthropic | Already installed | Anthropic Claude models | Existing provider. |
| langchain-google-genai | Already installed | Google Gemini models | Existing provider. |
| langchain-core | >=0.3.0 (installed) | BaseChatModel interface | Provider-agnostic interface all chat models implement. |

### Supporting Packages

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pyyaml | >=6.0.0 (installed) | YAML configuration loading | Already used for `prompts.yaml`. Extend for provider registry and per-agent config. |
| pydantic-settings | >=2.0.0 (installed) | Environment variable validation | Already used in `app/config.py`. Extend with new env vars (OLLAMA_BASE_URL, OPENROUTER_API_KEY). |
| python-dotenv | >=1.0.0 (installed) | .env file loading | Already used. No changes needed. |
| structlog | Latest stable | Structured JSON logging | Optional but recommended for production-grade LLM call logging. Standard library `logging` module can work but lacks structured logging features. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| langchain-ollama | ollama-python + custom wrapper | Official LangChain integration provides `BaseChatModel` interface out-of-box. Custom wrapper adds maintenance burden. |
| OpenRouter via langchain-openai | openrouter-python SDK | No official LangChain package exists. OpenRouter's OpenAI compatibility means existing package works perfectly. |
| structlog | Standard logging module | Standard `logging` works but requires manual JSON formatting. structlog provides processors, context binding, and built-in JSON renderer. |
| Per-agent YAML files | Single monolithic config | User decided on per-agent YAML files (extends existing `prompts.yaml` pattern). Monolithic config would be simpler but less modular. |

### Installation

Already installed (existing packages):
```bash
# No new installation needed for existing providers
langchain-anthropic, langchain-openai, langchain-google-genai, pyyaml, pydantic-settings
```

New packages for Phase 7:
```bash
# Add to pyproject.toml dependencies:
langchain-ollama>=0.2.0  # Ollama integration
structlog>=25.0.0        # Optional: structured logging (Claude's discretion)
```

## Architecture Patterns

### Recommended Project Structure

```
backend/app/
├── config/
│   ├── prompts.yaml              # Existing: agent prompts with max_tokens
│   ├── allowlist.yaml            # Existing: security policies
│   └── llm_providers.yaml        # NEW: central provider registry
├── agents/
│   ├── llm_factory.py            # EXTEND: add ollama, openrouter cases
│   ├── config.py                 # EXTEND: per-agent provider/model loading
│   ├── onboarding.py             # MODIFY: use per-agent config
│   ├── coding.py                 # MODIFY: use per-agent config
│   ├── code_checker.py           # MODIFY: use per-agent config
│   └── data_analysis.py          # MODIFY: use per-agent config
├── routers/
│   └── health.py                 # EXTEND: add /health/llm endpoint
├── config.py                     # EXTEND: add OLLAMA_BASE_URL, OPENROUTER_API_KEY to Settings
└── main.py                       # EXTEND: add startup validation in lifespan
```

### Pattern 1: LangChain Provider-Agnostic Factory

**What:** Central factory function that returns `BaseChatModel` instances for any provider. Existing `llm_factory.py` already implements this pattern for Anthropic/OpenAI/Google.

**When to use:** Every agent LLM instantiation. Agent code never imports provider-specific classes directly.

**Example (extending existing factory):**
```python
# Source: Existing backend/app/agents/llm_factory.py + LangChain docs
from langchain_core.language_models import BaseChatModel

def get_llm(provider: str, model: str, api_key: str, **kwargs) -> BaseChatModel:
    """Create LLM instance based on provider."""
    provider = provider.lower()

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model, api_key=api_key, **kwargs)

    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model, api_key=api_key, **kwargs)

    elif provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=model, google_api_key=api_key, **kwargs)

    # NEW: Ollama support (local or remote)
    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        # base_url from kwargs (e.g., http://localhost:11434 or remote URL)
        return ChatOllama(model=model, base_url=kwargs.get("base_url"), **kwargs)

    # NEW: OpenRouter via OpenAI compatibility
    elif provider == "openrouter":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            **kwargs
        )

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
```

### Pattern 2: Per-Agent YAML Configuration

**What:** Extend existing `prompts.yaml` structure to include `provider` and `model` fields for each agent. Maintains single-file-per-concern pattern.

**When to use:** Defining agent-specific LLM configuration. Users edit YAML to change agent's provider/model.

**Example:**
```yaml
# Source: User decision from CONTEXT.md
# backend/config/prompts.yaml (extended)
agents:
  onboarding:
    provider: anthropic                   # NEW: which provider to use
    model: claude-3-5-sonnet-20241022    # NEW: which model to use
    max_tokens: 1500
    system_prompt: |
      You are a Data Onboarding Agent...

  coding:
    provider: openrouter                  # Different provider for cost optimization
    model: anthropic/claude-3.5-sonnet   # OpenRouter model naming format
    max_tokens: 10000
    system_prompt: |
      Generate Python code...

  code_checker:
    # No provider/model specified → use default from registry
    max_tokens: 500
    system_prompt: |
      Review code for safety...

  data_analysis:
    provider: ollama                      # Local/cost-free option
    model: llama3.1                       # Ollama model name
    max_tokens: 2000
    system_prompt: |
      Interpret execution results...
```

### Pattern 3: Central Provider Registry

**What:** Single YAML file defining all available providers with configuration metadata. Agents reference providers by name. One provider marked as default.

**When to use:** Centralizing provider configuration, validation, and discovery.

**Example:**
```yaml
# Source: User decision from CONTEXT.md
# backend/config/llm_providers.yaml (NEW FILE)
providers:
  anthropic:
    type: anthropic
    default: true                        # System-wide fallback
    # API key from env: ANTHROPIC_API_KEY
    # No base_url needed (uses default)

  google:
    type: google
    # API key from env: GOOGLE_API_KEY

  openai:
    type: openai
    # API key from env: OPENAI_API_KEY

  ollama:
    type: ollama
    base_url_env: OLLAMA_BASE_URL        # Read base_url from this env var
    # No API key needed for local Ollama

  openrouter:
    type: openrouter
    base_url: https://openrouter.ai/api/v1  # Fixed endpoint
    # API key from env: OPENROUTER_API_KEY
```

### Pattern 4: Fail-Fast Startup Validation

**What:** FastAPI lifespan event that validates all agent-provider configurations and tests connectivity before accepting requests.

**When to use:** System startup. Prevents runtime failures from misconfigurations.

**Example:**
```python
# Source: FastAPI docs + User decision from CONTEXT.md
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with LLM validation."""
    # Startup: validate LLM configuration
    try:
        validate_llm_configuration()     # Check YAML syntax, references
        await test_provider_connectivity()  # Lightweight API calls
        logger.info("LLM providers validated successfully")
    except ConfigurationError as e:
        logger.error(f"LLM configuration invalid: {e}")
        raise  # Refuse to start
    except ProviderConnectivityError as e:
        logger.error(f"Provider connectivity failed: {e}")
        raise  # Refuse to start

    yield

    # Shutdown: cleanup
    await engine.dispose()

app = FastAPI(lifespan=lifespan)
```

### Pattern 5: Structured LLM Call Logging

**What:** Log metadata for every LLM call (provider, model, tokens, latency) without logging full prompts/responses. LangSmith tracing handles detailed inspection.

**When to use:** Every LLM invocation in agents. Production monitoring and cost tracking.

**Example (Standard Library Approach):**
```python
# Source: Python logging docs + User decision from CONTEXT.md
import logging
import json
import time

logger = logging.getLogger(__name__)

async def invoke_llm_with_logging(llm, messages, agent_name, provider, model):
    """Invoke LLM with structured metadata logging."""
    start_time = time.time()

    try:
        response = await llm.ainvoke(messages)
        latency = time.time() - start_time

        # Log successful call metadata
        logger.info(json.dumps({
            "event": "llm_call",
            "agent": agent_name,
            "provider": provider,
            "model": model,
            "status": "success",
            "latency_seconds": round(latency, 3),
            "timestamp": time.time()
        }))

        return response

    except Exception as e:
        latency = time.time() - start_time

        # Log failed call metadata
        logger.error(json.dumps({
            "event": "llm_call",
            "agent": agent_name,
            "provider": provider,
            "model": model,
            "status": "error",
            "error_type": type(e).__name__,
            "latency_seconds": round(latency, 3),
            "timestamp": time.time()
        }))

        raise  # Re-raise for error handling
```

**Example (structlog Approach - Optional):**
```python
# Source: structlog docs (Claude's discretion)
import structlog

logger = structlog.get_logger()

async def invoke_llm_with_logging(llm, messages, agent_name, provider, model):
    """Invoke LLM with structured logging using structlog."""
    log = logger.bind(agent=agent_name, provider=provider, model=model)

    with log.info("llm_call") as ctx:
        try:
            response = await llm.ainvoke(messages)
            ctx.update(status="success")
            return response
        except Exception as e:
            ctx.update(status="error", error_type=type(e).__name__)
            raise
```

### Anti-Patterns to Avoid

- **Hardcoding provider logic in agents:** Never import `ChatAnthropic` directly in agent code. Always use `llm_factory.get_llm()`. Violates provider-agnostic architecture.
- **Storing API keys in YAML:** Never put `api_key: sk-...` in YAML files. Always use environment variables loaded by Pydantic Settings.
- **Silent provider failures:** Never catch provider errors without logging and re-raising. User decision requires immediate failure surfacing.
- **Logging full prompts/responses:** Wastes storage and duplicates LangSmith tracing. Log only metadata (provider, model, tokens, latency).
- **Runtime provider switching:** User decision locks provider/model in YAML. Don't build per-request override mechanisms.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| LLM provider abstraction | Custom wrapper classes for each provider | LangChain's `BaseChatModel` interface + provider packages | LangChain already provides standardized interface. Custom wrappers duplicate work and miss features (streaming, async, callbacks). |
| YAML schema validation | Manual dict key checking | Pydantic models for YAML structure | Pydantic provides automatic validation, type coercion, and clear error messages. Manual checking is error-prone. |
| Provider connectivity testing | Custom HTTP ping/probe logic | Provider-specific lightweight calls (e.g., list models API) | Each provider has different health check mechanisms. Use their native APIs instead of generic HTTP checks. |
| Structured logging | String concatenation + JSON.dumps | `structlog` library or standard `logging` with formatters | Structured logging requires context binding, processor pipelines, and format consistency. Libraries handle edge cases (exceptions, nested data, performance). |
| Environment variable loading | Manual `os.getenv()` with defaults | Pydantic Settings `BaseSettings` | Pydantic provides validation, type conversion, multiple sources (env, .env file, secrets), and clear error messages. |
| Startup validation errors | Generic exceptions with full tracebacks | Custom exception classes with user-friendly messages | Users need actionable guidance ("Check OLLAMA_BASE_URL"), not technical stack traces. Custom exceptions separate user errors from bugs. |

**Key insight:** LangChain ecosystem already solved multi-provider abstraction. Phase 7 is configuration and validation work, not building provider wrappers.

## Common Pitfalls

### Pitfall 1: Ollama Base URL Environment Variable Not Set

**What goes wrong:** Agent configured with `provider: ollama` but `OLLAMA_BASE_URL` not in `.env`. Factory receives `base_url=None`, ChatOllama defaults to `http://localhost:11434`, fails if Ollama is remote or not running locally.

**Why it happens:** Ollama's default behavior (localhost) differs from other providers (require explicit endpoint). Easy to forget base_url for remote deployments.

**How to avoid:**
- Pydantic Settings validation: mark `OLLAMA_BASE_URL` as required if any agent uses Ollama provider (check during startup).
- Provider registry YAML: explicitly document `base_url_env: OLLAMA_BASE_URL` requirement.
- Startup validation: test Ollama connectivity, fail with clear error: "Ollama configured but OLLAMA_BASE_URL not set. Set environment variable to http://localhost:11434 (local) or your remote URL."

**Warning signs:** Agent fails with connection timeout to localhost:11434 when Ollama is actually remote.

### Pitfall 2: OpenRouter Model Naming Mismatch

**What goes wrong:** User specifies `model: claude-3-5-sonnet-20241022` for OpenRouter provider. OpenRouter expects `anthropic/claude-3-5-sonnet` format. Request fails with "model not found" error.

**Why it happens:** OpenRouter uses `provider/model` naming convention different from direct provider APIs. Documentation example in CONTEXT.md shows correct format but easy to miss.

**How to avoid:**
- YAML comments: add examples in `prompts.yaml` showing OpenRouter naming format.
- Validation: startup validation could test model name format (presence of `/` for OpenRouter).
- Error messages: catch OpenRouter model-not-found errors, suggest checking model name format at https://openrouter.ai/models.

**Warning signs:** 404 or "model not found" errors from OpenRouter API during agent invocation.

### Pitfall 3: Circular Import from Startup Validation

**What goes wrong:** `main.py` lifespan imports agent modules to validate configuration. Agent modules import `get_settings()` from `config.py`. `main.py` also imports `get_settings()`. Circular import causes AttributeError or ImportError.

**Why it happens:** Python module initialization order. If `main.py` → `agents/config.py` → `config.py` → `main.py` (via lifespan), circular dependency.

**How to avoid:**
- Lazy imports: import agent config functions inside lifespan function, not at module level.
- Separate validation module: create `app/validators/llm_config.py` that both `main.py` and agents import (no circular dependency).
- Dependency injection: pass settings instance to validation function instead of importing `get_settings()` internally.

**Warning signs:** `AttributeError: module 'app.config' has no attribute 'get_settings'` during startup or agent import.

### Pitfall 4: LangSmith Tracing Disabled Silently Hides Provider Issues

**What goes wrong:** Provider connectivity fails during agent execution. Error surfaces to user. Engineer tries to debug using LangSmith tracing but `LANGSMITH_TRACING=false` in environment. No trace data available, hard to diagnose root cause.

**Why it happens:** LangSmith tracing controlled by environment variable. Developers forget to enable for debugging. Production may disable to reduce costs.

**How to avoid:**
- Documentation: prominently document that LangSmith tracing is primary debugging tool, not logs.
- Default-on for development: `.env.example` should have `LANGSMITH_TRACING=true` with comment explaining when to disable.
- Validation warning: if any agent fails during startup validation and `LANGSMITH_TRACING=false`, log warning: "LangSmith tracing disabled. Enable LANGSMITH_TRACING=true for detailed debugging."

**Warning signs:** Provider errors occur but no trace appears in LangSmith UI. Developer manually JSON.dumps() prompts/responses to debug.

### Pitfall 5: Health Check Endpoint Consumes API Quota

**What goes wrong:** `/health/llm` endpoint invokes full LLM requests for each provider to test connectivity. CI/CD pipeline hits endpoint every 10 seconds. Thousands of unnecessary API calls drain quota and cost money.

**Why it happens:** Health check uses same code path as agent invocation (calls `llm.invoke()`). Easy to copy-paste agent code without considering health check frequency.

**How to avoid:**
- Lightweight calls: use provider-specific list-models or status endpoints (e.g., Anthropic `/v1/models`, OpenRouter `/api/v1/models`). No inference needed.
- Caching: health check results cached for 60 seconds. Don't re-test providers on every request.
- Minimal prompts: if inference required (Ollama has no list-models API), use single-token prompt ("Hi") instead of real system prompts.
- Documentation: clearly label `/health/llm` as "lightweight connectivity test" not "full agent validation."

**Warning signs:** Unexpected API bills. Health check endpoint taking >1 second to respond. Quota exceeded errors in logs.

## Code Examples

Verified patterns from official sources:

### Example 1: ChatOllama Initialization (Local and Remote)

```python
# Source: LangChain Ollama integration docs
from langchain_ollama import ChatOllama

# Local Ollama instance (default)
llm_local = ChatOllama(
    model="llama3.1",
    temperature=0,
)

# Remote Ollama instance (via base_url)
llm_remote = ChatOllama(
    model="llama3.1",
    base_url="http://192.168.1.100:11434",  # Remote server
    temperature=0,
)

# With authentication (if Ollama behind proxy)
llm_auth = ChatOllama(
    model="llama3.1",
    base_url="http://username:password@proxy.example.com:11434",
    temperature=0,
)
```

### Example 2: OpenRouter via ChatOpenAI

```python
# Source: OpenRouter LangChain integration docs
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="anthropic/claude-3.5-sonnet",  # OpenRouter model naming
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    temperature=0.8,
    # Optional: attribution headers
    default_headers={
        "HTTP-Referer": "https://yourapp.com",
        "X-Title": "Your App Name"
    }
)
```

### Example 3: Pydantic Settings with New Environment Variables

```python
# Source: Pydantic Settings docs + existing backend/app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Existing LLM settings
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""

    # NEW: Phase 7 settings
    ollama_base_url: str = "http://localhost:11434"  # Default to local
    openrouter_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env")
```

### Example 4: Loading Provider Registry YAML

```python
# Source: Existing backend/app/agents/config.py pattern
from functools import lru_cache
from pathlib import Path
import yaml

@lru_cache(maxsize=1)
def load_provider_registry() -> dict:
    """Load LLM provider registry from YAML configuration.

    Returns:
        dict: Parsed registry with structure:
            {
                "providers": {
                    "anthropic": {"type": "anthropic", "default": true},
                    "ollama": {"type": "ollama", "base_url_env": "OLLAMA_BASE_URL"},
                    ...
                }
            }
    """
    config_dir = Path(__file__).parent.parent / "config"
    registry_path = config_dir / "llm_providers.yaml"

    with open(registry_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def get_default_provider() -> str:
    """Get name of default provider from registry.

    Returns:
        str: Provider name marked with default: true
    """
    registry = load_provider_registry()
    for name, config in registry["providers"].items():
        if config.get("default", False):
            return name
    raise ValueError("No default provider marked in llm_providers.yaml")
```

### Example 5: Per-Agent Config Loading

```python
# Source: Extension of existing backend/app/agents/config.py
def get_agent_provider(agent_name: str) -> str:
    """Get LLM provider for a specific agent.

    Args:
        agent_name: Name of the agent (onboarding, coding, etc.)

    Returns:
        str: Provider name (e.g., "anthropic", "ollama")
        Falls back to default provider if agent doesn't specify.
    """
    prompts = load_prompts()
    agent_config = prompts["agents"][agent_name]

    # Return agent's explicit provider or system default
    return agent_config.get("provider", get_default_provider())

def get_agent_model(agent_name: str) -> str:
    """Get LLM model for a specific agent.

    Args:
        agent_name: Name of the agent.

    Returns:
        str: Model name/ID.

    Raises:
        KeyError: If agent doesn't specify model and no default exists.
    """
    prompts = load_prompts()
    agent_config = prompts["agents"][agent_name]

    if "model" not in agent_config:
        raise KeyError(
            f"Agent '{agent_name}' has no 'model' field in prompts.yaml. "
            f"Add 'model: <model-name>' to agent configuration."
        )

    return agent_config["model"]
```

### Example 6: Startup Validation with Clear Error Messages

```python
# Source: FastAPI lifespan pattern + User decision from CONTEXT.md
from contextlib import asynccontextmanager
import httpx

class LLMConfigurationError(Exception):
    """User-facing configuration error (not a bug)."""
    pass

async def validate_provider_connectivity(provider_name: str, provider_config: dict, settings):
    """Test connectivity to a single provider.

    Args:
        provider_name: Provider name (e.g., "ollama")
        provider_config: Provider config from registry
        settings: Application settings instance

    Raises:
        LLMConfigurationError: If connectivity fails with actionable message
    """
    provider_type = provider_config["type"]

    if provider_type == "ollama":
        # Test Ollama connectivity
        base_url = getattr(settings, "ollama_base_url", None)
        if not base_url:
            raise LLMConfigurationError(
                f"Provider '{provider_name}' (Ollama) configured but OLLAMA_BASE_URL not set. "
                f"Set environment variable to http://localhost:11434 (local) or your remote URL."
            )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{base_url}/api/tags", timeout=5.0)
                response.raise_for_status()
        except httpx.ConnectError:
            raise LLMConfigurationError(
                f"Cannot connect to Ollama at {base_url}. "
                f"Check that Ollama is running and OLLAMA_BASE_URL is correct."
            )
        except httpx.TimeoutException:
            raise LLMConfigurationError(
                f"Ollama connection timeout at {base_url}. "
                f"Check network connectivity and firewall settings."
            )

    elif provider_type == "openrouter":
        # Test OpenRouter API key
        api_key = getattr(settings, "openrouter_api_key", None)
        if not api_key:
            raise LLMConfigurationError(
                f"Provider '{provider_name}' (OpenRouter) configured but OPENROUTER_API_KEY not set. "
                f"Get an API key from https://openrouter.ai/keys"
            )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=5.0
                )
                if response.status_code == 401:
                    raise LLMConfigurationError(
                        f"OpenRouter API key invalid. Check OPENROUTER_API_KEY environment variable."
                    )
                response.raise_for_status()
        except httpx.TimeoutException:
            raise LLMConfigurationError(
                f"OpenRouter API timeout. Check network connectivity."
            )

    # ... similar checks for other providers ...

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with fail-fast LLM validation."""
    settings = get_settings()
    registry = load_provider_registry()

    # Validate all configured providers
    for provider_name, provider_config in registry["providers"].items():
        try:
            await validate_provider_connectivity(provider_name, provider_config, settings)
            logger.info(f"Provider '{provider_name}' validated successfully")
        except LLMConfigurationError as e:
            logger.error(f"LLM configuration failed: {e}")
            raise  # Refuse to start backend

    logger.info("All LLM providers validated successfully")

    yield

    await engine.dispose()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single global LLM provider for all agents | Per-agent provider/model configuration | Phase 7 (v0.2) | Enables cost optimization (cheap models for simple tasks), vendor flexibility (avoid vendor lock-in), and local deployment options (Ollama for privacy). |
| Provider-specific agent code (`from langchain_anthropic import ChatAnthropic`) | Provider-agnostic factory pattern (`get_llm()`) | Already implemented in v0.1 | Agent code decoupled from provider. Adding new providers requires only factory changes, not agent rewrites. |
| Runtime provider failures surface during agent execution | Fail-fast startup validation | Phase 7 (v0.2) | Prevents production outages from misconfigurations. Forces fix before system accepts requests. |
| Unstructured log messages for LLM calls | Structured JSON logging with metadata | Phase 7 (v0.2) | Enables log aggregation, cost tracking (token counts), latency monitoring, and provider comparison. Machine-parseable instead of grep-only. |
| No health check visibility into provider status | Dedicated `/health/llm` endpoint | Phase 7 (v0.2) | CI/CD pipelines can validate provider connectivity. Monitoring systems can alert on provider downtime before users affected. |

**Deprecated/outdated:**
- **Global `LLM_PROVIDER` setting:** Phase 7 removes single global provider. Each agent specifies its own provider/model. Global setting becomes default fallback only.
- **`langchain_community.chat_models.ollama.ChatOllama`:** Older integration package. Use `langchain_ollama.ChatOllama` (official standalone package with better `base_url` support).

## Open Questions

1. **Health check quota consumption tradeoff**
   - What we know: User wants `/health/llm` endpoint testing providers. Health checks can consume API quota if using inference calls.
   - What's unclear: Best lightweight test per provider (list-models API vs minimal inference vs TCP connection check). Ollama has no list-models equivalent - must use inference or tags endpoint.
   - Recommendation: Use provider-specific non-inference endpoints where available (Anthropic `/v1/models`, OpenRouter `/api/v1/models`, Ollama `/api/tags`). Cache results for 60 seconds. Document as "connectivity check" not "inference validation."

2. **Provider connection pooling and reuse**
   - What we know: Each agent invocation currently creates new LLM instance via `get_llm()`. No connection pooling. LangChain chat models may maintain internal connection pools.
   - What's unclear: Whether to cache LLM instances at agent level (one instance per agent lifecycle) or create fresh instances per invocation. Provider rate limits, connection limits, and memory consumption tradeoffs.
   - Recommendation: Start with per-invocation instances (existing pattern). Monitor memory usage and connection counts. Add instance caching only if performance profiling shows bottleneck (unlikely for async HTTP clients).

3. **Log rotation and retention strategy**
   - What we know: User wants metadata logging for all LLM calls (timestamp, provider, model, tokens, latency). Production systems generate high log volume.
   - What's unclear: Log rotation configuration (file size limits, retention period), log storage location (local files vs log aggregation service), cost/storage tradeoffs.
   - Recommendation: Use Python `logging.handlers.RotatingFileHandler` with 100MB max file size, 10 backup files (1GB total). Document integration with external log aggregation (CloudWatch, Datadog) for production deployments. User decision defers specifics to Claude's discretion.

4. **Ollama model validation on startup**
   - What we know: ChatOllama supports `validate_model_on_init=True` parameter to verify model exists before first use. Ollama models must be pulled (`ollama pull llama3.1`) before use.
   - What's unclear: Whether startup validation should check model existence (requires listing models, parsing response) or just connectivity (simpler but defers model-not-found errors to runtime).
   - Recommendation: Connectivity validation only during startup (fast, no model-specific logic). Document in deployment guide that Ollama models must be pulled before starting backend. Runtime errors clearly indicate "model not found - run `ollama pull <model>`."

## Sources

### Primary (HIGH confidence)

**LangChain Integrations:**
- [Ollama integrations - LangChain Docs](https://docs.langchain.com/oss/python/integrations/providers/ollama)
- [ChatOllama integration - LangChain Docs](https://docs.langchain.com/oss/python/integrations/chat/ollama)
- [langchain-ollama Reference](https://reference.langchain.com/python/integrations/langchain_ollama/)
- [LangChain Integration | OpenRouter Docs](https://openrouter.ai/docs/guides/community/langchain)
- [LangChain Python integrations - Overview](https://docs.langchain.com/oss/python/integrations/providers/overview)

**Configuration & Validation:**
- [Settings Management - Pydantic](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [Settings and Environment Variables - FastAPI](https://fastapi.tiangolo.com/advanced/settings/)
- [Lifespan Events - FastAPI](https://fastapi.tiangolo.com/advanced/events/)

**Observability:**
- [LangSmith Observability - LangChain Docs](https://docs.langchain.com/langsmith/observability)
- [A Comprehensive Guide to Python Logging with Structlog | Better Stack](https://betterstack.com/community/guides/logging/structlog/)
- [structlog official documentation](https://www.structlog.org/en/stable/)

**Provider-Specific:**
- [GitHub - ollama/ollama-python](https://github.com/ollama/ollama-python)
- [OpenRouter Frameworks and Integrations](https://openrouter.ai/docs/guides/community/frameworks-and-integrations-overview)

### Secondary (MEDIUM confidence)

- [Remote Ollama Access Guide | Kite Metric](https://kitemetric.com/blogs/remote-ollama-access-a-comprehensive-guide) - Remote deployment patterns
- [Working with Different LLM Providers in LangChain](https://apxml.com/courses/python-llm-workflows/chapter-4-langchain-fundamentals/langchain-llm-providers) - Multi-provider patterns
- [FastAPI Health Check Endpoint Example | Index.dev](https://www.index.dev/blog/how-to-implement-health-check-in-python) - Health check patterns
- [JSON is all you need: Monitor LLM apps with structlog](https://ploomber.io/blog/json-monitor-llm/) - LLM logging patterns
- [How do I handle error management and retries in LangChain workflows?](https://milvus.io/ai-quick-reference/how-do-i-handle-error-management-and-retries-in-langchain-workflows) - Error handling patterns

### Tertiary (LOW confidence)

- Various Medium articles and tutorials on LangChain/Ollama/OpenRouter integration (useful for examples but not authoritative for specifications)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All packages verified via official PyPI/LangChain docs. Existing codebase already uses most dependencies.
- Architecture: HIGH - Patterns extend proven v0.1 implementations (factory, YAML config, Pydantic). LangChain `BaseChatModel` interface is stable.
- Pitfalls: MEDIUM - Based on common patterns from docs and community reports. Some pitfalls inferred from configuration complexity (e.g., circular imports) rather than directly observed.

**Research date:** 2026-02-07
**Valid until:** 2026-03-07 (30 days - stable ecosystem, LangChain integrations mature)
