# Phase 4: Streaming Infrastructure - Research

**Researched:** 2026-02-03
**Domain:** Server-Sent Events (SSE) streaming from LangGraph agent pipeline to frontend
**Confidence:** HIGH

## Summary

This phase converts the existing synchronous `graph.ainvoke()` call in `agent_service.run_chat_query()` into a streaming pipeline using LangGraph's `astream()` with combined `["updates", "custom"]` stream modes, served to the frontend via SSE using `sse-starlette`. The backend emits structured events for each agent transition (coding, validation, execution, analysis) plus error/retry status, while the frontend consumes them via `@microsoft/fetch-event-source` (required because native `EventSource` does not support POST requests with JSON bodies).

The existing codebase is well-structured for this change: the `ChatAgentState` TypedDict already tracks all fields needed for streaming events (`generated_code`, `validation_result`, `error_count`, `execution_result`, `analysis`), and the graph nodes map directly to the user-visible status events defined in CONTEXT.md. The key architectural shift is from `ainvoke()` (returns final state) to `astream()` (yields intermediate state updates per node), plus injecting `get_stream_writer()` into nodes for custom status/progress events. Python 3.12 is confirmed, so `get_stream_writer` works via contextvars (no need for the `StreamWriter` parameter injection workaround required for Python < 3.11).

Chat history persistence follows the "save on completion only" decision: the SSE endpoint buffers the full response, then writes to the database atomically after the stream completes successfully. Failed streams save nothing. Stream metadata (duration, retry count, errors) is stored in `metadata_json` on the `ChatMessage` record.

**Primary recommendation:** Use LangGraph `astream(stream_mode=["updates", "custom"])` with `get_stream_writer()` for custom status events, served via `sse-starlette`'s `EventSourceResponse`, consumed by `@microsoft/fetch-event-source` on the frontend.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| sse-starlette | 3.2.0 | FastAPI SSE response class | W3C SSE spec compliant; automatic client disconnect detection; ping/keepalive; production-ready for Starlette/FastAPI |
| langgraph | 1.0.7 (installed) | Agent graph streaming via `astream()` | Already in project; native `stream_mode=["updates", "custom"]` gives both node transitions and custom events |
| @microsoft/fetch-event-source | 2.0.1 | Frontend SSE client with POST support | Only SSE client that supports POST + JSON body + custom headers + reconnection callbacks; de facto standard for AI streaming UIs |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| langgraph.config.get_stream_writer | (part of langgraph 1.0.7) | Emit custom events from inside graph nodes | When nodes need to emit status updates (e.g., "Generating code...", "Validating...") beyond state updates |
| langgraph.types.StreamWriter | (part of langgraph 1.0.7) | Type annotation for stream writer parameter | For type-safe node signatures; auto-injected by LangGraph |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| sse-starlette | FastAPI StreamingResponse | StreamingResponse works but lacks SSE-specific features: no automatic ping/keepalive, no W3C event format helpers, no disconnect detection |
| @microsoft/fetch-event-source | Native EventSource API | EventSource only supports GET requests; cannot send POST with JSON body for chat queries; no custom headers for JWT auth |
| LangGraph astream | LangGraph astream_events | astream_events is being deprecated as of LangGraph 1.0; astream with stream_mode is the current recommended approach |

**Installation:**
```bash
# Backend
cd backend && uv add sse-starlette

# Frontend (Phase 6, but documenting for reference)
cd frontend && npm install @microsoft/fetch-event-source
```

## Architecture Patterns

### Recommended Project Structure
```
backend/app/
├── routers/
│   └── chat.py              # Add SSE streaming endpoint
├── services/
│   └── agent_service.py     # Add run_chat_query_stream() generator
├── schemas/
│   └── chat.py              # Add StreamEvent schema
├── agents/
│   ├── graph.py              # Modify to support streaming (no structural change)
│   ├── coding.py             # Add get_stream_writer() calls for status events
│   ├── code_checker.py       # Add get_stream_writer() calls for validation status
│   ├── data_analysis.py      # Add get_stream_writer() calls for analysis status
│   └── state.py              # No change needed
└── config.py                 # Add streaming timeout setting
```

### Pattern 1: LangGraph Combined Stream Mode
**What:** Use `astream(stream_mode=["updates", "custom"])` to get both node state updates and custom status events in a single stream.
**When to use:** Always for this project -- we need node transitions (which agent is running) AND custom progress messages.

```python
# Source: LangGraph official docs + verified with langgraph 1.0.7
async for stream_mode, chunk in graph.astream(
    initial_state,
    config,
    stream_mode=["updates", "custom"],
):
    if stream_mode == "custom":
        # Custom event from get_stream_writer() inside a node
        # e.g., {"type": "status", "message": "Generating code..."}
        yield format_sse_event("status", chunk)
    elif stream_mode == "updates":
        # State delta after a node completes
        # chunk is dict keyed by node name: {"coding_agent": {"generated_code": "..."}}
        for node_name, state_update in chunk.items():
            yield format_sse_event("node_complete", {
                "node": node_name,
                "update": state_update
            })
```

### Pattern 2: Custom Status Events via get_stream_writer
**What:** Inject status updates from inside LangGraph nodes so users see real-time progress.
**When to use:** In every graph node to emit the status events defined in CONTEXT.md.

```python
# Source: LangGraph docs, verified importable with langgraph 1.0.7 on Python 3.12
from langgraph.config import get_stream_writer

async def coding_agent(state: ChatAgentState) -> dict:
    writer = get_stream_writer()

    # Emit status event visible to user
    writer({
        "type": "status",
        "event": "coding_started",
        "message": "Generating code...",
        "step": 1,
        "total_steps": 4
    })

    # ... existing coding agent logic ...

    return {"generated_code": code}
```

### Pattern 3: SSE Endpoint with EventSourceResponse
**What:** FastAPI endpoint that wraps the LangGraph stream in an SSE response.
**When to use:** For the streaming chat query endpoint.

```python
# Source: sse-starlette docs + FastAPI SSE patterns
from sse_starlette.sse import EventSourceResponse
import json

@router.post("/{file_id}/stream")
async def stream_query(
    file_id: UUID,
    body: ChatQueryRequest,
    current_user: CurrentUser,
    db: DbSession,
    request: Request
):
    async def event_generator():
        try:
            async for event in agent_service.run_chat_query_stream(
                db, file_id, current_user.id, body.content
            ):
                if await request.is_disconnected():
                    break
                yield {
                    "event": event["type"],
                    "data": json.dumps(event),
                    "id": event.get("id"),
                    "retry": 15000  # 15 second retry
                }
            # Final completion event
            yield {
                "event": "completed",
                "data": json.dumps({"type": "completed"}),
            }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({
                    "type": "error",
                    "message": str(e)
                }),
            }

    return EventSourceResponse(
        event_generator(),
        ping=30,  # keepalive every 30 seconds
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering
        }
    )
```

### Pattern 4: Atomic Chat History Persistence
**What:** Save user message and AI response to database only after successful stream completion.
**When to use:** After stream completes without error (per CONTEXT.md decision).

```python
async def run_chat_query_stream(db, file_id, user_id, user_query):
    # ... setup graph, initial_state, config ...

    final_state = {}

    async for stream_mode, chunk in graph.astream(
        initial_state, config,
        stream_mode=["updates", "custom"],
    ):
        if stream_mode == "custom":
            yield {"type": "status", **chunk}
        elif stream_mode == "updates":
            for node_name, update in chunk.items():
                final_state.update(update)
                yield {"type": "node_complete", "node": node_name, **update}

    # Stream completed successfully -- save to database atomically
    await ChatService.create_message(db, file_id, user_id, user_query, role="user")
    await ChatService.create_message(
        db, file_id, user_id,
        final_state.get("final_response", ""),
        role="assistant",
        message_type="agent_response",
        metadata_json={
            "generated_code": final_state.get("generated_code"),
            "execution_result": final_state.get("execution_result"),
            "error_count": final_state.get("error_count", 0),
            "stream_metadata": {
                "duration_ms": elapsed_ms,
                "retry_count": final_state.get("error_count", 0),
                "error": final_state.get("error"),
            }
        }
    )
```

### Pattern 5: Frontend SSE Consumption with fetch-event-source
**What:** POST-based SSE client with typed event handling and reconnection.
**When to use:** In the chat component when sending AI queries.

```typescript
// Source: @microsoft/fetch-event-source docs
import { fetchEventSource } from '@microsoft/fetch-event-source';

class RetriableError extends Error {}
class FatalError extends Error {}

const ctrl = new AbortController();

await fetchEventSource(`/api/chat/${fileId}/stream`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({ content: query }),
    signal: ctrl.signal,

    async onopen(response) {
        if (response.ok) return;
        if (response.status === 401) throw new FatalError('Unauthorized');
        throw new RetriableError();
    },

    onmessage(ev) {
        const data = JSON.parse(ev.data);
        switch (ev.event) {
            case 'status':
                setStatus(data.message);  // "Generating code..."
                setProgress({ step: data.step, total: data.total_steps });
                break;
            case 'node_complete':
                // Handle intermediate results
                break;
            case 'content_chunk':
                appendContent(data.text);  // Chunk-based rendering
                break;
            case 'completed':
                setComplete(true);
                break;
            case 'error':
                setError(data.message);
                break;
        }
    },

    onclose() {
        // Server closed connection -- could be normal completion
    },

    onerror(err) {
        if (err instanceof FatalError) throw err;  // Stop retrying
        // Otherwise auto-retry (return nothing)
        setStatus('Reconnecting...');
    },
});

// User cancels
ctrl.abort();
```

### Anti-Patterns to Avoid
- **Using `ainvoke()` then faking streaming:** Never call `ainvoke()` and then artificially delay sending chunks. Use `astream()` for real streaming from the graph.
- **Using `astream_events()` instead of `astream()`:** `astream_events` is being deprecated in LangGraph 1.0+. Use `astream(stream_mode=...)` instead.
- **Saving to database during stream:** Never write partial results to DB mid-stream. This violates the CONTEXT.md decision of "save on completion only" and risks orphaned partial records on failure.
- **Using native EventSource on frontend:** The native `EventSource` API only supports GET requests. Chat queries require POST with JSON body and JWT auth headers.
- **Blocking the event loop in stream generator:** Never do synchronous I/O inside the SSE generator. All operations must be async.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SSE response formatting | Custom `text/event-stream` StreamingResponse | `sse-starlette` EventSourceResponse | Handles SSE spec compliance, ping/keepalive, disconnect detection, proper event formatting |
| Client disconnect detection | Manual TCP keepalive checking | `sse-starlette` + `request.is_disconnected()` | sse-starlette runs disconnect listener concurrently with stream; handles edge cases |
| POST-based SSE client | Custom fetch + ReadableStream parsing | `@microsoft/fetch-event-source` | Handles SSE parsing, reconnection, typed events, abort; battle-tested by Microsoft |
| Node-level streaming events | Custom callback system for agent transitions | LangGraph `astream(stream_mode="updates")` | Built-in: yields `{node_name: state_delta}` for each node completion |
| Custom progress events | Custom event bus or queue | LangGraph `get_stream_writer()` | Built-in: nodes emit arbitrary data into the stream; no external queue needed |
| SSE event ID tracking | Custom counter/UUID system | SSE `id` field + `Last-Event-ID` header | W3C spec: browser automatically sends `Last-Event-ID` on reconnection |

**Key insight:** The entire streaming pipeline is built from three well-integrated pieces: LangGraph (produces events) -> sse-starlette (formats and serves SSE) -> fetch-event-source (consumes SSE). Each handles its layer's complexity. Custom solutions at any layer would miss edge cases these libraries handle.

## Common Pitfalls

### Pitfall 1: Nginx/Proxy Response Buffering
**What goes wrong:** SSE events are buffered by Nginx until ~16KB accumulates, causing long delays before first event appears.
**Why it happens:** Nginx buffers responses by default for performance.
**How to avoid:** Set `X-Accel-Buffering: no` header on SSE responses. Add `proxy_buffering off;` in Nginx config.
**Warning signs:** Events arrive in bursts instead of individually; long initial delay before first event.

### Pitfall 2: Saving Partial Results to Database
**What goes wrong:** Stream fails mid-way, leaving orphaned user messages or partial assistant responses in chat history.
**Why it happens:** Developer saves messages incrementally as events arrive.
**How to avoid:** Buffer complete response, save atomically after stream completes. On failure, save nothing (per CONTEXT.md decision).
**Warning signs:** Chat history shows messages without corresponding responses; partial/truncated assistant messages.

### Pitfall 3: Frontend Memory Leak from Unclosed SSE Connections
**What goes wrong:** Browser accumulates open connections, degrading performance.
**Why it happens:** Not calling `AbortController.abort()` when component unmounts or user navigates away.
**How to avoid:** Always abort in cleanup: React `useEffect` return function, Vue `onUnmounted`, etc.
**Warning signs:** Browser dev tools show multiple pending SSE connections; memory usage grows over time.

### Pitfall 4: EventSource GET-Only Limitation
**What goes wrong:** Developer tries to use native `EventSource` API, discovers it only supports GET requests -- cannot send POST body with query or auth headers.
**Why it happens:** SSE spec's `EventSource` was designed for simple GET subscriptions.
**How to avoid:** Use `@microsoft/fetch-event-source` which wraps `fetch()` and supports POST, custom headers, and JSON bodies.
**Warning signs:** Cannot send query body; cannot attach JWT auth header; forced to put sensitive data in URL query params.

### Pitfall 5: Stream Timeout on Complex Queries
**What goes wrong:** Stream connection times out before the 4-agent pipeline completes, especially with validation retries.
**Why it happens:** Default HTTP timeout is often 30-60 seconds; complex queries with retries can take 2-3 minutes.
**How to avoid:** Configure 180-second (3-minute) timeout on SSE endpoint. Set keepalive ping every 30 seconds to prevent proxy/load balancer timeouts. Add `retry: 15000` in SSE events for client-side reconnection.
**Warning signs:** Connections drop during long queries; users see "connection closed" errors for complex analyses.

### Pitfall 6: Blocking Event Loop in Generator
**What goes wrong:** SSE stream freezes or stops sending events.
**Why it happens:** Synchronous code (file I/O, CPU-bound operations) runs inside the async generator, blocking the event loop.
**How to avoid:** All I/O inside the generator must be async. Use `asyncio.to_thread()` for any blocking operations. The LangGraph `astream()` call is already async.
**Warning signs:** No events arrive for extended periods; server stops responding to other requests during streaming.

### Pitfall 7: Concurrent Database Session Issues
**What goes wrong:** Database session errors or deadlocks during streaming.
**Why it happens:** The SSE generator holds a database session open for the entire stream duration (potentially minutes). Other requests may conflict.
**How to avoid:** Use separate database sessions: one short-lived session for file/auth validation at stream start, then save results with a fresh session after stream completes. Do not hold a session open across the entire stream.
**Warning signs:** `TimeoutError` or `InterfaceError` from SQLAlchemy during streaming; database connection pool exhaustion.

## Code Examples

Verified patterns from official sources:

### SSE Event Format (W3C Spec)
```
event: status
data: {"type":"status","event":"coding_started","message":"Generating code...","step":1,"total_steps":4}
id: evt_001
retry: 15000

event: node_complete
data: {"type":"node_complete","node":"coding_agent","generated_code":"import pandas as pd\n..."}

event: status
data: {"type":"status","event":"validation_started","message":"Validating...","step":2,"total_steps":4}

event: error
data: {"type":"retry","message":"Code validation failed: unsafe import","attempt":2,"max_attempts":3}

event: status
data: {"type":"status","event":"coding_started","message":"Regenerating code (attempt 2/3)...","step":1,"total_steps":4}

event: content_chunk
data: {"type":"content","text":"Based on the analysis, the average "}

event: content_chunk
data: {"type":"content","text":"sales figure is $42,500 per quarter."}

event: completed
data: {"type":"completed","message":"Analysis complete"}
```

### Proposed SSE Event Type Enum
```python
from enum import Enum

class StreamEventType(str, Enum):
    """SSE event types for the streaming chat pipeline."""
    # Status events (agent transitions)
    CODING_STARTED = "coding_started"
    VALIDATION_STARTED = "validation_started"
    EXECUTION_STARTED = "execution_started"
    ANALYSIS_STARTED = "analysis_started"

    # Progress events
    PROGRESS = "progress"           # step X of Y
    RETRY = "retry"                 # validation failed, retrying

    # Content events
    CONTENT_CHUNK = "content_chunk"  # analysis text chunks
    NODE_COMPLETE = "node_complete"  # node finished with state delta

    # Terminal events
    COMPLETED = "completed"
    ERROR = "error"
```

### Agent Node with Stream Writer (Coding Agent Example)
```python
# Source: LangGraph docs for get_stream_writer, adapted for project
from langgraph.config import get_stream_writer

async def coding_agent(state: ChatAgentState) -> dict:
    writer = get_stream_writer()

    # Emit user-visible status (no agent name exposed, per CONTEXT.md)
    writer({
        "type": "status",
        "event": "coding_started",
        "message": "Generating code...",
        "step": 1,
        "total_steps": 4
    })

    # Build prompt and invoke LLM (existing logic)
    settings = get_settings()
    system_prompt = get_agent_prompt("coding")
    # ... format prompt with data_summary, user_context, user_query ...

    llm = get_llm(
        provider=settings.llm_provider,
        model=settings.agent_model,
        api_key=api_key,
        max_tokens=max_tokens,
    )

    response = await llm.ainvoke(messages)
    code = extract_code(response.content)

    return {"generated_code": code}
```

### Complete SSE Streaming Service Function
```python
# Source: Pattern combining LangGraph astream + sse-starlette
import time
import json
from typing import AsyncGenerator

async def run_chat_query_stream(
    db: AsyncSession,
    file_id: UUID,
    user_id: UUID,
    user_query: str
) -> AsyncGenerator[dict, None]:
    """Stream chat query through agent pipeline, yielding SSE events.

    Yields status events for each agent transition, error/retry events,
    and content chunks. Saves to database atomically on completion.
    """
    start_time = time.monotonic()

    # Validate file and onboarding (uses short-lived query)
    file_record = await FileService.get_user_file(db, file_id, user_id)
    if not file_record:
        yield {"type": "error", "message": "File not found"}
        return
    if file_record.data_summary is None:
        yield {"type": "error", "message": "File not yet analyzed"}
        return

    graph = get_or_create_graph()
    thread_id = f"file_{file_id}_user_{user_id}"
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "file_id": str(file_id),
        "user_id": str(user_id),
        "user_query": user_query,
        "data_summary": file_record.data_summary,
        "user_context": file_record.user_context or "",
        "generated_code": "",
        "validation_result": "",
        "validation_errors": [],
        "error_count": 0,
        "max_steps": settings.agent_max_retries,
        "execution_result": "",
        "analysis": "",
        "messages": [],
        "final_response": "",
        "error": ""
    }

    final_state = {}

    try:
        async for mode, chunk in graph.astream(
            initial_state, config,
            stream_mode=["updates", "custom"],
        ):
            if mode == "custom":
                yield chunk  # Already formatted by get_stream_writer()
            elif mode == "updates":
                for node_name, update in chunk.items():
                    final_state.update(update)
                    yield {
                        "type": "node_complete",
                        "node": node_name,
                        **{k: v for k, v in update.items()
                           if k in ("generated_code", "execution_result",
                                    "analysis", "final_response")}
                    }

        # Success: save atomically
        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        await ChatService.create_message(
            db, file_id, user_id, user_query, role="user"
        )

        response_text = final_state.get("final_response") or final_state.get("analysis", "")
        await ChatService.create_message(
            db, file_id, user_id, response_text,
            role="assistant",
            message_type="agent_response",
            metadata_json={
                "generated_code": final_state.get("generated_code"),
                "execution_result": final_state.get("execution_result"),
                "error_count": final_state.get("error_count", 0),
                "stream_metadata": {
                    "duration_ms": elapsed_ms,
                    "retry_count": final_state.get("error_count", 0),
                    "error": final_state.get("error"),
                }
            }
        )

        yield {"type": "completed", "message": "Analysis complete"}

    except Exception as e:
        # Failure: save nothing (per CONTEXT.md decision)
        yield {"type": "error", "message": str(e)}
```

### EventSourceResponse with Ping and Timeout
```python
# Source: sse-starlette docs
from sse_starlette.sse import EventSourceResponse

return EventSourceResponse(
    event_generator(),
    ping=30,                    # Send keepalive every 30 seconds
    ping_message_factory=None,  # Default SSE comment ping
    send_timeout=180,           # 3-minute timeout (per CONTEXT.md medium timeout)
    headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    }
)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `astream_events()` for node tracking | `astream(stream_mode="updates")` | LangGraph 1.0 (Oct 2025) | astream_events deprecated in favor of stream modes |
| Manual StreamWriter parameter injection | `get_stream_writer()` via contextvars | LangGraph 0.x -> 1.0, Python >= 3.11 | Cleaner API; no need to add writer param to node signature |
| WebSockets for AI streaming | SSE via sse-starlette | 2024-2025 industry shift | SSE is simpler, auto-reconnects, works with HTTP proxies/CDNs |
| Native EventSource API | @microsoft/fetch-event-source | 2021+ for AI apps | POST support, custom headers, reconnection callbacks |
| sse-starlette 2.x AppStatus pattern | sse-starlette 3.x automatic context | sse-starlette 3.0 (2025) | No manual AppStatus.should_exit_event management needed |

**Deprecated/outdated:**
- `astream_events()`: Being phased out in LangGraph 1.0+; use `astream(stream_mode=...)` instead
- `sse-starlette` 2.x `AppStatus.should_exit_event`: Deprecated since 3.0.0; library handles event loop contexts automatically
- WebSockets for unidirectional AI streaming: Unnecessary complexity; SSE is the standard for server-to-client streaming

## Open Questions

Things that couldn't be fully resolved:

1. **How does `astream()` interact with the PostgreSQL checkpointer?**
   - What we know: `ainvoke()` currently uses the checkpointer for thread isolation. `astream()` should work identically since it's the same compiled graph.
   - What's unclear: Whether checkpointing happens per-node or only at completion during streaming. This affects resume behavior on reconnection.
   - Recommendation: Test in implementation. The checkpointer should work transparently with `astream()`.

2. **Content chunk streaming from Data Analysis Agent**
   - What we know: CONTEXT.md specifies "chunk-based (word or line at a time)" content rendering. LangGraph `stream_mode="messages"` can stream LLM tokens.
   - What's unclear: Whether combining three modes `["updates", "custom", "messages"]` works reliably in LangGraph 1.0.7 for token-by-token streaming from the analysis node only.
   - Recommendation: Start with `["updates", "custom"]` for node-level events. If token streaming from the analysis node is needed, add `"messages"` mode and filter by `langgraph_node == "data_analysis"`. Alternatively, stream the analysis text in chunks via `get_stream_writer()` within the data_analysis node itself.

3. **Database session lifecycle during long-running streams**
   - What we know: FastAPI `Depends(get_db)` creates a session scoped to the request. SSE streams can run for minutes.
   - What's unclear: Whether the session remains valid for the atomic save at stream completion, or if it will timeout/expire.
   - Recommendation: Validate file access at stream start with the injected session, then create a new session for the final atomic save using `async with async_session() as db:`. This avoids holding a session open for the entire stream duration.

4. **Whether to show intermediate generated code during stream**
   - What we know: This is listed as "Claude's Discretion" in CONTEXT.md.
   - Recommendation: Stream generated code as part of `node_complete` events when `coding_agent` finishes. Frontend can choose to show it in a collapsible "View Code" section. Show it by default since it builds user trust in the pipeline.

5. **User message save timing (also Claude's Discretion)**
   - What we know: CONTEXT.md leaves this to discretion.
   - Recommendation: Save user message together with assistant response after successful completion. This ensures atomicity -- if the stream fails, neither message appears, keeping chat history clean.

## Sources

### Primary (HIGH confidence)
- LangGraph 1.0.7 (installed in project) - `get_stream_writer`, `StreamWriter`, `astream()` APIs verified importable
- [LangGraph streaming concepts](https://github.com/langchain-ai/langgraph/blob/main/docs/docs/concepts/streaming.md) - stream modes documentation
- [LangGraph official streaming docs](https://docs.langchain.com/oss/python/langgraph/streaming) - astream, get_stream_writer, stream_mode
- [LangGraph config reference](https://reference.langchain.com/python/langgraph/config/) - get_stream_writer API
- [sse-starlette GitHub](https://github.com/sysid/sse-starlette) - EventSourceResponse API, version 3.2.0
- [sse-starlette PyPI](https://pypi.org/project/sse-starlette/) - version verification
- [@microsoft/fetch-event-source GitHub](https://github.com/Azure/fetch-event-source) - v2.0.1, POST support, reconnection API

### Secondary (MEDIUM confidence)
- [SSE with FastAPI and React + LangGraph](https://www.softgrade.org/sse-with-fastapi-react-langgraph/) - integration pattern verified with official docs
- [LangGraph fullstack Python SSE streaming](https://deepwiki.com/langchain-ai/langgraph-fullstack-python/2.3-sse-streaming) - SSE endpoint patterns
- [FastAPI SSE for LLM tokens](https://medium.com/@hadiyolworld007/fastapi-sse-for-llm-tokens-smooth-streaming-without-websockets-001ead4b5e53) - production patterns
- [MDN Server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events) - SSE spec reference
- [LangGraph streaming academy](https://deepwiki.com/langchain-ai/langchain-academy/6.3-streaming-and-state-editing) - stream modes education

### Tertiary (LOW confidence)
- [LangGraph astream_events issue #6105](https://github.com/langchain-ai/langgraph/issues/6105) - known bug with nested runnables (may not affect this project)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries verified: langgraph 1.0.7 installed with get_stream_writer confirmed importable; sse-starlette 3.2.0 on PyPI; @microsoft/fetch-event-source 2.0.1 on npm
- Architecture: HIGH - Pattern of LangGraph astream -> SSE response -> fetch-event-source is well-documented across official docs and multiple verified sources
- Pitfalls: HIGH - Nginx buffering, EventSource GET limitation, database session lifecycle are all well-documented issues with established solutions
- Event format: MEDIUM - The specific event type enum and payload structure is a design choice informed by CONTEXT.md decisions; not dictated by any library
- Content chunk streaming: MEDIUM - Combining three stream modes (updates+custom+messages) needs validation during implementation

**Research date:** 2026-02-03
**Valid until:** 2026-03-03 (30 days; stable libraries, stable patterns)
