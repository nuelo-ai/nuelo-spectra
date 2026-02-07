# Architecture Research: LangGraph Memory, Multi-LLM, and Tool Integration

**Domain:** LangGraph agent system enhancement
**Researched:** 2026-02-06
**Confidence:** MEDIUM-HIGH

## Executive Summary

This research focuses on integrating three capabilities into Spectra's existing 4-agent LangGraph system:
1. **Memory persistence** using AsyncPostgresSaver (fixing v0.1's disabled checkpointing)
2. **Multi-LLM support** for Ollama and OpenRouter (extending existing Anthropic/OpenAI/Google)
3. **Tool integration** for web search (Tavily/Serper.dev)

Key finding: All three features integrate cleanly with existing architecture through well-defined LangGraph extension points. The async PostgreSQL checkpointing issue from v0.1 is resolved in current LangGraph versions with AsyncPostgresSaver from `langgraph-checkpoint-postgres`.

## Current Architecture (v0.1)

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Endpoints                        │
│  (chat stream endpoint with SSE, file upload, auth)          │
├─────────────────────────────────────────────────────────────┤
│                      LangGraph Workflow                      │
│  ┌─────────┐   ┌──────────┐   ┌─────────┐   ┌──────────┐   │
│  │Onboarding│→ │  Coding  │ → │  Code   │ → │  Data    │   │
│  │  Agent  │   │  Agent   │   │ Checker │   │ Analysis │   │
│  └─────────┘   └──────────┘   └─────────┘   └──────────┘   │
│       ↓              ↓             ↓              ↓          │
│                  Shared State (TypedDict)                    │
│  { user_query, generated_code, execution_result, ... }      │
├─────────────────────────────────────────────────────────────┤
│                     Supporting Services                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │LLM Factory│  │YAML Config│  │E2B Sandbox│  │PostgreSQL│   │
│  │get_llm()  │  │(prompts)  │  │(execute) │  │(data)    │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Component Inventory

| Component | Current Implementation | File Location |
|-----------|------------------------|---------------|
| Graph definition | StateGraph with 5 nodes (4 agents + halt) | `backend/app/agents/graph.py` |
| State schema | ChatAgentState TypedDict (13 keys) | `backend/app/agents/state.py` |
| LLM factory | Supports Anthropic, OpenAI, Google | `backend/app/agents/llm_factory.py` |
| Config loader | YAML prompts with max_tokens per agent | `backend/app/agents/config.py` |
| Checkpointing | **Disabled** (lines 476-480 in graph.py) | None (was PostgresSaver) |
| Tool calling | **Not implemented** | N/A |
| Message history | State key exists but unused | `state["messages"]` |

### Current Limitations (v0.1)

1. **No memory**: `checkpointer=None` in graph compilation (line 501)
2. **Single LLM provider**: Global setting, all agents use same provider/model
3. **No tool integration**: Agents cannot call external services
4. **Fresh state per request**: No conversation context across queries
5. **Async incompatibility**: Comment at line 476 mentions `NotImplementedError` with async streaming

## Integration Architecture (v0.2)

### System Overview with Enhancements

```
┌───────────────────────────────────────────────────────────────────┐
│                     FastAPI Lifespan & Endpoints                  │
│  (connection pool init, SSE streaming with thread_id)             │
├───────────────────────────────────────────────────────────────────┤
│                    LangGraph with Memory                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐    │
│  │ Onboarding │  │   Coding   │  │    Code    │  │   Data   │    │
│  │   Agent    │→ │   Agent    │→ │  Checker   │→ │ Analysis │    │
│  │ (Claude)   │  │ (OpenRouter│  │  (Claude)  │  │ (Ollama) │    │
│  └────────────┘  └────────────┘  └────────────┘  └──────────┘    │
│        ↓               ↓                ↓               ↓          │
│                    Shared State (TypedDict)                        │
│  { messages: Annotated[list, add_messages], ... }                 │
│        ↓                                                           │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │         AsyncPostgresSaver (checkpointer)               │      │
│  │  thread_id: user_{user_id}_file_{file_id}              │      │
│  │  checkpoint: JSONB state after each node               │      │
│  └─────────────────────────────────────────────────────────┘      │
├───────────────────────────────────────────────────────────────────┤
│                      Enhanced Services                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────┐ │
│  │Multi-LLM │  │ Agent    │  │ToolNode  │  │Connection│  │SMTP│ │
│  │ Factory  │  │Config    │  │(web      │  │  Pool    │  │Svc │ │
│  │(6 provs) │  │(per-agent│  │ search)  │  │(async)   │  │    │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └────┘ │
└───────────────────────────────────────────────────────────────────┘
```

## 1. Memory Persistence Integration

### AsyncPostgresSaver Setup

**Implementation pattern:** FastAPI lifespan function manages connection pool lifecycle.

```python
# backend/app/main.py or graph.py
from contextlib import asynccontextmanager
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage shared resources across application lifetime."""
    settings = get_settings()

    # Initialize async connection pool
    pool = AsyncConnectionPool(
        conninfo=settings.database_url,
        min_size=2,
        max_size=10,
        timeout=30.0,
        kwargs={
            "autocommit": True,
            "row_factory": dict_row,
        }
    )
    await pool.open()

    # Initialize checkpointer and setup tables
    checkpointer = AsyncPostgresSaver(pool)
    await checkpointer.setup()

    # Store in app state for endpoint access
    app.state.checkpointer = checkpointer

    yield

    # Cleanup
    await pool.close()

app = FastAPI(lifespan=lifespan)
```

### Graph Compilation with Memory

```python
# backend/app/agents/graph.py
def build_chat_graph(checkpointer=None):
    """Build and compile the chat analysis LangGraph workflow.

    Args:
        checkpointer: Optional AsyncPostgresSaver for state persistence
    """
    graph = StateGraph(ChatAgentState)

    # Add nodes (same as v0.1)
    graph.add_node("coding_agent", coding_agent)
    graph.add_node("code_checker", code_checker_node)
    graph.add_node("execute", execute_in_sandbox)
    graph.add_node("data_analysis", data_analysis_agent)
    graph.add_node("halt", halt_node)

    # Add edges (same as v0.1)
    graph.set_entry_point("coding_agent")
    graph.add_edge("coding_agent", "code_checker")
    graph.add_edge("execute", "data_analysis")
    graph.set_finish_point("data_analysis")
    graph.set_finish_point("halt")

    # Compile WITH checkpointer
    compiled = graph.compile(checkpointer=checkpointer)

    return compiled
```

### State Schema Enhancement for Messages

**Change:** Add `add_messages` reducer for message history.

```python
# backend/app/agents/state.py
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class ChatAgentState(TypedDict):
    """State for the Chat Agent workflow."""

    # Add reducer for message history
    messages: Annotated[list[BaseMessage], add_messages]

    # Existing fields (unchanged)
    file_id: str
    user_id: str
    user_query: str
    data_summary: str
    data_profile: str
    user_context: str
    file_path: str
    generated_code: str
    validation_result: str
    validation_errors: list[str]
    error_count: int
    max_steps: int
    execution_result: str
    analysis: str
    final_response: str
    error: str
```

### Endpoint Integration with thread_id

```python
# backend/app/api/endpoints/chat.py
@router.post("/stream")
async def stream_chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stream chat responses with memory persistence."""

    # Get checkpointer from app state
    checkpointer = request.app.state.checkpointer

    # Build graph with checkpointer
    graph = build_chat_graph(checkpointer=checkpointer)

    # Construct thread_id for conversation isolation
    thread_id = f"user_{current_user.id}_file_{request.file_id}"

    # Invoke graph with config
    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    # Initial state (first message or continuing conversation)
    initial_state = {
        "user_query": request.message,
        "file_id": request.file_id,
        "user_id": str(current_user.id),
        # ... other state fields
    }

    # Stream with memory
    async for chunk in graph.astream(initial_state, config=config):
        # Stream SSE events to client
        yield format_sse_event(chunk)
```

### Database Schema (Auto-created by AsyncPostgresSaver)

When `checkpointer.setup()` runs, LangGraph creates two tables:

| Table | Schema | Purpose |
|-------|--------|---------|
| `checkpoints` | `(thread_id TEXT, checkpoint_id UUID, checkpoint JSONB, metadata JSONB)` | Main state snapshots after each node |
| `checkpoint_blobs` | `(thread_id TEXT, checkpoint_id UUID, channel TEXT, data BYTEA)` | Large objects (serialized messages) |

### Configuration Options

```yaml
# backend/app/config/memory.yaml (new file)
memory:
  enabled: true

  # Context window configuration
  max_messages: 50  # Maximum messages to keep in history
  context_window_tokens: 8000  # Approximate token limit

  # Checkpoint settings
  checkpoint_frequency: "per_node"  # Options: per_node, per_edge, manual

  # Cleanup policy
  ttl_days: 30  # Delete checkpoints older than 30 days
  auto_cleanup: true
```

### Context Window Management

**Pattern:** Implement message trimming in agent nodes.

```python
# backend/app/agents/utils.py
from langchain_core.messages import trim_messages

def get_context_window_messages(state: ChatAgentState, max_messages: int = 50) -> list:
    """Trim message history to fit context window.

    Args:
        state: Current graph state
        max_messages: Maximum messages to keep

    Returns:
        Trimmed message list
    """
    messages = state.get("messages", [])

    # Keep system messages, trim rest
    return trim_messages(
        messages,
        max_tokens=8000,
        strategy="last",
        token_counter=len,  # Replace with actual token counter
        include_system=True,
    )
```

## 2. Multi-LLM Provider Integration

### Extended LLM Factory

**New providers:** Ollama (local), OpenRouter (gateway)

```python
# backend/app/agents/llm_factory.py
from langchain_core.language_models import BaseChatModel

def get_llm(
    provider: str,
    model: str,
    api_key: str,
    **kwargs
) -> BaseChatModel:
    """Create LLM instance based on provider.

    Supported providers:
        - anthropic: Claude models
        - openai: GPT models
        - google: Gemini models
        - ollama: Local Ollama models
        - openrouter: Multi-model gateway
        - groq: Fast inference (optional)
    """
    provider = provider.lower()

    # Existing providers
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model, api_key=api_key, **kwargs)

    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model, api_key=api_key, **kwargs)

    elif provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=model, google_api_key=api_key, **kwargs)

    # New providers for v0.2
    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=model,
            base_url=kwargs.get("base_url", "http://localhost:11434"),
            # Note: Ollama doesn't use API keys for local deployment
            **{k: v for k, v in kwargs.items() if k != "base_url"}
        )

    elif provider == "openrouter":
        from langchain_openai import ChatOpenAI
        # OpenRouter uses OpenAI-compatible API
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            **kwargs
        )

    elif provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(model=model, api_key=api_key, **kwargs)

    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider}. "
            f"Supported: anthropic, openai, google, ollama, openrouter, groq"
        )
```

### Per-Agent LLM Configuration

**Pattern:** Extend YAML config to include provider and model per agent.

```yaml
# backend/app/config/prompts.yaml (enhanced)
agents:
  onboarding:
    system_prompt: |
      You are a Data Onboarding Agent...
    max_tokens: 1500

    # New: per-agent LLM configuration
    llm:
      provider: "anthropic"
      model: "claude-sonnet-4-20250514"
      temperature: 0.7

  coding:
    system_prompt: |
      Generate Python code for data analysis...
    max_tokens: 10000

    llm:
      provider: "openrouter"
      model: "anthropic/claude-3.7-sonnet"  # OpenRouter model path
      temperature: 0.0  # Deterministic for code

  code_checker:
    system_prompt: |
      You are a Code Checker Agent...
    max_tokens: 500

    llm:
      provider: "anthropic"
      model: "claude-sonnet-4-20250514"
      temperature: 0.0

  data_analysis:
    system_prompt: |
      You are a Data Analysis Agent...
    max_tokens: 2000

    llm:
      provider: "ollama"
      model: "llama3.2:latest"  # Local Ollama model
      temperature: 0.5
      base_url: "http://localhost:11434"  # Configurable Ollama endpoint
```

### Enhanced Config Loader

```python
# backend/app/agents/config.py (enhanced)
def get_agent_llm_config(agent_name: str) -> dict:
    """Get LLM configuration for a specific agent.

    Args:
        agent_name: Name of the agent

    Returns:
        dict: LLM config with keys: provider, model, temperature, etc.
    """
    prompts = load_prompts()

    # Get agent config
    agent_config = prompts["agents"].get(agent_name, {})

    # Return LLM config with defaults
    llm_config = agent_config.get("llm", {})

    return {
        "provider": llm_config.get("provider", "anthropic"),
        "model": llm_config.get("model", "claude-sonnet-4-20250514"),
        "temperature": llm_config.get("temperature", 0.7),
        "base_url": llm_config.get("base_url"),  # For Ollama
        "max_tokens": agent_config.get("max_tokens", 2000),
    }
```

### Agent Node with Per-Node LLM

```python
# backend/app/agents/coding.py (example pattern)
async def coding_agent(state: ChatAgentState) -> dict:
    """Coding agent with per-agent LLM configuration."""

    # Load agent-specific LLM config
    llm_config = get_agent_llm_config("coding")

    # Get API key for provider
    settings = get_settings()
    api_key = get_api_key_for_provider(llm_config["provider"], settings)

    # Initialize LLM for this agent
    llm = get_llm(
        provider=llm_config["provider"],
        model=llm_config["model"],
        api_key=api_key,
        temperature=llm_config["temperature"],
        max_tokens=llm_config["max_tokens"],
        base_url=llm_config.get("base_url"),  # For Ollama
    )

    # Load system prompt
    system_prompt_template = get_agent_prompt("coding")
    system_prompt = system_prompt_template.format(
        data_profile=state["data_profile"],
        user_context=state["user_context"],
        allowed_libraries=", ".join(get_allowed_libraries()),
    )

    # Invoke LLM
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=state["user_query"]),
    ]

    response = await llm.ainvoke(messages)

    return {
        "generated_code": response.content,
    }
```

### API Key Management

```python
# backend/app/agents/utils.py
def get_api_key_for_provider(provider: str, settings: Settings) -> str:
    """Get API key for the specified provider.

    Args:
        provider: Provider name (anthropic, openai, google, openrouter, groq)
        settings: Application settings

    Returns:
        API key string (or None for Ollama)

    Raises:
        ValueError: If provider requires API key but none configured
    """
    # Ollama doesn't need API key for local deployment
    if provider == "ollama":
        return None

    key_map = {
        "anthropic": settings.anthropic_api_key,
        "openai": settings.openai_api_key,
        "google": settings.google_api_key,
        "openrouter": settings.openrouter_api_key,
        "groq": settings.groq_api_key,
    }

    api_key = key_map.get(provider)

    if not api_key:
        raise ValueError(
            f"No API key configured for provider: {provider}. "
            f"Set environment variable: {provider.upper()}_API_KEY"
        )

    return api_key
```

### Environment Variables

```bash
# .env (enhanced)
# Existing providers
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...

# New providers for v0.2
OPENROUTER_API_KEY=sk-or-...
GROQ_API_KEY=gsk_...
OLLAMA_BASE_URL=http://localhost:11434  # Optional override
```

## 3. Tool Integration (Web Search)

### Tool Definition

```python
# backend/app/agents/tools.py (new file)
from langchain_community.tools import TavilySearchResults
from langchain_community.tools import DuckDuckGoSearchResults
from typing import Literal

def get_web_search_tool(provider: Literal["tavily", "serper", "duckduckgo"] = "tavily"):
    """Get web search tool instance.

    Args:
        provider: Search provider (tavily, serper, duckduckgo)

    Returns:
        LangChain tool instance
    """
    settings = get_settings()

    if provider == "tavily":
        return TavilySearchResults(
            api_key=settings.tavily_api_key,
            max_results=5,
            search_depth="advanced",
        )

    elif provider == "serper":
        from langchain_community.utilities import GoogleSerperAPIWrapper
        from langchain_core.tools import Tool

        search = GoogleSerperAPIWrapper(
            serper_api_key=settings.serper_api_key,
            k=5,
        )

        return Tool(
            name="web_search",
            description="Search the web for current information",
            func=search.run,
        )

    elif provider == "duckduckgo":
        return DuckDuckGoSearchResults(
            max_results=5,
            # No API key needed
        )

    else:
        raise ValueError(f"Unsupported search provider: {provider}")
```

### ToolNode Integration

**Pattern:** Add ToolNode to graph for agents that need tool calling.

```python
# backend/app/agents/graph.py (enhanced)
from langgraph.prebuilt import ToolNode
from app.agents.tools import get_web_search_tool

def build_chat_graph(checkpointer=None):
    """Build and compile the chat analysis LangGraph workflow."""

    # Initialize tools
    search_tool = get_web_search_tool("tavily")
    tools = [search_tool]
    tool_node = ToolNode(tools)

    graph = StateGraph(ChatAgentState)

    # Add nodes
    graph.add_node("coding_agent", coding_agent)
    graph.add_node("code_checker", code_checker_node)
    graph.add_node("execute", execute_in_sandbox)
    graph.add_node("data_analysis", data_analysis_agent)
    graph.add_node("halt", halt_node)

    # Add tool node for data analysis agent
    graph.add_node("tools", tool_node)

    # Add edges
    graph.set_entry_point("coding_agent")
    graph.add_edge("coding_agent", "code_checker")
    graph.add_edge("execute", "data_analysis")

    # Add conditional edge for tool calling
    graph.add_conditional_edges(
        "data_analysis",
        should_call_tools,  # Routing function
        {
            "tools": "tools",
            "finish": END,
        }
    )
    graph.add_edge("tools", "data_analysis")  # Return to agent after tool use

    graph.set_finish_point("data_analysis")
    graph.set_finish_point("halt")

    compiled = graph.compile(checkpointer=checkpointer)

    return compiled

def should_call_tools(state: ChatAgentState) -> Literal["tools", "finish"]:
    """Determine if agent needs to call tools.

    Checks if last message has tool_calls.
    """
    messages = state.get("messages", [])

    if not messages:
        return "finish"

    last_message = messages[-1]

    # Check if LLM requested tool calls
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    return "finish"
```

### Agent with Tool Binding

```python
# backend/app/agents/data_analysis.py (enhanced)
async def data_analysis_agent(state: ChatAgentState) -> dict:
    """Data Analysis agent with web search tool."""

    # Load LLM config
    llm_config = get_agent_llm_config("data_analysis")
    api_key = get_api_key_for_provider(llm_config["provider"], settings)

    llm = get_llm(
        provider=llm_config["provider"],
        model=llm_config["model"],
        api_key=api_key,
        temperature=llm_config["temperature"],
    )

    # Bind tools to LLM
    tools = [get_web_search_tool("tavily")]
    llm_with_tools = llm.bind_tools(tools)

    # Load system prompt
    system_prompt_template = get_agent_prompt("data_analysis")
    system_prompt = system_prompt_template.format(
        user_query=state["user_query"],
        executed_code=state["generated_code"],
        execution_result=state["execution_result"],
    )

    # Build messages with context
    messages = [
        SystemMessage(content=system_prompt),
    ]

    # Add conversation history if available
    if state.get("messages"):
        messages.extend(state["messages"])

    # Add current query
    messages.append(HumanMessage(content="Analyze the results and provide insights."))

    # Invoke LLM (may return tool calls)
    response = await llm_with_tools.ainvoke(messages)

    # Update state with new message
    return {
        "analysis": response.content if response.content else "",
        "messages": [response],  # Will be appended by add_messages reducer
    }
```

### Tool Configuration

```yaml
# backend/app/config/tools.yaml (new file)
tools:
  web_search:
    enabled: true
    provider: "tavily"  # Options: tavily, serper, duckduckgo

    # Provider-specific settings
    tavily:
      api_key_env: "TAVILY_API_KEY"
      max_results: 5
      search_depth: "advanced"

    serper:
      api_key_env: "SERPER_API_KEY"
      max_results: 5

    duckduckgo:
      max_results: 5
      # No API key needed

  # Future tools
  calculator:
    enabled: false

  python_repl:
    enabled: false
```

## 4. SMTP Email Service Integration

### Async SMTP Service

**Library:** `aiosmtplib` for async email sending (replacing Mailgun API)

```python
# backend/app/services/email.py (rewritten)
import logging
from typing import Optional
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import Settings

logger = logging.getLogger(__name__)

async def send_password_reset_email(
    to_email: str,
    reset_link: str,
    settings: Settings
) -> bool:
    """Send password reset email via SMTP.

    Args:
        to_email: Recipient email address
        reset_link: Password reset URL with token
        settings: Application settings

    Returns:
        True if email sent successfully, False otherwise
    """
    # Check if SMTP is configured
    if not settings.smtp_host or not settings.smtp_username:
        logger.warning(
            f"SMTP not configured. Would send reset link to {to_email}: {reset_link}"
        )
        return True

    try:
        # Compose email
        message = MIMEMultipart("alternative")
        message["Subject"] = "Spectra - Password Reset Request"
        message["From"] = settings.email_from
        message["To"] = to_email

        # HTML body
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2>Password Reset Request</h2>
            <p>You requested to reset your password for your Spectra account.</p>
            <p>Click the link below to reset your password:</p>
            <p>
                <a href="{reset_link}"
                   style="display: inline-block; padding: 10px 20px;
                          background-color: #007bff; color: white;
                          text-decoration: none; border-radius: 5px;">
                    Reset Password
                </a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all;">{reset_link}</p>
            <p><strong>This link will expire in 10 minutes.</strong></p>
            <p>If you did not request this password reset, please ignore this email.</p>
            <hr>
            <p style="color: #666; font-size: 12px;">
                This is an automated email from Spectra. Please do not reply.
            </p>
        </body>
        </html>
        """

        # Attach HTML part
        html_part = MIMEText(html_body, "html")
        message.attach(html_part)

        # Send via aiosmtplib
        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password,
            use_tls=settings.smtp_use_tls,
            start_tls=settings.smtp_start_tls,
        )

        logger.info(f"Password reset email sent to {to_email} via SMTP")
        return True

    except Exception as e:
        logger.error(f"Error sending password reset email via SMTP: {e}")
        return False
```

### SMTP Configuration

```python
# backend/app/config.py (add SMTP settings)
class Settings(BaseSettings):
    # ... existing settings ...

    # SMTP settings (new for v0.2)
    smtp_host: str = Field(default="", env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_username: str = Field(default="", env="SMTP_USERNAME")
    smtp_password: str = Field(default="", env="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=True, env="SMTP_USE_TLS")
    smtp_start_tls: bool = Field(default=True, env="SMTP_START_TLS")
    email_from: str = Field(default="noreply@spectra.com", env="EMAIL_FROM")
```

### Environment Variables

```bash
# .env (SMTP settings)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
SMTP_START_TLS=true
EMAIL_FROM=noreply@spectra.com
```

## Data Flow Changes

### Request Flow with Memory

```
[User sends query via SSE endpoint]
    ↓
[Endpoint constructs thread_id: user_{id}_file_{file_id}]
    ↓
[Graph.astream(initial_state, config={"configurable": {"thread_id": ...}})]
    ↓
[AsyncPostgresSaver loads checkpoint for thread_id]
    ↓
[Graph executes nodes with restored state + new query]
    ↓
    ┌──────────────────────────────────────┐
    │ Node 1: coding_agent                 │
    │ - Loads agent-specific LLM (YAML)   │
    │ - Invokes LLM with context           │
    │ - Returns {generated_code: "..."}   │
    └──────────────────────────────────────┘
    ↓ [AsyncPostgresSaver saves checkpoint]
    ┌──────────────────────────────────────┐
    │ Node 2: code_checker                 │
    │ - Loads agent-specific LLM (YAML)   │
    │ - Validates code                     │
    │ - Returns routing Command            │
    └──────────────────────────────────────┘
    ↓ [AsyncPostgresSaver saves checkpoint]
    ┌──────────────────────────────────────┐
    │ Node 3: execute                      │
    │ - Runs code in E2B sandbox           │
    │ - Returns {execution_result: "..."}  │
    └──────────────────────────────────────┘
    ↓ [AsyncPostgresSaver saves checkpoint]
    ┌──────────────────────────────────────┐
    │ Node 4: data_analysis                │
    │ - Loads agent-specific LLM (YAML)   │
    │ - Binds web search tool              │
    │ - Invokes LLM (may call tool)        │
    │ - Returns {analysis: "...", messages}│
    └──────────────────────────────────────┘
    ↓ [AsyncPostgresSaver saves final checkpoint]
[SSE stream completes]
    ↓
[Next query loads checkpoint and continues conversation]
```

### State Management with Reducers

**Key insight:** `add_messages` reducer enables message appending instead of overwriting.

```python
# State update example
state_before = {
    "messages": [
        SystemMessage("You are an analyst"),
        HumanMessage("What is the average?"),
        AIMessage("The average is 42"),
    ],
    "user_query": "What is the average?",
}

# Node returns new message
node_output = {
    "messages": [HumanMessage("Now show the max")],
    "user_query": "Now show the max",
}

# With add_messages reducer, messages are appended
state_after = {
    "messages": [
        SystemMessage("You are an analyst"),
        HumanMessage("What is the average?"),
        AIMessage("The average is 42"),
        HumanMessage("Now show the max"),  # Appended, not replaced
    ],
    "user_query": "Now show the max",  # Overwritten (no reducer)
}
```

## Integration Points

### New Components

| Component | Purpose | Dependencies | File Location |
|-----------|---------|--------------|---------------|
| AsyncPostgresSaver | Memory persistence | psycopg-pool, langgraph-checkpoint-postgres | `app/main.py` (lifespan) |
| AsyncConnectionPool | DB connection pooling | psycopg-pool | `app/main.py` (lifespan) |
| Enhanced LLM factory | Multi-provider support | langchain-ollama, langchain-openai (for OpenRouter) | `app/agents/llm_factory.py` |
| Per-agent config loader | Load LLM config from YAML | PyYAML | `app/agents/config.py` |
| Tool definitions | Web search tools | langchain-community | `app/agents/tools.py` (new) |
| ToolNode | Execute tools in graph | langgraph.prebuilt | `app/agents/graph.py` |
| Async SMTP service | Email sending | aiosmtplib | `app/services/email.py` |
| Context window trimmer | Message history management | langchain-core | `app/agents/utils.py` (new) |

### Modified Components

| Component | Change | Reason |
|-----------|--------|--------|
| `graph.py` | Add checkpointer parameter to build_chat_graph() | Enable memory |
| `graph.py` | Add ToolNode and conditional edges | Enable tool calling |
| `state.py` | Add `Annotated[list, add_messages]` to messages field | Enable message appending |
| `config.py` | Add get_agent_llm_config() function | Per-agent LLM config |
| `prompts.yaml` | Add llm section per agent | Per-agent provider/model |
| Agent nodes | Load LLM from config, not global settings | Per-agent LLM support |
| Agent nodes | Add tool binding for relevant agents | Tool integration |
| `main.py` | Add lifespan function for connection pool | Memory initialization |
| Chat endpoint | Pass checkpointer to build_chat_graph(), add thread_id to config | Memory persistence |
| `email.py` | Replace Mailgun API with aiosmtplib | SMTP integration |

## Build Order (Dependency-Aware)

### Phase 1: Memory Foundation
1. **Install dependencies**: `langgraph-checkpoint-postgres`, `psycopg-pool`
2. **Add state reducer**: Modify `state.py` to add `Annotated[list, add_messages]`
3. **Create lifespan function**: Initialize AsyncConnectionPool and AsyncPostgresSaver
4. **Update graph compilation**: Pass checkpointer to `build_chat_graph()`
5. **Update endpoints**: Add thread_id to config, pass checkpointer
6. **Test**: Verify checkpoints are created in PostgreSQL

### Phase 2: Multi-LLM Support
1. **Install dependencies**: `langchain-ollama`
2. **Extend LLM factory**: Add Ollama and OpenRouter providers
3. **Enhance YAML config**: Add llm section per agent in `prompts.yaml`
4. **Create config loader**: Add `get_agent_llm_config()` function
5. **Update agent nodes**: Load LLM from config instead of global settings
6. **Add environment variables**: `OPENROUTER_API_KEY`, `OLLAMA_BASE_URL`
7. **Test**: Verify each agent uses configured provider

### Phase 3: Tool Integration
1. **Install dependencies**: `langchain-community`, `tavily-python` (or `google-search-results`)
2. **Create tool definitions**: Add `tools.py` with web search tool
3. **Add ToolNode to graph**: Import and initialize ToolNode
4. **Add conditional routing**: Add should_call_tools() function
5. **Bind tools to agents**: Update data_analysis agent to bind tools
6. **Add tool config**: Create `tools.yaml` with provider settings
7. **Test**: Verify agent can call web search tool

### Phase 4: SMTP Email
1. **Install dependencies**: `aiosmtplib`
2. **Rewrite email service**: Replace Mailgun API with aiosmtplib
3. **Add SMTP settings**: Update `config.py` with SMTP fields
4. **Update environment**: Add SMTP variables to `.env`
5. **Test**: Send test email via SMTP

### Phase 5: Context Window Management
1. **Create utils module**: Add `trim_messages()` wrapper
2. **Add context window config**: Create `memory.yaml` with limits
3. **Update agent nodes**: Call trim_messages() before LLM invocation
4. **Test**: Verify message history is trimmed

## Migration Strategy

### Backward Compatibility

**Goal:** v0.2 changes should not break v0.1 functionality.

| Feature | v0.1 Behavior | v0.2 Behavior | Compatibility Strategy |
|---------|---------------|---------------|------------------------|
| Memory | Disabled (checkpointer=None) | Enabled (AsyncPostgresSaver) | Graceful: graph works with or without checkpointer |
| LLM provider | Global setting (all agents use same) | Per-agent config (YAML) | Default: if no llm config in YAML, fall back to global |
| Tools | Not used | data_analysis agent has tools | Additive: other agents unchanged |
| Email | Mailgun API (dev mode logs) | SMTP (aiosmtplib) | Config-based: if no SMTP settings, log to console |

### Rollout Plan

1. **Deploy memory first**: Enables conversation context (high value)
2. **Deploy multi-LLM second**: Enables cost optimization and experimentation
3. **Deploy tools third**: Enables web search (additive feature)
4. **Deploy SMTP last**: Production email (replaces dev mode)

## Architectural Patterns to Follow

### Pattern 1: Agent-Agnostic Tool Binding

**What:** Bind tools at graph-level, not hard-coded in agent nodes.

**Why:** Makes it easy to add/remove tools without changing agent code.

**Implementation:**
```python
# Good: tools configured at graph level
tools = [get_web_search_tool("tavily")]
llm_with_tools = llm.bind_tools(tools)

# Bad: hard-coded tool binding in agent
llm_with_tools = llm.bind_tools([TavilySearchResults(api_key="...")])
```

### Pattern 2: Config-Driven LLM Selection

**What:** LLM provider and model come from YAML, not code.

**Why:** Enables experimentation without code changes.

**Implementation:**
```python
# Good: config-driven
llm_config = get_agent_llm_config("coding")
llm = get_llm(provider=llm_config["provider"], model=llm_config["model"], ...)

# Bad: hard-coded provider
llm = ChatAnthropic(model="claude-sonnet-4-20250514", ...)
```

### Pattern 3: Lifespan Resource Management

**What:** Initialize connection pools in FastAPI lifespan, not per-request.

**Why:** Connection pooling is expensive; should be shared across requests.

**Implementation:**
```python
# Good: lifespan manages pool
@asynccontextmanager
async def lifespan(app):
    pool = AsyncConnectionPool(...)
    await pool.open()
    app.state.pool = pool
    yield
    await pool.close()

# Bad: per-request pool creation
async def endpoint():
    pool = AsyncConnectionPool(...)  # Creates new pool every request
```

### Pattern 4: Graceful Degradation

**What:** Features work even if optional components are missing.

**Why:** Makes deployment flexible and testing easier.

**Implementation:**
```python
# Good: graceful fallback
if not settings.smtp_host:
    logger.warning("SMTP not configured, logging to console")
    return True

# Bad: crash if not configured
await aiosmtplib.send(...)  # Crashes if SMTP not configured
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Synchronous DB Operations in Async Context

**What:** Using PostgresSaver (sync) instead of AsyncPostgresSaver in async FastAPI.

**Why:** Blocks event loop, causes poor performance and potential deadlocks.

**Instead:**
```python
# Good: async checkpointer
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
checkpointer = AsyncPostgresSaver(async_pool)

# Bad: sync checkpointer in async app
from langgraph.checkpoint.postgres import PostgresSaver
checkpointer = PostgresSaver(sync_conn)  # Blocks event loop
```

### Anti-Pattern 2: Unbounded Message History

**What:** Storing all messages without trimming, causing context overflow.

**Why:** Exceeds model context limits, increases latency and cost.

**Instead:**
```python
# Good: trim messages
from langchain_core.messages import trim_messages
messages = trim_messages(state["messages"], max_tokens=8000)

# Bad: pass all messages
messages = state["messages"]  # Can exceed context limit
```

### Anti-Pattern 3: API Keys in Code

**What:** Hard-coding API keys or putting them in YAML config files.

**Why:** Security risk if code is committed to git.

**Instead:**
```python
# Good: environment variables
api_key = settings.tavily_api_key  # Loaded from .env

# Bad: hard-coded in YAML
tavily:
  api_key: "tvly-abc123..."  # Committed to git
```

### Anti-Pattern 4: Global LLM Instance

**What:** Creating single LLM instance shared by all agents.

**Why:** Prevents per-agent configuration (provider, model, temperature).

**Instead:**
```python
# Good: per-agent LLM
async def coding_agent(state):
    llm = get_llm(**get_agent_llm_config("coding"))
    ...

# Bad: global LLM
LLM = ChatAnthropic(...)  # All agents use same LLM
```

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-100 users | Single server, local Ollama optional, default PostgreSQL pool (min=2, max=10) |
| 100-1k users | Increase pool size (max=50), add Redis for session caching, separate Ollama to dedicated server |
| 1k-10k users | Add connection pooler (PgBouncer), horizontal scaling of FastAPI workers, CDN for static assets, consider managed Ollama (e.g., Replicate) |
| 10k+ users | Multi-region deployment, read replicas for PostgreSQL, async task queue for tool calls, LLM gateway for rate limiting and caching |

### First Bottleneck: Database Connections

**Symptom:** Connection pool exhaustion under load

**Solution:**
1. Increase AsyncConnectionPool max_size
2. Add PgBouncer for connection pooling
3. Monitor `checkpoints` table size, implement TTL cleanup

### Second Bottleneck: LLM API Rate Limits

**Symptom:** 429 errors from LLM providers

**Solution:**
1. Implement retry with exponential backoff
2. Add LLM gateway (LiteLLM, OpenRouter) for fallback routing
3. Cache LLM responses for identical queries
4. Use faster models (Groq, OpenRouter) for non-critical agents

## Dependencies

### New Packages for v0.2

```toml
# pyproject.toml or requirements.txt

# Memory persistence
langgraph-checkpoint-postgres = "^2.0"
psycopg = {extras = ["pool"], version = "^3.2"}
psycopg-pool = "^3.2"

# Multi-LLM support
langchain-ollama = "^0.2"
# OpenRouter uses langchain-openai with custom base_url

# Tool integration
langchain-community = "^0.3"
tavily-python = "^0.5"  # or google-search-results for Serper

# SMTP email
aiosmtplib = "^3.0"
```

## Sources

**Memory Persistence:**
- [Simple LangGraph Implementation with Memory AsyncSqliteSaver Checkpointer — FastAPI](https://medium.com/@devwithll/simple-langgraph-implementation-with-memory-asyncsqlitesaver-checkpointer-fastapi-54f4e4879a2e)
- [langgraph-checkpoint-postgres · PyPI](https://pypi.org/project/langgraph-checkpoint-postgres/)
- [Internals of Langgraph Postgres Checkpointer (AsyncPostgresSaver)](https://blog.lordpatil.com/posts/langgraph-postgres-checkpointer/)
- [Understanding Memory Management in LangGraph: A Practical Guide](https://pub.towardsai.net/understanding-memory-management-in-langgraph-a-practical-guide-for-genai-students-b3642c9ea7e1)
- [Mastering LangGraph Checkpointing: Best Practices for 2025](https://sparkco.ai/blog/mastering-langgraph-checkpointing-best-practices-for-2025)

**Multi-LLM Support:**
- [Build a Multi-LLM AI Agent with Kong AI Gateway & LangGraph](https://konghq.com/blog/engineering/build-a-multi-llm-ai-agent-with-kong-ai-gateway-and-langgraph)
- [LangGraph: Multi-Agent Workflows](https://blog.langchain.com/langgraph-multi-agent-workflows/)
- [ChatOllama integration - Docs by LangChain](https://docs.langchain.com/oss/python/integrations/chat/ollama)
- [LangChain Integration | OpenRouter SDK Support](https://openrouter.ai/docs/guides/community/langchain)
- [OpenRouter with LangChain](https://medium.com/@arth2048/openrouter-with-langchain-0eab702b9977)

**State Management:**
- [LangGraph Notes: State Management](https://medium.com/@omeryalcin48/langgraph-notes-state-management-62ea5b5a5cdd)
- [Building AI Agents Using LangGraph: Part 8 — Understanding Reducers and State Updates](https://harshaselvi.medium.com/building-ai-agents-using-langgraph-part-8-understanding-reducers-and-state-updates-c8056963a42c)
- [Mastering LangGraph State Management in 2025](https://sparkco.ai/blog/mastering-langgraph-state-management-in-2025)

**Tool Integration:**
- [Building Tool Calling Agents with LangGraph: A Complete Guide](https://sangeethasaravanan.medium.com/building-tool-calling-agents-with-langgraph-a-complete-guide-ebdcdea8f475)
- [Tavily search integration - Docs by LangChain](https://docs.langchain.com/oss/javascript/integrations/tools/tavily_search)
- [Adding tools to your LangGraph Chatbots | Beginner's Guide](https://www.codersarts.com/post/adding-tools-to-your-langgraph-chatbots-beginner-s-guide)

**SMTP Email:**
- [aiosmtplib · PyPI](https://pypi.org/project/aiosmtplib/)
- [GitHub - cole/aiosmtplib: asyncio smtplib implementation](https://github.com/cole/aiosmtplib)
- [Sending Emails with Python FastAPI: A Quick Guide](https://mailmug.net/blog/fastapi-mail/)

**Connection Pooling:**
- [psycopg_pool – Connection pool implementations](https://www.psycopg.org/psycopg3/docs/api/pool.html)
- [asyncpg Usage — asyncpg Documentation](https://magicstack.github.io/asyncpg/current/usage.html)
- [Asynchronous Postgres with Python, FastAPI, and Psycopg 3](https://medium.com/@benshearlaw/asynchronous-postgres-with-python-fastapi-and-psycopg-3-fafa5faa2c08)

---
*Architecture research for: Spectra v0.2 Intelligence & Integration*
*Researched: 2026-02-06*
