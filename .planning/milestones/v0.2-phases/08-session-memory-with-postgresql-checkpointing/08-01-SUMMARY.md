---
phase: 08-session-memory-with-postgresql-checkpointing
plan: 01
subsystem: agent-infrastructure
tags: [langgraph, postgresql, checkpointing, session-memory, async, multi-turn-conversation]

# Dependency graph
requires:
  - phase: 07-multi-llm-provider-infrastructure
    provides: LLM factory, agent configuration, provider registry
provides:
  - AsyncPostgresSaver initialized in FastAPI lifespan with connection pooling
  - ChatAgentState with add_messages reducer for message accumulation
  - Graph compilation with checkpointer parameter
  - Agent service and router wired to pass checkpointer from app.state
  - Context window configuration settings (context_window_tokens, context_warning_threshold)
affects: [phase-09-query-suggestions, phase-08-02-token-counting, conversation-memory]

# Tech tracking
tech-stack:
  added:
    - langgraph.checkpoint.postgres.aio.AsyncPostgresSaver
    - psycopg_pool.AsyncConnectionPool
    - langchain_core.messages.HumanMessage
    - langgraph.graph.message.add_messages
  patterns:
    - FastAPI lifespan context for checkpointer lifecycle management
    - Message reducer pattern with Annotated[list[AnyMessage], add_messages]
    - Thread-based conversation isolation via thread_id (file_{file_id}_user_{user_id})
    - Database URL format conversion (asyncpg to psycopg)

key-files:
  created: []
  modified:
    - backend/app/config.py
    - backend/app/agents/state.py
    - backend/app/agents/graph.py
    - backend/app/main.py
    - backend/app/services/agent_service.py
    - backend/app/routers/chat.py

key-decisions:
  - "AsyncPostgresSaver is NOT an async context manager - use direct instantiation, not async with"
  - "Database URL must be converted from postgresql+asyncpg:// to postgresql:// for psycopg compatibility"
  - "Messages initialized as [HumanMessage(content=user_query)] instead of empty list to enable reducer accumulation"
  - "Checkpointer lifecycle managed via FastAPI lifespan with AsyncConnectionPool context"
  - "Context window defaults: 12000 tokens, 85% warning threshold (configurable via .env)"

patterns-established:
  - "Checkpointer passed through function signatures (agent_service → get_or_create_graph → build_chat_graph)"
  - "Graph cached at module level, checkpointer passed on first call (lazy initialization)"
  - "Checkpoint tables auto-created via checkpointer.setup() (idempotent)"

# Metrics
duration: 4min
completed: 2026-02-07
---

# Phase 8 Plan 1: PostgreSQL Checkpointing Infrastructure Summary

**AsyncPostgresSaver with add_messages reducer enables multi-turn conversation memory persisted to PostgreSQL, with thread-based isolation per file tab**

## Performance

- **Duration:** 4 min 16 sec
- **Started:** 2026-02-07T15:25:08Z
- **Completed:** 2026-02-07T15:29:24Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- AsyncPostgresSaver initialized in FastAPI lifespan with connection pooling and automatic table creation
- ChatAgentState messages field updated to use add_messages reducer for automatic message accumulation
- Graph compilation accepts checkpointer parameter, removing hardcoded None and duplicate construction
- Agent service and chat router fully wired to pass checkpointer from app.state
- Checkpoint tables created in PostgreSQL (checkpoints, checkpoint_blobs, checkpoint_writes, checkpoint_migrations)
- Context window configuration added to Settings (12000 tokens, 85% threshold)

## Task Commits

Each task was committed atomically:

1. **Task 1: Enable AsyncPostgresSaver and update state schema** - `a0cc387` (feat)
   - Add context window settings to config.py
   - Update ChatAgentState with add_messages reducer
   - Modify build_chat_graph() and get_or_create_graph() to accept checkpointer
   - Remove duplicate graph construction block
   - Initialize AsyncPostgresSaver in FastAPI lifespan

2. **Task 2: Wire agent service to use checkpointer from app.state** - `b8f630f` (feat)
   - Add checkpointer parameter to run_chat_query() and run_chat_query_stream()
   - Pass checkpointer from request.app.state to agent functions
   - Initialize messages with HumanMessage for reducer accumulation
   - Fix AsyncPostgresSaver initialization (not an async context manager)
   - Add Request parameter to query_with_ai() endpoint

## Files Created/Modified

- `backend/app/config.py` - Added context_window_tokens (12000) and context_warning_threshold (0.85) to Settings
- `backend/app/agents/state.py` - Updated messages field to Annotated[list[AnyMessage], add_messages] with reducer
- `backend/app/agents/graph.py` - Added checkpointer parameter to build_chat_graph() and get_or_create_graph(), removed duplicate graph construction
- `backend/app/main.py` - Initialized AsyncPostgresSaver in lifespan context with AsyncConnectionPool, database URL conversion
- `backend/app/services/agent_service.py` - Added checkpointer parameter to both query functions, updated messages to [HumanMessage(content=user_query)]
- `backend/app/routers/chat.py` - Added Request parameter to query_with_ai(), passed checkpointer from app.state to agent service

## Decisions Made

1. **AsyncPostgresSaver is not an async context manager** - Discovered during testing that AsyncPostgresSaver doesn't support `async with`. Changed from `async with AsyncPostgresSaver(pool) as checkpointer` to `checkpointer = AsyncPostgresSaver(pool)`. This is the correct pattern per LangGraph documentation.

2. **Database URL format conversion** - SQLAlchemy uses `postgresql+asyncpg://` format, but psycopg requires plain `postgresql://`. Added conversion logic in lifespan to replace prefix before passing to AsyncConnectionPool.

3. **Messages initialization for reducer** - Changed from empty list `messages: []` to `messages: [HumanMessage(content=user_query)]` so the add_messages reducer can properly accumulate conversation history. Empty list would cause the current query to be lost.

4. **Checkpointer lifecycle in lifespan** - Placed checkpointer initialization inside AsyncConnectionPool's async context manager, with yield INSIDE the context. This ensures the connection pool stays alive during the application lifecycle and closes cleanly on shutdown.

5. **Graph caching with checkpointer** - Kept module-level cached graph pattern, passing checkpointer on first call. Since checkpointer is set once at startup and doesn't change, the cache remains valid for the application lifetime.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed AsyncPostgresSaver context manager usage**
- **Found during:** Task 1 verification (server startup test)
- **Issue:** AsyncPostgresSaver doesn't support async context manager protocol. Code used `async with AsyncPostgresSaver(pool) as checkpointer` which raised TypeError: 'AsyncPostgresSaver' object does not support the asynchronous context manager protocol
- **Fix:** Changed to direct instantiation: `checkpointer = AsyncPostgresSaver(pool)` and called `await checkpointer.setup()` separately
- **Files modified:** backend/app/main.py
- **Verification:** Server started successfully, checkpointer initialized, checkpoint tables created in database
- **Committed in:** b8f630f (Task 2 commit, as fix was discovered during Task 1 verification but corrected during Task 2 execution)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Fix was essential for correctness - AsyncPostgresSaver API doesn't match the async context manager pattern shown in some examples. No scope creep.

## Issues Encountered

**AsyncPostgresSaver async context manager assumption** - The plan (based on RESEARCH.md examples) showed AsyncPostgresSaver as an async context manager. Testing revealed this is incorrect - the class doesn't implement `__aenter__`/`__aexit__`. Resolution: Used direct instantiation pattern which is the correct approach per LangGraph source code.

## User Setup Required

None - no external service configuration required. Checkpointing uses the existing PostgreSQL database (already configured in DATABASE_URL).

## Next Phase Readiness

**Ready for next phase:**
- PostgreSQL checkpointing infrastructure fully operational
- Message accumulation working via add_messages reducer
- Thread-based isolation enables per-file-tab conversation memory
- Context window settings in place for token counting (Phase 8 Plan 2)

**Next steps:**
- Plan 08-02: Implement token counting and context window management
- Plan 08-03: Add frontend warnings for context usage
- Plan 08-04: Add message trimming with user confirmation

**No blockers.** Infrastructure is solid and checkpoint tables are created. Ready for token counting implementation.

## Self-Check

Verifying all claimed artifacts exist:

**Files modified:**
- backend/app/config.py: FOUND (context_window_tokens, context_warning_threshold added)
- backend/app/agents/state.py: FOUND (messages field with add_messages reducer)
- backend/app/agents/graph.py: FOUND (checkpointer parameter, duplicate removed)
- backend/app/main.py: FOUND (AsyncPostgresSaver initialization in lifespan)
- backend/app/services/agent_service.py: FOUND (checkpointer parameter, HumanMessage usage)
- backend/app/routers/chat.py: FOUND (checkpointer passed from app.state)

**Commits:**
- a0cc387: FOUND (feat(08-01): enable AsyncPostgresSaver and update state schema)
- b8f630f: FOUND (feat(08-01): wire agent service and router to use checkpointer)

**Database tables:**
- checkpoints: FOUND
- checkpoint_blobs: FOUND
- checkpoint_writes: FOUND
- checkpoint_migrations: FOUND

## Self-Check: PASSED

All claimed files, commits, and database artifacts verified.

---
*Phase: 08-session-memory-with-postgresql-checkpointing*
*Completed: 2026-02-07*
