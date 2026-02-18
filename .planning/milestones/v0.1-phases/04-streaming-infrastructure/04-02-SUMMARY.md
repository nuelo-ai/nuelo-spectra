---
phase: 04-streaming-infrastructure
plan: 02
subsystem: streaming
tags: [sse-starlette, langgraph, streaming, events, sse, fastapi]

# Dependency graph
requires:
  - phase: 04-01
    provides: StreamEventType enum, StreamEvent model, stream timeout/ping config, get_stream_writer() in all agent nodes
  - phase: 03-05
    provides: run_chat_query() service function, ChatService.create_message(), thread isolation
provides:
  - run_chat_query_stream() async generator yielding SSE events from LangGraph astream()
  - POST /chat/{file_id}/stream SSE endpoint with EventSourceResponse
  - Atomic chat history persistence on stream completion with metadata
  - Fresh database session pattern for long-running streams
  - Client disconnect detection and keepalive pings
affects: [06-frontend-streaming-ui]

# Tech tracking
tech-stack:
  added: []
  patterns: [LangGraph astream() with stream_mode, Fresh DB session for persistence, SSE EventSourceResponse with disconnect detection]

key-files:
  created: []
  modified:
    - backend/app/services/agent_service.py
    - backend/app/routers/chat.py

key-decisions:
  - "Fresh database session via async_session_maker() for chat persistence prevents connection timeout on long streams"
  - "Stream metadata stored in assistant message metadata_json: duration_ms, retry_count, errors"
  - "Failed streams save nothing to database (clean failure state per CONTEXT.md)"
  - "File ownership verified before stream starts for fast fail with proper HTTP error"
  - "15-second SSE retry interval for client auto-reconnection"
  - "Event IDs for SSE reconnection support (Last-Event-ID header)"

patterns-established:
  - "Streaming service layer: async generator yields event dicts, router wraps in EventSourceResponse"
  - "Two-session pattern: request-scoped session for validation, fresh session for persistence"
  - "Atomic persistence: buffer stream, save user+assistant messages together on completion"
  - "Disconnect detection: check request.is_disconnected() in event generator loop"

# Metrics
duration: 2min
completed: 2026-02-03
---

# Phase 04 Plan 02: SSE Endpoint & Atomic Persistence Summary

**LangGraph astream() served via EventSourceResponse with atomic chat history saved using fresh DB session on completion**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-03T17:24:42Z
- **Completed:** 2026-02-03T17:26:54Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Created run_chat_query_stream() async generator that converts graph.ainvoke() to graph.astream(stream_mode=["updates", "custom"])
- Yields custom status events from get_stream_writer() and node completion events with intermediate results
- Implemented POST /chat/{file_id}/stream endpoint with EventSourceResponse, disconnect detection, and keepalive pings
- Atomic chat history persistence on success with fresh database session (prevents connection timeout on long streams)
- Stream metadata tracked: duration_ms, retry_count, errors stored in assistant message
- Failed streams save nothing to database (clean failure state)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create run_chat_query_stream() async generator** - `2db1d42` (feat)
2. **Task 2: Create POST /chat/{file_id}/stream SSE endpoint** - `96c553d` (feat)

## Files Created/Modified
- `backend/app/services/agent_service.py` - run_chat_query_stream() async generator yields SSE events from LangGraph astream(), uses fresh DB session for persistence after stream completes
- `backend/app/routers/chat.py` - POST /chat/{file_id}/stream endpoint wraps event generator in EventSourceResponse with 30s ping, 180s timeout, disconnect detection

## Decisions Made

1. **Fresh database session for persistence**: Uses async_session_maker() to create new session for chat history writes instead of reusing request-scoped db session. The request-scoped session may timeout or lose connection during long-running streams (2-3 minutes for complex queries). Documented with explicit comment in code referencing 04-RESEARCH.md Pitfall 7.

2. **Stream metadata structure**: Stores duration_ms, retry_count, and error in nested stream_metadata object within assistant message metadata_json. Also includes generated_code, execution_result, and error_count at top level for backward compatibility with non-streaming endpoint.

3. **File ownership verification timing**: Verify file ownership BEFORE starting stream (in endpoint, before event_generator starts) for fast fail with proper HTTP 404 error. If verification happened inside generator, error would be SSE event instead of HTTP error.

4. **Event counter for SSE IDs**: Sequential counter starting at 0 for SSE event IDs. Enables Last-Event-ID reconnection support without complex ID generation.

5. **Keepalive and timeout values**: 30-second ping interval and 180-second send timeout from settings (stream_ping_interval and stream_timeout_seconds). Prevents proxy timeout during long-running agent operations.

6. **Disconnect detection inside loop**: Check request.is_disconnected() on every event yield, break immediately if client disconnected. Prevents wasteful processing if user navigates away.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - LangGraph astream() API worked as documented, sse-starlette EventSourceResponse integrated cleanly with FastAPI, all verifications passed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Ready for Plan 04-03 (Error Handling & Reconnection):
- SSE streaming endpoint functional with basic error handling
- Stream yields error events on exception
- Disconnect detection active
- Event IDs enable reconnection support

Foundation streaming pipeline complete. Next plan should enhance error handling (structured error types, retry guidance) and reconnection logic (Last-Event-ID handling, stream resume).

---
*Phase: 04-streaming-infrastructure*
*Completed: 2026-02-03*
