# Phase 8: Session Memory with PostgreSQL Checkpointing - Research

**Researched:** 2026-02-07
**Domain:** LangGraph session persistence, PostgreSQL checkpointing, conversation memory management
**Confidence:** HIGH

## Summary

Phase 8 implements multi-turn conversation memory within chat tabs using LangGraph's PostgreSQL checkpointing system. The codebase already has `langgraph-checkpoint-postgres>=2.0.0` installed and has placeholder code for checkpointing (currently disabled at line 469 in `graph.py`). This phase enables that functionality and adds token-aware context window management.

LangGraph's `AsyncPostgresSaver` provides production-grade state persistence using the existing PostgreSQL database. Each file tab gets a unique `thread_id` (already implemented as `f"file_{file_id}_user_{user_id}"`), and the checkpointer automatically maintains conversation history across queries. Token counting requires provider-specific libraries (tiktoken for OpenAI, Anthropic's official API for Claude), and message trimming uses LangGraph's built-in `trim_messages` utility with the `add_messages` reducer.

The existing `chat_messages` table serves as the application-level message history (for UI display and persistence beyond tab closure), while LangGraph's checkpointer tables (`checkpoints`, `checkpoint_blobs`, `checkpoint_writes`) handle agent state persistence during active sessions. The two systems work in parallel: checkpointer enables multi-turn agent memory, while chat_messages provides durable cross-session storage.

**Primary recommendation:** Enable `AsyncPostgresSaver` in the existing graph initialization, add a state reducer for message accumulation, implement token counting using provider-specific libraries, create frontend warning dialogs with `beforeunload` events, and add configurable context window settings.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| langgraph-checkpoint-postgres | >=2.0.0 | PostgreSQL-backed checkpoint persistence | Official LangGraph production checkpointer, already installed |
| psycopg[binary,pool] | >=3.0 | Async PostgreSQL driver | Required by AsyncPostgresSaver, supports connection pooling |
| langchain-core | >=0.3.0 | Message types, reducers, utilities | Core LangChain primitives (already installed) |
| tiktoken | latest | Token counting for OpenAI models | Official OpenAI tokenizer library |
| anthropic | latest | Token counting for Claude models | Official Anthropic SDK with `count_tokens()` API |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| react-beforeunload | ^2.6.0 | Browser tab close warning | Simplifies beforeunload event handling in React |
| zustand | >=5.0.11 | Frontend state for session metadata | Already installed, can store token usage state |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| AsyncPostgresSaver | SQLite checkpointer | PostgreSQL already in use, supports concurrent access |
| Provider-specific token counting | Universal approximation (tiktoken for all) | Inaccurate counts for non-OpenAI models (Claude uses different tokenizer) |
| react-beforeunload | Manual `window.addEventListener` | More boilerplate, easy to implement wrong |

**Installation:**
```bash
# Backend (most already installed)
pip install tiktoken anthropic

# Frontend
npm install react-beforeunload
```

## Architecture Patterns

### Recommended Project Structure
```
backend/app/
├── agents/
│   ├── graph.py              # Enable AsyncPostgresSaver here
│   ├── state.py              # Add message reducer with add_messages
│   └── memory/               # NEW: Token counting, trimming utilities
│       ├── __init__.py
│       ├── token_counter.py  # Provider-agnostic token counting
│       └── trimmer.py        # Message trimming with user confirmation
├── config.py                 # Add context_window_tokens, context_warning_threshold
├── main.py                   # Add checkpointer setup in lifespan context
└── routers/
    └── chat.py               # Add /context-usage endpoint

frontend/src/
├── hooks/
│   └── useTabCloseWarning.ts # NEW: beforeunload warning hook
├── stores/
│   └── tabStore.ts           # Add context usage tracking
└── components/
    └── chat/
        ├── ContextWarning.tsx # NEW: 85% context usage warning
        └── TabCloseDialog.tsx # NEW: Confirm tab close dialog
```

### Pattern 1: Enable AsyncPostgresSaver with Lifespan Management

**What:** Initialize PostgreSQL checkpointer in FastAPI's lifespan context to ensure proper connection management and table setup.

**When to use:** Always for production checkpointing with async FastAPI applications.

**Example:**
```python
# app/main.py (based on official docs + FastAPI best practices)
from contextlib import asynccontextmanager
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage AsyncPostgresSaver lifecycle."""
    settings = get_settings()

    # Create async connection pool
    async with AsyncConnectionPool(
        conninfo=settings.database_url,
        max_size=10,
        kwargs={"autocommit": True, "row_factory": dict_row}
    ) as pool:
        # Initialize checkpointer
        async with AsyncPostgresSaver(pool) as checkpointer:
            # Create checkpoint tables if needed
            await checkpointer.setup()

            # Store in app state for request handlers
            app.state.checkpointer = checkpointer

            yield  # Application runs here

    # Cleanup happens automatically via context managers

app = FastAPI(lifespan=lifespan)
```

**Critical details:**
- `autocommit=True` required for `.setup()` to persist tables
- `row_factory=dict_row` required for PostgresSaver's dict-style row access
- Use `async with` to ensure proper connection cleanup
- Store checkpointer in `app.state`, not as module-level global

### Pattern 2: Add Message Reducer to State for Accumulation

**What:** Configure `ChatAgentState` with `add_messages` reducer to accumulate conversation history across graph invocations.

**When to use:** Required for multi-turn conversations with checkpointing.

**Example:**
```python
# app/agents/state.py
from typing import Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class ChatAgentState(TypedDict):
    # ... existing fields ...

    # Replace this line:
    # messages: list

    # With annotated field using add_messages reducer:
    messages: Annotated[list[AnyMessage], add_messages]
    """Accumulated conversation history with automatic deduplication."""
```

**Why it matters:** Without the reducer, `messages` gets overwritten on each node update. With `add_messages`, LangGraph merges new messages into existing history, enabling context accumulation.

### Pattern 3: Provider-Agnostic Token Counting

**What:** Abstract token counting behind a unified interface that delegates to provider-specific implementations.

**When to use:** When supporting multiple LLM providers with different tokenization schemes.

**Example:**
```python
# app/agents/memory/token_counter.py
from typing import Protocol
from langchain_core.messages import BaseMessage
import tiktoken
from anthropic import Anthropic

class TokenCounter(Protocol):
    def count_messages(self, messages: list[BaseMessage]) -> int: ...

class OpenAITokenCounter:
    def __init__(self, model: str = "gpt-4"):
        self.encoding = tiktoken.encoding_for_model(model)

    def count_messages(self, messages: list[BaseMessage]) -> int:
        """Count tokens using tiktoken (OpenAI's official tokenizer)."""
        total = 0
        for msg in messages:
            # Format: role + content + message overhead
            total += len(self.encoding.encode(f"{msg.type}: {msg.content}"))
            total += 4  # Message formatting overhead
        return total

class AnthropicTokenCounter:
    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self.client = Anthropic()
        self.model = model

    def count_messages(self, messages: list[BaseMessage]) -> int:
        """Count tokens using Anthropic's official API."""
        # Convert to Anthropic message format
        formatted = [{"role": m.type, "content": m.content} for m in messages]
        result = self.client.messages.count_tokens(
            model=self.model,
            messages=formatted
        )
        return result.input_tokens

def get_token_counter(provider: str, model: str) -> TokenCounter:
    """Factory function for provider-specific counters."""
    if provider == "openai":
        return OpenAITokenCounter(model)
    elif provider == "anthropic":
        return AnthropicTokenCounter(model)
    elif provider == "ollama":
        # Ollama models often use OpenAI-compatible tokenization
        return OpenAITokenCounter("gpt-4")  # Approximation
    else:
        # Fallback: use OpenAI's tokenizer as approximation
        return OpenAITokenCounter("gpt-4")
```

**Important:** Anthropic's token counting requires an API call. For performance, only count when approaching limits (85% threshold) or when explicitly requested by user.

### Pattern 4: Message Trimming with User Confirmation

**What:** Trim oldest messages when context window approaches limit, requiring user opt-in per MEMORY-07.

**When to use:** When token count exceeds configurable threshold (default: 85% of context window).

**Example:**
```python
# app/agents/memory/trimmer.py
from langchain_core.messages import trim_messages, RemoveMessage
from typing import List
from langchain_core.messages import BaseMessage

async def trim_if_needed(
    messages: list[BaseMessage],
    max_tokens: int,
    token_counter: TokenCounter,
    user_confirmed: bool = False
) -> tuple[list[BaseMessage], bool]:
    """Trim messages if token limit exceeded.

    Returns:
        (trimmed_messages, needs_confirmation)
    """
    current_tokens = token_counter.count_messages(messages)

    if current_tokens <= max_tokens:
        return messages, False

    # User needs to confirm trimming
    if not user_confirmed:
        return messages, True  # Signal frontend to show confirmation

    # User confirmed - perform trimming
    trimmed = trim_messages(
        messages,
        max_tokens=max_tokens,
        strategy="last",  # Keep most recent messages
        token_counter=lambda msgs: token_counter.count_messages(msgs),
        start_on="human",  # Start with user message
        end_on=("human", "tool"),  # End on valid boundary
        include_system=True  # Always preserve system prompt
    )

    return trimmed, False
```

**Key parameters:**
- `strategy="last"`: Keep most recent messages (discards oldest first)
- `start_on="human"`: Ensure conversation starts with user message (LLM requirement)
- `end_on=("human", "tool")`: Valid message boundaries for most models
- `include_system=True`: Preserve system prompt regardless of trimming

### Pattern 5: Frontend Tab Close Warning

**What:** Show browser-native confirmation dialog when user attempts to close tab with active conversation context.

**When to use:** Always for tabs with accumulated conversation history (more than 1 message pair).

**Example:**
```typescript
// frontend/src/hooks/useTabCloseWarning.ts
import { useEffect } from 'react';
import { useBeforeunload } from 'react-beforeunload';

export function useTabCloseWarning(hasContext: boolean) {
  useBeforeunload((event) => {
    if (hasContext) {
      // Modern browsers require returnValue to be set
      event.preventDefault();
      event.returnValue = '';  // Empty string (browser shows generic message)
    }
  });
}

// Usage in chat component
function ChatTab({ fileId }: { fileId: string }) {
  const messages = useChatHistory(fileId);
  const hasContext = messages.length > 2;  // More than greeting

  useTabCloseWarning(hasContext);

  return <div>...</div>;
}
```

**Important browser behavior:** Modern browsers (2024+) only show generic confirmation text. Custom messages are ignored for security reasons.

### Anti-Patterns to Avoid

- **Creating graph inside async with block:** Never wrap `graph = builder.compile()` in `async with AsyncPostgresSaver.from_conn_string()` inside request handlers. Graph should be compiled once at startup and reused across requests.

- **Forgetting autocommit=True:** Without `autocommit=True`, the `.setup()` method's table creation is not committed to the database, causing "table does not exist" errors.

- **Using global checkpointer without lifecycle management:** Module-level `checkpointer = AsyncPostgresSaver(...)` creates connection that never closes. Always use FastAPI's lifespan context.

- **Token counting on every message:** Don't count tokens after every message. Only check when:
  1. User requests context usage display
  2. Approaching threshold (check every 5 messages)
  3. Before trimming operation

- **Hardcoding thread_id format:** Don't use `thread_id = f"session_{uuid}"`. Use existing pattern `f"file_{file_id}_user_{user_id}"` for proper isolation per file tab.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Message deduplication | Custom message ID tracking | `add_messages` reducer | Handles message merging, deduplication by ID, replacement by role |
| Token counting | Naive character/word count | Provider-specific libraries (tiktoken, Anthropic SDK) | Tokenization is model-specific; approximations cause over/under-counting |
| Message trimming | Manual message slicing | `trim_messages` utility | Respects message boundaries, model-specific rules (e.g., start on human) |
| Checkpoint table schema | Custom state storage tables | `AsyncPostgresSaver.setup()` | Creates optimized schema with indexes, handles migrations |
| Browser close detection | Custom visibility/focus listeners | `beforeunload` event | Standard browser API for tab close, guaranteed to fire |

**Key insight:** LangGraph's checkpointing system is battle-tested for agent state persistence. Custom solutions miss edge cases like:
- Message deduplication when nodes retry
- Proper checkpoint versioning for time-travel debugging
- Connection pool exhaustion under concurrent load
- Token counting differences between model families
- Browser compatibility for close warnings

## Common Pitfalls

### Pitfall 1: Missing `.setup()` Call on First Run

**What goes wrong:** Application crashes with "relation 'checkpoints' does not exist" error when trying to save first checkpoint.

**Why it happens:** `AsyncPostgresSaver` requires checkpoint tables (`checkpoints`, `checkpoint_blobs`, `checkpoint_writes`) to exist. These are not created by Alembic migrations - they're created by the checkpointer itself.

**How to avoid:** Call `await checkpointer.setup()` once during application startup (lifespan context). This is idempotent - safe to call every time.

**Warning signs:**
- Postgres error mentioning missing relations
- Works fine after manually running `setup()` in Python REPL
- Fresh database deployments fail, but existing deployments work

**Code fix:**
```python
# app/main.py - lifespan context
async with AsyncPostgresSaver(pool) as checkpointer:
    await checkpointer.setup()  # ADD THIS LINE
    app.state.checkpointer = checkpointer
    yield
```

### Pitfall 2: Forgetting `autocommit=True` in Connection Config

**What goes wrong:** `.setup()` appears to succeed, but tables are not actually created. Subsequent checkpoint saves fail with "table does not exist."

**Why it happens:** PostgreSQL transactions require explicit `COMMIT` to persist changes. Without `autocommit=True`, the `CREATE TABLE` statements in `.setup()` are rolled back when the connection context exits.

**How to avoid:** Always include `autocommit=True` when creating connection pools or connections for `AsyncPostgresSaver`:

```python
async with AsyncConnectionPool(
    conninfo=db_uri,
    kwargs={"autocommit": True, "row_factory": dict_row}  # REQUIRED
) as pool:
    async with AsyncPostgresSaver(pool) as checkpointer:
        await checkpointer.setup()
```

**Warning signs:**
- `.setup()` returns without errors
- `\dt` in psql shows no checkpoint tables
- Checkpoint saves fail with "relation does not exist"
- Tables appear temporarily during `.setup()` but disappear after

### Pitfall 3: Graph Compilation Inside Request Handler

**What goes wrong:** Each request creates a new graph instance, losing module-level caching. Worse, if using `async with AsyncPostgresSaver.from_conn_string()` inside handler, connections are never closed, causing connection pool exhaustion.

**Why it happens:** Developers follow documentation examples that show complete setup in one function, forgetting that FastAPI request handlers run hundreds of times.

**How to avoid:** Compile graph once at startup and store in `app.state`:

```python
# ❌ WRONG - compiles graph on every request
@router.post("/chat")
async def chat(request: Request):
    async with AsyncPostgresSaver.from_conn_string(db_uri) as checkpointer:
        graph = builder.compile(checkpointer=checkpointer)  # BAD
        result = await graph.ainvoke(...)
    return result

# ✅ CORRECT - use pre-compiled graph from app.state
@router.post("/chat")
async def chat(request: Request):
    graph = get_or_create_graph(request.app.state.checkpointer)  # GOOD
    result = await graph.ainvoke(...)
    return result
```

**Warning signs:**
- Connection pool errors after ~100 requests
- Graph compilation takes 100-500ms per request
- Memory usage grows continuously
- Database shows hundreds of idle connections

### Pitfall 4: Using Injected DB Session for Long-Running Streams

**What goes wrong:** After 30-120 seconds of streaming, database write fails with "connection already closed" or "connection lost during query."

**Why it happens:** The injected `db: AsyncSession` from `Depends(get_db)` is scoped to the HTTP request. For long-running SSE streams, the session's underlying connection may timeout or be closed by the connection pool while the stream is still active.

**How to avoid:** Create a fresh session via `async_session_maker()` when saving to database after stream completes (this pattern is already implemented at line 365 in `agent_service.py`):

```python
# ✅ CORRECT (from agent_service.py line 365)
async with async_session_maker() as save_db:
    await ChatService.create_message(save_db, file_id, user_id, ...)
```

**Warning signs:**
- Intermittent "connection closed" errors after long streams
- Works for short queries (<30s) but fails for complex ones (>2min)
- Error messages mention "MissingGreenlet" or connection pool state

**Note:** This is already handled correctly in the existing codebase's streaming implementation.

### Pitfall 5: Token Count Mismatch Between Providers

**What goes wrong:** User sees "85% context used" warning with 10,200 OpenAI tokens, but Anthropic's Claude model actually accepts 200,000 tokens. Or vice versa - counting with OpenAI's tokenizer for Anthropic model underestimates by 20-30%.

**Why it happens:** Each LLM family uses different tokenization:
- OpenAI: tiktoken (BPE-based)
- Anthropic: Custom tokenizer (count via API)
- Ollama: Varies by model (llama.cpp, etc.)

**How to avoid:** Use provider-specific token counting based on the current agent's LLM configuration:

```python
# app/agents/memory/token_counter.py
def get_token_counter(provider: str, model: str) -> TokenCounter:
    if provider == "anthropic":
        return AnthropicTokenCounter(model)  # Use Anthropic API
    elif provider == "openai":
        return OpenAITokenCounter(model)  # Use tiktoken
    else:
        # Fallback to approximation with warning
        logger.warning(f"No exact tokenizer for {provider}, using approximation")
        return OpenAITokenCounter("gpt-4")
```

**Warning signs:**
- Context warning triggers too early/late
- User complains "I was warned at 50% but could continue to 100%"
- Token counts don't match LangSmith/LangFuse traces
- Different counts for same messages when switching providers

### Pitfall 6: Not Updating State Reducer When Adding Messages Key

**What goes wrong:** After adding `messages: Annotated[list[AnyMessage], add_messages]` to state, old messages are still overwritten instead of accumulated.

**Why it happens:** Forgot to update the initial state creation in `agent_service.py` to use `[]` instead of constructing message list directly. Or, the graph is cached and needs to be recreated.

**How to avoid:**
1. Add reducer annotation to state class:
   ```python
   messages: Annotated[list[AnyMessage], add_messages]
   ```

2. Initialize as empty list in initial state:
   ```python
   initial_state = {
       # ...
       "messages": [],  # Reducer will accumulate here
   }
   ```

3. Recreate the graph or restart server to clear cached graph instance.

**Warning signs:**
- Second query doesn't see first query's context
- `state.values["messages"]` only contains latest exchange
- LangSmith traces show state being overwritten, not merged

### Pitfall 7: Browser beforeunload Warning Not Showing

**What goes wrong:** Tab closes immediately without confirmation dialog, despite `beforeunload` listener being registered.

**Why it happens:**
- Browser only shows dialog if page has user interaction (security feature)
- Event listener added after user tried to close tab
- `event.preventDefault()` or `event.returnValue` not set correctly

**How to avoid:**
```typescript
// Ensure both preventDefault AND returnValue are set
useBeforeunload((event) => {
  if (hasContext) {
    event.preventDefault();  // Required in modern browsers
    event.returnValue = '';  // Must be empty string (spec requirement)
  }
});
```

**Warning signs:**
- Works in development, fails in production (React Strict Mode difference)
- Works in Chrome, fails in Firefox (browser differences)
- Works when navigating between pages, fails on tab close
- Console shows "beforeunload listener blocked" warning

## Code Examples

Verified patterns from official sources and existing codebase:

### Enable Checkpointing in Graph Initialization

```python
# app/main.py - Add to lifespan context
from contextlib import asynccontextmanager
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    # Create async connection pool for checkpointer
    async with AsyncConnectionPool(
        conninfo=settings.database_url,
        max_size=10,
        kwargs={"autocommit": True, "row_factory": dict_row}
    ) as pool:
        # Initialize checkpointer
        async with AsyncPostgresSaver(pool) as checkpointer:
            await checkpointer.setup()
            app.state.checkpointer = checkpointer
            yield

app = FastAPI(lifespan=lifespan)
```

**Source:** [LangGraph Persistence Documentation](https://docs.langchain.com/oss/python/langgraph/persistence)

### Update Graph Builder to Use Checkpointer

```python
# app/agents/graph.py - Modify build_chat_graph()
def build_chat_graph(checkpointer):
    """Build graph with PostgreSQL checkpointing enabled."""
    graph = StateGraph(ChatAgentState)

    # Add nodes (existing code)
    graph.add_node("coding_agent", coding_agent)
    graph.add_node("code_checker", code_checker_node)
    graph.add_node("execute", execute_in_sandbox)
    graph.add_node("data_analysis", data_analysis_agent)
    graph.add_node("halt", halt_node)

    # Add edges (existing code)
    graph.set_entry_point("coding_agent")
    graph.add_edge("coding_agent", "code_checker")
    graph.add_edge("execute", "data_analysis")
    graph.set_finish_point("data_analysis")
    graph.set_finish_point("halt")

    # Compile WITH checkpointer (replace line 469-490)
    compiled = graph.compile(checkpointer=checkpointer)
    return compiled

# Modify get_or_create_graph to accept checkpointer
def get_or_create_graph(checkpointer):
    global _cached_graph
    if _cached_graph is None:
        _cached_graph = build_chat_graph(checkpointer)
    return _cached_graph
```

**Source:** Existing codebase + [LangGraph Memory Documentation](https://docs.langchain.com/oss/python/langgraph/add-memory)

### Add Message Reducer to State

```python
# app/agents/state.py - Update ChatAgentState
from typing import Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class ChatAgentState(TypedDict):
    # ... existing fields ...

    # Replace: messages: list
    # With:
    messages: Annotated[list[AnyMessage], add_messages]
    """Conversation history with automatic accumulation via add_messages reducer."""

    # ... rest of fields ...
```

**Source:** [LangGraph State Management Guide](https://deepwiki.com/langchain-ai/langgraph-101/3.1-state-management)

### Get Context Usage Endpoint

```python
# app/routers/chat.py - Add new endpoint
from app.agents.memory.token_counter import get_token_counter

@router.get("/files/{file_id}/context-usage")
async def get_context_usage(
    file_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Get current context window usage for file tab."""
    settings = get_settings()
    graph = get_or_create_graph(request.app.state.checkpointer)

    # Get current state from checkpointer
    thread_id = f"file_{file_id}_user_{current_user.id}"
    config = {"configurable": {"thread_id": thread_id}}
    state = await graph.aget_state(config)

    messages = state.values.get("messages", [])

    # Count tokens using provider-specific counter
    provider = get_agent_provider("coding_agent")  # Use first agent's provider
    model = get_agent_model("coding_agent")
    counter = get_token_counter(provider, model)

    current_tokens = counter.count_messages(messages)
    max_tokens = settings.context_window_tokens

    return {
        "current_tokens": current_tokens,
        "max_tokens": max_tokens,
        "percentage": (current_tokens / max_tokens * 100) if max_tokens > 0 else 0,
        "message_count": len(messages)
    }
```

**Source:** [LangGraph Checkpointing API Reference](https://reference.langchain.com/python/langgraph/checkpoints/)

### Trim Messages Node (Optional - for explicit trimming)

```python
# app/agents/memory/trimmer.py
from langchain_core.messages import trim_messages
from app.agents.state import ChatAgentState

async def trim_messages_node(state: ChatAgentState) -> dict:
    """Trim messages if user confirmed and limit exceeded.

    This is called ONLY when user confirms trimming via UI.
    """
    settings = get_settings()
    messages = state.get("messages", [])

    # Get token counter for current provider
    provider = get_agent_provider("coding_agent")
    model = get_agent_model("coding_agent")
    counter = get_token_counter(provider, model)

    # Trim to 90% of limit to leave headroom
    target_tokens = int(settings.context_window_tokens * 0.9)

    trimmed = trim_messages(
        messages,
        max_tokens=target_tokens,
        strategy="last",
        token_counter=lambda msgs: counter.count_messages(msgs),
        start_on="human",
        end_on=("human", "tool"),
        include_system=True
    )

    return {"messages": trimmed}
```

**Source:** [Managing Message History in LangGraph](https://langchain-ai.github.io/langgraph/how-tos/create-react-agent-manage-message-history/)

### Frontend: Context Usage Display

```typescript
// frontend/src/components/chat/ContextUsage.tsx
import { useQuery } from '@tanstack/react-query';

export function ContextUsage({ fileId }: { fileId: string }) {
  const { data } = useQuery({
    queryKey: ['context-usage', fileId],
    queryFn: async () => {
      const res = await fetch(`/api/files/${fileId}/context-usage`);
      return res.json();
    },
    refetchInterval: 30000, // Check every 30s
  });

  if (!data) return null;

  const percentage = data.percentage;
  const isWarning = percentage >= 85;

  return (
    <div className="text-sm text-gray-600">
      <span className={isWarning ? 'text-orange-600 font-semibold' : ''}>
        {data.current_tokens.toLocaleString()} / {data.max_tokens.toLocaleString()} tokens
      </span>
      {isWarning && (
        <span className="ml-2 text-orange-600">
          ⚠ Context limit approaching
        </span>
      )}
    </div>
  );
}
```

**Source:** Existing codebase patterns (tabStore.ts, chat types)

### Frontend: Tab Close Warning

```typescript
// frontend/src/hooks/useTabCloseWarning.ts
import { useBeforeunload } from 'react-beforeunload';

export function useTabCloseWarning(hasContext: boolean) {
  useBeforeunload((event) => {
    if (hasContext) {
      event.preventDefault();
      event.returnValue = '';
    }
  });
}

// Usage in ChatTab component
function ChatTab({ fileId }: { fileId: string }) {
  const messages = useChatHistory(fileId);
  const hasContext = messages.length > 2;

  useTabCloseWarning(hasContext);

  // ... rest of component
}
```

**Source:** [MDN beforeunload event](https://developer.mozilla.org/en-US/docs/Web/API/Window/beforeunload_event), [react-beforeunload npm](https://www.npmjs.com/package/react-beforeunload)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| In-memory session storage | PostgreSQL checkpointing | LangGraph 1.0 (2024) | Persistent sessions survive server restarts |
| SQLite checkpointer | AsyncPostgresSaver | langgraph-checkpoint-postgres 2.0 (Jan 2026) | Async/await support, connection pooling |
| Custom message deduplication | `add_messages` reducer | LangGraph 0.2+ | Built-in ID-based deduplication |
| Manual token counting loops | `trim_messages` utility | langchain-core 0.3+ | Respects model-specific message boundaries |
| PostgresSaver.aget_tuple() | AsyncPostgresSaver native async | checkpoint-postgres 2.0 | No more NotImplementedError with streaming |

**Deprecated/outdated:**
- **PostgresSaver with sync methods:** Use `AsyncPostgresSaver` from `.aio` submodule for FastAPI applications
- **BaseChatMessageHistory:** LangGraph's checkpointing replaces this older LangChain memory abstraction
- **Custom beforeunload message text:** Browsers no longer allow custom messages (security feature, removed ~2020)
- **langgraph-checkpoint-sqlite for production:** Use PostgreSQL variant for concurrent access and durability

## Open Questions

1. **Should we implement LLM-based summarization for very long conversations?**
   - What we know: `trim_messages` deletes old messages. Summarization replaces them with condensed versions.
   - What's unclear: Whether users need access to full history beyond current session, or if trimming is sufficient.
   - Recommendation: Start with trimming (simpler). Add summarization in future phase if users request "conversation recap" feature.

2. **How to handle context across multiple tabs for same file?**
   - What we know: `thread_id = f"file_{file_id}_user_{user_id}"` means all tabs for same file share one conversation thread.
   - What's unclear: Is this desired behavior? Or should each browser tab have isolated context?
   - Recommendation: Keep current behavior (shared context per file). If users complain about "cross-tab contamination," add `session_id` to thread_id in future phase. MEMORY-04 requires "independent conversation memory" per tab, so this needs clarification.

3. **Should context warning persist across browser refresh?**
   - What we know: Zustand state is cleared on refresh. Context usage must be re-fetched from backend.
   - What's unclear: Should we show "You were at 90% before refresh" on reload?
   - Recommendation: No. Current token usage on load is what matters. Historical usage is in LangSmith traces if needed for debugging.

4. **How to handle checkpointer connection pool sizing?**
   - What we know: Default `max_size=10` in AsyncConnectionPool. Each request uses checkpointer connection.
   - What's unclear: Optimal pool size for production with 50+ concurrent users.
   - Recommendation: Start with 10. Monitor connection pool exhaustion metrics. Increase to 20-30 if needed. Document in deployment guide.

## Sources

### Primary (HIGH confidence)
- [LangGraph Memory Documentation](https://docs.langchain.com/oss/python/langgraph/add-memory) - Checkpointing setup and thread_id usage
- [langgraph-checkpoint-postgres PyPI](https://pypi.org/project/langgraph-checkpoint-postgres/) - Official package documentation (v2.0.0, released Jan 31, 2026)
- [LangGraph Persistence Guide](https://docs.langchain.com/oss/python/langgraph/persistence) - AsyncPostgresSaver configuration
- [Managing Message History in LangGraph](https://langchain-ai.github.io/langgraph/how-tos/create-react-agent-manage-message-history/) - Message trimming strategies
- [LangGraph Checkpointing API Reference](https://reference.langchain.com/python/langgraph/checkpoints/) - get_state_history, aget_state methods
- Existing codebase: `backend/app/agents/graph.py` (lines 465-469, 469, 170), `backend/app/services/agent_service.py` (line 365)

### Secondary (MEDIUM confidence)
- [Mastering LangGraph Checkpointing: Best Practices for 2025](https://sparkco.ai/blog/mastering-langgraph-checkpointing-best-practices-for-2025) - Production patterns, verified against official docs
- [Building an Agentic IDE with LangGraph and PostgreSQL](https://medium.com/@prashanthkgajula/building-an-agentic-ide-how-i-built-a-multi-agent-code-generation-system-with-langgraph-and-467f08f6bf64) - Real-world implementation example
- [FastAPI + LangGraph Agent Production Template](https://github.com/wassim249/fastapi-langgraph-agent-production-ready-template) - Lifecycle management patterns
- [I Built a LangGraph + FastAPI Agent… and Spent Days Fighting Postgres](https://medium.com/@termtrix/i-built-a-langgraph-fastapi-agent-and-spent-days-fighting-postgres-8913f84c296d) - Common pitfalls and solutions
- [Token Counting Guide: tiktoken, Anthropic, Gemini](https://www.propelcode.ai/blog/token-counting-tiktoken-anthropic-gemini-guide-2025) - Provider-specific tokenization

### Tertiary (LOW confidence)
- [MDN beforeunload event](https://developer.mozilla.org/en-US/docs/Web/API/Window/beforeunload_event) - Browser API (stable, but browser behavior varies)
- [react-beforeunload npm](https://www.npmjs.com/package/react-beforeunload) - Community library (not official React)
- [Understanding Memory Management in LangGraph](https://pub.towardsai.net/understanding-memory-management-in-langgraph-a-practical-guide-for-genai-students-b3642c9ea7e1) - Educational content (use for concepts, verify code patterns)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official LangGraph packages, already installed, documented thoroughly
- Architecture: HIGH - Patterns verified in official docs + existing codebase + multiple production examples
- Pitfalls: HIGH - Documented in GitHub issues, official docs warnings, and real-world blog posts
- Token counting: MEDIUM - Provider APIs are official, but integration patterns vary
- Browser warnings: MEDIUM - Standard API but browser behavior differs (verify in testing)

**Research date:** 2026-02-07
**Valid until:** ~60 days (LangGraph checkpointing is mature/stable domain, low churn rate)

**Key sources requiring ongoing verification:**
- AsyncPostgresSaver async compatibility (recently fixed in 2.0, monitor for regressions)
- Browser beforeunload behavior (evolving web standard)
- Provider-specific token counting APIs (may change with new model releases)
