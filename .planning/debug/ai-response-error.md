# Debug Session: AI Response Error

## Issue Summary
**Severity:** CRITICAL
**Component:** AI Chat Feature
**Symptom:** After sending chat message, user receives "something went wrong, please try again" error
**Expected:** Typing indicator → AI response streams character-by-character
**Actual:** Generic error message displayed inline in chat
**Blocked Tests:** UAT Tests 13-21 (all AI response features)

## Timeline
- **Discovered:** Phase 6 UAT
- **Test:** Test 12 in 06-UAT.md
- **Impact:** Core functionality broken

## Investigation Log

### Session Start
- **Date:** 2026-02-04
- **Investigator:** Claude Code
- **Goal:** Find root cause only (diagnosis for UAT gap closure)

### Investigation Steps

#### Step 1: Locate UAT Test Details
- Read UAT file at `.planning/phases/06-frontend-ui-interactive-data-cards/06-UAT.md`
- Test 12 failed: "fail. received error message \"something went wrong, please try again\""
- Expected: Typing indicator → AI response streams character-by-character
- Actual: Generic error message

#### Step 2: Frontend Analysis
- Checked `frontend/src/components/chat/ChatInterface.tsx`
  - Uses `useSSEStream` hook for streaming
  - Error displayed via `streamError` state at line 239-254
  - Error message: "Something went wrong. Please try again."

- Checked `frontend/src/hooks/useSSEStream.ts`
  - Streams from `/api/chat/${fileId}/stream` endpoint (line 76)
  - Uses POST with ReadableStream
  - Catches errors and sets error state (line 171-187)

#### Step 3: Backend Analysis
- Checked `backend/app/routers/chat.py`
  - Stream endpoint at line 147: `POST /{file_id}/stream`
  - Calls `agent_service.run_chat_query_stream()` (line 196)
  - Catches exceptions and yields error event (line 212-219)

- Checked `backend/app/services/agent_service.py`
  - `run_chat_query_stream()` function at line 229
  - Gets graph via `get_or_create_graph()` (line 276)
  - Streams graph execution with `graph.astream()` (line 308)

#### Step 4: Graph Initialization Issue FOUND
- Checked `backend/app/agents/graph.py`
  - `build_chat_graph()` function at line 412
  - Line 436: `checkpointer = PostgresSaver.from_conn_string(postgres_url)`
  - Line 437: `checkpointer.setup()` ← **THIS LINE FAILS**

#### Step 5: Root Cause Confirmed
- Tested graph creation manually with backend venv
- **ERROR:** `AttributeError: '_GeneratorContextManager' object has no attribute 'setup'`
- Checked PostgresSaver API:
  - `from_conn_string()` returns `Iterator[PostgresSaver]` (context manager)
  - NOT a PostgresSaver object directly
  - Needs to be used with `with` statement or iterator consumed

**ROOT CAUSE IDENTIFIED:** The graph initialization fails because `PostgresSaver.from_conn_string()` is misused. It returns a context manager/iterator, but the code tries to call `.setup()` on it directly. This causes an AttributeError during graph creation, which propagates up as a generic error to the frontend.

## Root Cause

### Problem
The LangGraph workflow fails to initialize due to incorrect usage of `PostgresSaver.from_conn_string()` in `backend/app/agents/graph.py`.

### Location
- File: `/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/backend/app/agents/graph.py`
- Function: `build_chat_graph()`
- Lines: 436-437

### Code
```python
# Line 436-437 - BROKEN
checkpointer = PostgresSaver.from_conn_string(postgres_url)
checkpointer.setup()  # AttributeError: context manager has no 'setup'
```

### Why It Fails
1. `PostgresSaver.from_conn_string()` returns `Iterator[PostgresSaver]` (a context manager)
2. The code treats the return value as a PostgresSaver object
3. Calling `.setup()` on the context manager raises `AttributeError`
4. Graph initialization fails silently (cached in module-level variable)
5. When SSE stream endpoint calls `get_or_create_graph()`, it raises exception
6. Exception caught by SSE error handler, yields generic error event
7. Frontend displays "Something went wrong. Please try again."

### Impact
- **Complete AI chat failure:** All chat queries fail
- **Blocked UAT tests:** Tests 12-21 cannot run (all AI response features)
- **Silent failure:** No obvious error in logs, fails at graph init time
- **Cascading errors:** Every chat attempt re-triggers the same initialization failure

## Verification

### Test 1: API Key Valid
```bash
$ cd backend && .venv/bin/python -c "test anthropic API"
Result: API Key is VALID
Response: Hi! How are you doing today?
```

### Test 2: Backend Running
```bash
$ ps aux | grep uvicorn
Result: Backend running on port 8000
```

### Test 3: Graph Creation Fails
```bash
$ cd backend && .venv/bin/python -c "from app.agents.graph import get_or_create_graph; get_or_create_graph()"
Result: AttributeError: '_GeneratorContextManager' object has no attribute 'setup'
```

### Test 4: PostgresSaver API Check
```bash
$ cd backend && .venv/bin/python -c "check PostgresSaver.from_conn_string signature"
Result: Returns Iterator[PostgresSaver] (context manager), NOT PostgresSaver object
```

## Related Issues

This root cause explains multiple UAT failures:
- **Test 12:** AI response fails (direct impact)
- **Tests 13-21:** All skipped (depend on Test 12)
- **Tests 4-6:** File upload issues may be related (files not showing in sidebar)

## Next Steps

**Gap Closure Plan Required:**
1. Fix PostgresSaver initialization in `build_chat_graph()`
2. Use proper context manager pattern or consume iterator
3. Test graph creation manually
4. Verify SSE streaming endpoint works
5. Run UAT Test 12 again
6. Unblock Tests 13-21

**DO NOT FIX** - This is a diagnosis-only session per debugging context.

## Technical Details

### Correct Usage Pattern
The LangGraph PostgresSaver API requires context manager usage:

```python
# CORRECT - Use with statement
with PostgresSaver.from_conn_string(postgres_url) as checkpointer:
    checkpointer.setup()
    graph = StateGraph(ChatAgentState)
    # ... add nodes ...
    compiled = graph.compile(checkpointer=checkpointer)
    return compiled
```

### Current Broken Code
```python
# BROKEN - backend/app/agents/graph.py lines 436-437
checkpointer = PostgresSaver.from_conn_string(postgres_url)
checkpointer.setup()  # AttributeError!
```

### API Signature
```python
PostgresSaver.from_conn_string(conn_string: str) -> Iterator[PostgresSaver]
```

The method returns an `Iterator[PostgresSaver]`, which is a generator/context manager. When used without the `with` statement, you get the context manager object itself, not the PostgresSaver instance.

### Error Flow
1. Backend starts → imports `app.agents.graph`
2. First chat request → calls `get_or_create_graph()`
3. Calls `build_chat_graph(settings.database_url)`
4. Line 436: `checkpointer = PostgresSaver.from_conn_string(postgres_url)` → returns context manager
5. Line 437: `checkpointer.setup()` → **AttributeError: '_GeneratorContextManager' object has no attribute 'setup'**
6. Exception propagates to `agent_service.run_chat_query_stream()`
7. Exception caught at line 371-377, yields error event
8. Frontend SSE hook receives error event
9. Sets `streamError` state
10. UI displays generic error message

## Session End

**Status:** ROOT CAUSE FOUND

**Root Cause:** PostgresSaver.from_conn_string() misused in backend/app/agents/graph.py:436-437. Returns context manager but code treats it as PostgresSaver object. Causes AttributeError during graph initialization, breaking all AI chat functionality.

**Severity:** CRITICAL - Complete AI chat failure

**Files Involved:**
- `/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/backend/app/agents/graph.py` (lines 436-437)

**Recommended Fix:** Use context manager pattern with `with` statement or consume iterator properly

**Investigation Duration:** ~30 minutes

**Artifacts:**
- Debug session: `.planning/debug/ai-response-error.md`
- Test results: API key valid, backend running, graph init fails
- Error reproduction: 100% reproducible
