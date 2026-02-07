# Stack Research: v0.2 Intelligence & Integration

**Domain:** AI-powered data analytics platform (LangGraph agent enhancements)
**Researched:** 2026-02-06
**Confidence:** HIGH

## Overview

This research focuses on stack additions needed for v0.2 features. The existing stack (FastAPI, PostgreSQL, LangGraph, LangChain, E2B, Next.js) is validated and remains unchanged. We're adding:

1. **Memory persistence** - Fix PostgreSQL checkpointing for conversation context
2. **Multi-LLM providers** - Support Ollama (local/remote) and OpenRouter (gateway)
3. **Per-agent LLM config** - Different models for different agents
4. **Web search tool** - Serper.dev integration for Analyst agent
5. **Production SMTP** - Replace Mailgun API with standard SMTP

## Recommended Stack Additions

### Memory Persistence

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| langgraph-checkpoint-postgres | 3.0.4+ | Async PostgreSQL checkpointing for LangGraph | Official LangGraph persistence layer. v3.0.4 (Jan 31, 2026) fixes async issues. Uses psycopg3 with proper async support. Already in pyproject.toml at v2.0.0 - needs upgrade. |
| psycopg[binary] | 3.3+ | PostgreSQL async driver (required by checkpoint lib) | Required dependency for AsyncPostgresSaver. Faster than pure-Python version. Binary wheels available for easy install. |

**Rationale:** v0.1 disabled PostgreSQL checkpointing due to async compatibility issues. LangGraph's AsyncPostgresSaver (v3.0+) properly supports async/await patterns with FastAPI. The key is using `autocommit=True` and `row_factory=dict_row` when creating connections manually. This enables conversation memory across sessions within the same thread (chat tab).

**Integration point:** Graph compilation with `checkpointer=AsyncPostgresSaver(...)`. Threads map to chat tabs (thread_id = chat_id). Closing tab clears thread.

### Multi-LLM Provider Support

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| langchain-ollama | 1.0.1+ | Official Ollama integration for LangChain | Official LangChain package (Dec 2025). Supports ChatOllama with streaming, tool binding, multi-modal. Works with local (http://localhost:11434) or remote Ollama instances. |
| ollama | 0.6.1+ | Python client for Ollama API (optional) | Useful for model management (pull, list, delete) outside LangChain. Not required if only using ChatOllama for inference. |
| langchain-openai | (existing) | OpenRouter integration via OpenAI-compatible API | Already installed. OpenRouter implements OpenAI-compatible API. Use ChatOpenAI with `base_url="https://openrouter.ai/api/v1"`. |

**Rationale:**
- **Ollama** enables cost-effective local models (DeepSeek-R1, Llama, Qwen) and remote Ollama servers. ChatOllama from langchain-ollama provides native LangChain integration.
- **OpenRouter** acts as gateway to 100+ models (Claude, GPT, Gemini, DeepSeek via API). Uses existing langchain-openai with custom base_url - no new dependencies needed.

**Integration point:** Agent configuration in YAML. Each agent specifies provider (anthropic/openai/ollama/openrouter) and model. LangGraph nodes instantiate appropriate ChatModel based on config.

### Web Search Tool

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| langchain-community | 0.4.1+ | Provides GoogleSerperAPIWrapper for Serper.dev | Official LangChain community integrations. Includes Serper tool via `load_tools(["google-serper"])`. Well-maintained, 2500 free searches on Serper.dev. |

**Rationale:** Serper.dev is fast, cheap Google Search API ($0.001/search vs $0.002+ for SerpAPI). LangChain has native integration via GoogleSerperAPIWrapper. Returns answer boxes, knowledge graphs, organic results. Perfect for Analyst agent benchmarking queries ("compare my sales to industry average").

**Integration point:** Tool binding on Analyst agent node. Set `SERPER_API_KEY` env var. Agent automatically uses tool when query requires external data.

### Production SMTP

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| aiosmtplib | 5.1.0+ | Async SMTP client for Python | Production-stable (Jan 25, 2026), zero dependencies, Python 3.10+. Native async/await for FastAPI. More explicit control than fastapi-mail wrapper. |
| jinja2 | 3.1+ | Email template rendering | Industry standard for Python templating. Already used in LangChain/LangGraph config. Simple, fast, well-documented. |

**Rationale:**
- **aiosmtplib** provides direct async SMTP control. Simpler than fastapi-mail (which wraps aiosmtplib anyway). Production-ready (v5.x), MIT license, comprehensive typing.
- **Jinja2** already in ecosystem (LangChain dependency). Familiar template syntax for HTML emails.
- **Why not fastapi-mail?** Adds unnecessary abstraction. We only need password reset emails - aiosmtplib + jinja2 is lighter and more maintainable.

**Integration point:** SMTP config in settings (host, port, username, password, use_tls). Jinja2 templates in `backend/app/templates/emails/`. Helper function `send_email(to, subject, template, context)`.

## Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| psycopg[binary] | 3.3+ | PostgreSQL driver for checkpoint persistence | Required by langgraph-checkpoint-postgres. Install with binary wheels for performance. |
| httpx | 0.27+ (existing) | HTTP client for API calls | Already installed. Used for Serper.dev API if needed outside LangChain wrapper. |
| pyyaml | 6.0+ (existing) | YAML config parsing | Already installed. Used for agent LLM configuration files. |

## Installation

```bash
# Memory persistence (upgrade existing)
pip install --upgrade langgraph-checkpoint-postgres>=3.0.4
pip install psycopg[binary]>=3.3

# Multi-LLM providers
pip install langchain-ollama>=1.0.1
pip install ollama>=0.6.1  # Optional, for model management

# Web search tool
pip install langchain-community>=0.4.1

# Production SMTP
pip install aiosmtplib>=5.1.0
pip install jinja2>=3.1.0  # May already be installed via dependencies
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| AsyncPostgresSaver | Redis checkpointing (langgraph-checkpoint-redis) | If needing <1ms read/write latency or cross-process state sharing. Overkill for single-server deployment. |
| AsyncPostgresSaver | InMemorySaver | Development/testing only. State lost on restart. Not for production. |
| langchain-ollama | Direct Ollama REST API | If avoiding LangChain abstractions. Loses tool binding, streaming support. |
| OpenRouter via ChatOpenAI | Individual provider packages (langchain-google-genai, etc) | If using only one provider. OpenRouter gives flexibility without package sprawl. |
| aiosmtplib | fastapi-mail | If needing bulk emails, attachments, complex templates. Too heavy for password resets. |
| aiosmtplib | smtplib (sync) | Never. FastAPI is async - sync SMTP blocks event loop. |
| Serper.dev | SerpAPI | If needing advanced features (location-based, images). More expensive ($0.002+/search). |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| langgraph-checkpoint-postgres v2.0.x | Async compatibility issues in v2.x (reported in v0.1). Known bugs with connection handling. | langgraph-checkpoint-postgres v3.0.4+. Fixed in v3.x releases. |
| smtplib (synchronous) | Blocks FastAPI async event loop. Causes performance degradation under load. | aiosmtplib for proper async support. |
| InMemorySaver in production | State lost on server restart. No conversation persistence. | AsyncPostgresSaver with PostgreSQL. |
| langchain-community chat models | Deprecated in favor of dedicated packages (langchain-ollama, etc). | Use official provider packages. |
| Custom Serper HTTP client | Reinventing the wheel. LangChain integration handles errors, retries, parsing. | GoogleSerperAPIWrapper from langchain-community. |

## Configuration Patterns

### Memory Persistence Pattern

```python
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg import AsyncConnection
from psycopg.rows import dict_row

# Create checkpointer with connection pool
async with await AsyncConnection.connect(
    DATABASE_URL,
    autocommit=True,
    row_factory=dict_row
) as conn:
    checkpointer = AsyncPostgresSaver(conn)
    await checkpointer.setup()  # Create tables on first run

    # Compile graph with checkpointer
    graph = workflow.compile(checkpointer=checkpointer)

    # Use thread_id for session persistence
    config = {"configurable": {"thread_id": chat_tab_id}}
    result = await graph.ainvoke(input, config=config)
```

### Per-Agent LLM Configuration Pattern

```yaml
# config/agents.yaml
agents:
  coding_agent:
    provider: anthropic
    model: claude-sonnet-4.5-20250929
    temperature: 0.0

  code_checker_agent:
    provider: openai
    model: gpt-4o
    temperature: 0.0

  analysis_agent:
    provider: openrouter
    model: anthropic/claude-3.7-sonnet
    temperature: 0.3

  onboarding_agent:
    provider: ollama
    model: deepseek-r1:8b
    base_url: http://localhost:11434  # or remote Ollama server
    temperature: 0.5
```

```python
# In agent node function
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama

def create_llm(config: dict):
    """Factory function to create LLM based on config"""
    provider = config["provider"]

    if provider == "anthropic":
        return ChatAnthropic(model=config["model"], temperature=config["temperature"])
    elif provider == "openai":
        return ChatOpenAI(model=config["model"], temperature=config["temperature"])
    elif provider == "openrouter":
        return ChatOpenAI(
            model=config["model"],
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            temperature=config["temperature"]
        )
    elif provider == "ollama":
        return ChatOllama(
            model=config["model"],
            base_url=config.get("base_url", "http://localhost:11434"),
            temperature=config["temperature"]
        )
```

### Web Search Tool Pattern

```python
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.agent_toolkits import load_tools

# Option 1: Direct wrapper
search = GoogleSerperAPIWrapper()
results = await search.arun("industry average conversion rate for e-commerce 2026")

# Option 2: As agent tool
tools = load_tools(["google-serper"])  # Requires SERPER_API_KEY env var
analyst_llm = ChatAnthropic(model="claude-sonnet-4.5").bind_tools(tools)
```

### SMTP Email Pattern

```python
import aiosmtplib
from jinja2 import Environment, FileSystemLoader
from email.message import EmailMessage

async def send_email(to: str, subject: str, template: str, context: dict):
    """Send HTML email using SMTP"""
    # Load template
    env = Environment(loader=FileSystemLoader("app/templates/emails"))
    template_obj = env.get_template(f"{template}.html")
    html_content = template_obj.render(**context)

    # Create message
    message = EmailMessage()
    message["From"] = settings.SMTP_FROM
    message["To"] = to
    message["Subject"] = subject
    message.set_content(html_content, subtype="html")

    # Send via SMTP
    await aiosmtplib.send(
        message,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USERNAME,
        password=settings.SMTP_PASSWORD,
        use_tls=settings.SMTP_USE_TLS
    )

# Usage
await send_email(
    to="user@example.com",
    subject="Reset Your Password",
    template="reset_password",
    context={"reset_link": "https://app.com/reset?token=..."}
)
```

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| langgraph-checkpoint-postgres 3.0.4 | langgraph>=1.0.7, psycopg>=3.3 | Requires psycopg3 (not psycopg2). Use binary wheels for performance. |
| langchain-ollama 1.0.1 | langchain-core>=0.3.0, Python 3.10+ | Works with existing LangChain ecosystem. |
| langchain-community 0.4.1 | langchain-core>=0.3.0 | May have breaking changes on minor releases (0.x series). Pin versions. |
| aiosmtplib 5.1.0 | Python 3.10+ | Zero dependencies. Production-stable (5.x). |
| psycopg[binary] 3.3 | PostgreSQL 9.5-18, Python 3.9+ | Binary wheels for Linux/macOS/Windows. Faster than pure-Python. |

**Critical compatibility notes:**

1. **PostgreSQL checkpointing:** langgraph-checkpoint-postgres v3.0+ requires psycopg3 (not psycopg2 or asyncpg). The existing `asyncpg>=0.29.0` in pyproject.toml is used by SQLAlchemy, not by checkpointer. Both can coexist.

2. **Python version:** aiosmtplib requires Python 3.10+. Existing requirement is `>=3.12`, so no conflict.

3. **LangChain ecosystem:** All LangChain packages (langchain-ollama, langchain-community, langchain-anthropic, langchain-openai) work with langchain-core>=0.3.0 (currently installed).

4. **Ollama server:** langchain-ollama client is independent of Ollama server version. Ollama server must be installed separately (not a Python package).

## Environment Variables Required

```bash
# Memory persistence (existing PostgreSQL)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/spectra

# Multi-LLM providers
ANTHROPIC_API_KEY=sk-ant-...  # Existing
OPENAI_API_KEY=sk-...  # Existing
OPENROUTER_API_KEY=sk-or-...  # New
OLLAMA_BASE_URL=http://localhost:11434  # Optional, defaults to localhost

# Web search
SERPER_API_KEY=...  # Get from serper.dev (2500 free credits)

# SMTP email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=noreply@spectra.com
SMTP_PASSWORD=...
SMTP_FROM=Spectra <noreply@spectra.com>
SMTP_USE_TLS=true
```

## Migration from v0.1

### Memory Persistence

**v0.1 state:** PostgreSQL checkpointing disabled in code due to async issues.

**v0.2 changes:**
1. Upgrade `langgraph-checkpoint-postgres` from 2.0.0 to 3.0.4
2. Add `psycopg[binary]>=3.3`
3. Enable checkpointing with `AsyncPostgresSaver`
4. Map thread_id to chat_tab_id for session persistence
5. Clear thread when tab closes (warn user before closing)

**No database migration needed.** AsyncPostgresSaver creates its own tables (checkpoints, checkpoint_writes).

### Multi-LLM Providers

**v0.1 state:** Single provider per environment (ANTHROPIC_API_KEY or OPENAI_API_KEY).

**v0.2 changes:**
1. Add `langchain-ollama>=1.0.1`
2. Move LLM config from env vars to YAML
3. Implement LLM factory function (`create_llm(config)`)
4. Update each agent node to load config and create appropriate ChatModel

**Backward compatible:** Existing API keys still work. New keys (OPENROUTER_API_KEY) optional until agents configured to use them.

### Web Search Tool

**v0.1 state:** No web search capability.

**v0.2 changes:**
1. Add `langchain-community>=0.4.1`
2. Set `SERPER_API_KEY` env var
3. Bind `google-serper` tool to Analyst agent
4. Agent automatically invokes when query needs external data

**No breaking changes.** Tool is opt-in via agent configuration.

### SMTP Email

**v0.1 state:** Mailgun API for password resets. Dev mode logs to console.

**v0.2 changes:**
1. Add `aiosmtplib>=5.1.0`
2. Create Jinja2 email templates
3. Replace Mailgun API calls with `send_email()` helper
4. Set SMTP env vars
5. Remove Mailgun dependency and API key

**Breaking change:** Requires SMTP configuration. No automatic fallback. Dev mode should use tools like Mailpit or MailHog for local SMTP testing.

## Deployment Considerations

### Docker

Add to backend Dockerfile:
```dockerfile
# Install dependencies for memory persistence
RUN pip install --no-cache-dir psycopg[binary]>=3.3

# No additional system dependencies needed
# (psycopg binary wheels include libpq)
```

### Ollama

For local Ollama:
```yaml
# docker-compose.yml
services:
  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama-data:/root/.ollama
    ports:
      - "11434:11434"

  backend:
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
```

For remote Ollama: Set `OLLAMA_BASE_URL` to remote server URL.

### SMTP Testing (Development)

Use Mailpit for local SMTP testing:
```yaml
# docker-compose.yml
services:
  mailpit:
    image: axllent/mailpit:latest
    ports:
      - "1025:1025"  # SMTP
      - "8025:8025"  # Web UI

  backend:
    environment:
      - SMTP_HOST=mailpit
      - SMTP_PORT=1025
      - SMTP_USE_TLS=false
```

Access web UI at http://localhost:8025 to view sent emails.

## Testing Strategy

### Memory Persistence

1. Create chat tab, send message
2. Get checkpoint via `checkpointer.aget(thread_id)`
3. Verify state saved
4. Send follow-up message referencing first message
5. Verify context maintained
6. Simulate tab close (delete thread)
7. Verify subsequent messages don't have context

### Multi-LLM Providers

1. Configure different agents with different providers
2. Send queries that trigger each agent
3. Verify correct model used (check LangSmith traces)
4. Test Ollama with local server
5. Test OpenRouter with multiple models
6. Verify cost tracking per provider

### Web Search Tool

1. Send query requiring external data ("industry average sales")
2. Verify Serper API called (check logs)
3. Verify results incorporated into response
4. Test with API key missing (should fail gracefully)
5. Monitor Serper credit usage

### SMTP Email

1. Trigger password reset
2. Verify email sent (check Mailpit web UI in dev)
3. Verify HTML rendering correct
4. Test with invalid SMTP credentials (should fail gracefully)
5. Test with various SMTP providers (Gmail, SendGrid, AWS SES)

## Cost Analysis

| Feature | Cost | Notes |
|---------|------|-------|
| Memory persistence | $0 | Uses existing PostgreSQL. ~1KB per checkpoint. |
| Ollama (local) | $0 | Runs on server. GPU recommended for speed. |
| Ollama (remote) | Variable | Depends on hosting provider. |
| OpenRouter | $0.0001-0.03/1K tokens | Model-dependent. DeepSeek-R1 very cheap (~$0.0001/1K). |
| Serper.dev | $0.001/search | 2500 free credits. Then $50/50K searches. |
| SMTP | $0-10/month | Gmail (free for low volume), SendGrid (free tier 100/day), AWS SES ($0.10/1K). |

**v0.2 cost impact:** Minimal if using Ollama for most agents. Serper only used when needed. SMTP negligible.

## Sources

**Memory Persistence:**
- [LangGraph Checkpointing Documentation](https://docs.langchain.com/oss/python/langgraph/persistence)
- [langgraph-checkpoint-postgres PyPI](https://pypi.org/project/langgraph-checkpoint-postgres/)
- [Mastering LangGraph Checkpointing: Best Practices for 2025](https://sparkco.ai/blog/mastering-langgraph-checkpointing-best-practices-for-2025)
- [Harnessing the Power of LangGraph Checkpoint With PostgreSQL](https://www.oreateai.com/blog/harnessing-the-power-of-langgraph-checkpoint-with-postgresql/68853ebedf7b26456aa5bff751d06842)

**Multi-LLM Providers:**
- [Ollama Python library GitHub](https://github.com/ollama/ollama-python)
- [langchain-ollama PyPI](https://pypi.org/project/langchain-ollama/)
- [ChatOllama LangChain Integration](https://docs.langchain.com/oss/python/integrations/chat/ollama)
- [OpenRouter LangChain Integration](https://openrouter.ai/docs/guides/community/langchain)
- [LangGraph Configuration Guide](https://www.baihezi.com/mirrors/langgraph/how-tos/configuration/index.html)

**Web Search Tool:**
- [Serper LangChain Integration](https://docs.langchain.com/oss/python/integrations/providers/google_serper)
- [Serper.dev Official Site](https://serper.dev/)
- [langchain-community PyPI](https://pypi.org/project/langchain-community/)

**SMTP Email:**
- [aiosmtplib PyPI](https://pypi.org/project/aiosmtplib/)
- [aiosmtplib Documentation](https://aiosmtplib.readthedocs.io/)
- [FastAPI Email Templates Guide](https://sabuhish.github.io/fastapi-mail/)
- [Python SMTP Tutorial 2026](https://mailtrap.io/blog/smtplib/)

**Performance & Compatibility:**
- [Psycopg 3 vs Asyncpg](https://fernandoarteaga.dev/blog/psycopg-vs-asyncpg/)
- [LangChain 1.0 Release](https://blog.langchain.com/langchain-langgraph-1dot0/)

---
*Stack research for: Spectra v0.2 Intelligence & Integration*
*Researched: 2026-02-06*
*Confidence: HIGH - All versions verified from official sources (PyPI, official docs)*
