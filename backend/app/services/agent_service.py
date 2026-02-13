"""Service layer for agent invocation and orchestration."""

import logging
import os
import time
import json
import traceback
from uuid import UUID
from typing import AsyncGenerator

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from app.agents.graph import get_or_create_graph
from app.agents.onboarding import OnboardingAgent
from app.config import get_settings
from app.database import async_session_maker
from app.services.chat import ChatService
from app.services.file import FileService


# Configure LangSmith tracing if enabled
settings = get_settings()
if settings.langsmith_tracing and settings.langsmith_api_key:
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project


async def run_onboarding(
    db: AsyncSession,
    file_id: UUID,
    user_id: UUID,
    user_context: str = ""
) -> str:
    """Run Onboarding Agent on uploaded file and save summary to database.

    Args:
        db: Database session
        file_id: File UUID
        user_id: User UUID (for access control)
        user_context: Optional user-provided context

    Returns:
        str: Generated data summary

    Raises:
        HTTPException: If file not found or agent execution fails
    """
    # Load file record with access control
    file_record = await FileService.get_user_file(db, file_id, user_id)
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Instantiate and run Onboarding Agent
    agent = OnboardingAgent()
    try:
        result = await agent.run(
            file_path=file_record.file_path,
            file_type=file_record.file_type,
            user_context=user_context
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Onboarding agent failed: {str(e)}"
        )

    # Update file record with summary, suggestions, and context
    file_record.data_summary = result.data_summary
    file_record.query_suggestions = result.query_suggestions
    file_record.user_context = user_context if user_context else None

    await db.commit()
    await db.refresh(file_record)

    return result.data_summary


async def update_user_context(
    db: AsyncSession,
    file_id: UUID,
    user_id: UUID,
    additional_context: str
) -> str:
    """Update user context for a file by appending additional context.

    Args:
        db: Database session
        file_id: File UUID
        user_id: User UUID (for access control)
        additional_context: Additional context to append

    Returns:
        str: Updated user_context

    Raises:
        HTTPException: If file not found
    """
    # Load file record with access control
    file_record = await FileService.get_user_file(db, file_id, user_id)
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Append additional context (v1 always appends per CONTEXT.md)
    if file_record.user_context:
        file_record.user_context += f"\n{additional_context}"
    else:
        file_record.user_context = additional_context

    await db.commit()
    await db.refresh(file_record)

    return file_record.user_context


async def run_chat_query(
    db: AsyncSession,
    file_id: UUID | None,
    user_id: UUID,
    user_query: str,
    checkpointer=None,
    web_search_enabled: bool = False,
    session_id: UUID | None = None,
) -> dict:
    """Run chat query through the full agent pipeline.

    This function orchestrates the complete AI analysis workflow:
    1. Load file and verify onboarding completed
    2. Invoke LangGraph workflow (Coding Agent -> Code Checker -> Execute -> Data Analysis)
    3. Save user message and agent response to chat history
    4. Return structured response with code, execution result, and analysis

    Supports both file-based (legacy) and session-based (v0.3) flows:
    - If session_id provided: uses session-based thread_id, saves messages with session_id
    - If session_id is None: uses file-based thread_id, saves messages with file_id (backward compat)

    Args:
        db: Database session
        file_id: File UUID (optional if session_id provided)
        user_id: User UUID (for access control)
        user_query: User's natural language query
        checkpointer: Optional PostgreSQL checkpointer
        web_search_enabled: Whether web search is enabled for this query
        session_id: Optional Session UUID (v0.3 multi-file conversations)

    Returns:
        dict: Agent response with user_query, generated_code, execution_result,
              analysis, error (if any), and retry_count

    Raises:
        HTTPException: If file not found or not yet onboarded (data_summary is None)
    """
    # Load file record based on session_id or file_id
    if session_id:
        # Session-based flow: assemble multi-file context via ContextAssembler
        from app.services.chat_session import ChatSessionService
        from app.services.context_assembler import ContextAssembler
        session = await ChatSessionService.get_user_session(db, session_id, user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        if not session.files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No files linked to this session"
            )
        # Use first file as primary (for legacy fields)
        file_record = session.files[0]

        # Assemble multi-file context -- fail with clear error if any file is missing/unreadable
        assembler = ContextAssembler()
        file_ids = [f.id for f in session.files]
        try:
            context_result = await assembler.assemble(db, file_ids, user_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        # File-based flow: get file directly (backward compatibility)
        file_record = await FileService.get_user_file(db, file_id, user_id)
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )

    # Check that onboarding has completed
    if file_record.data_summary is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File has not been analyzed yet. Please wait for onboarding to complete."
        )

    # Get or create compiled graph with checkpointer
    graph = get_or_create_graph(checkpointer)

    # Build thread ID based on session_id or file_id
    if session_id:
        thread_id = f"session_{session_id}_user_{user_id}"
    else:
        thread_id = f"file_{file_id}_user_{user_id}"
    config = {"configurable": {"thread_id": thread_id}}

    # Build initial state: per-query fields only.
    # Fields like generated_code, execution_result, analysis are OMITTED so that
    # checkpoint values from previous queries persist — the Manager Agent needs
    # to see previous code/results for accurate routing decisions.
    # These fields use .get() with defaults throughout the graph, so missing on
    # first query (no checkpoint) is safe.
    from langchain_core.messages import HumanMessage

    # Build multi-file fields based on session vs file flow
    if session_id:
        multi_file_context = context_result["context_string"]
        file_metadata = [
            {
                "id": f["id"],
                "name": f["name"],
                "var_name": f["var_name"],
                "file_path": next(sf.file_path for sf in session.files if str(sf.id) == f["id"]),
                "file_type": next(sf.file_type for sf in session.files if str(sf.id) == f["id"]),
            }
            for f in context_result["files"]
        ]
        session_files = [f.original_filename for f in session.files]
    else:
        multi_file_context = ""
        file_metadata = []
        session_files = []

    initial_state = {
        "file_id": str(file_record.id),  # Always use actual file_id for execution
        "user_id": str(user_id),
        "user_query": user_query,
        "data_summary": file_record.data_summary,
        "user_context": file_record.user_context or "",
        "file_path": file_record.file_path,
        "validation_result": "",
        "validation_errors": [],
        "error_count": 0,
        "max_steps": settings.agent_max_retries,
        "final_response": "",
        "error": "",
        "routing_decision": None,
        "previous_code": "",
        "web_search_enabled": web_search_enabled,
        "search_sources": [],
        "session_id": str(session_id) if session_id else None,
        # Multi-file fields (empty defaults for single-file backward compatibility)
        "multi_file_context": multi_file_context,
        "file_metadata": file_metadata,
        "session_files": session_files,
        # Visualization infrastructure defaults (v0.4 Phase 20)
        "visualization_requested": False,
        "chart_hint": "",
        "chart_code": "",
        "chart_specs": "",
        "chart_error": "",
    }

    # Add new user message to checkpoint using aupdate_state
    # This preserves existing messages and appends the new one via add_messages reducer
    # On first call (no checkpoint), creates checkpoint with this message
    # On subsequent calls, appends to existing checkpointed messages
    await graph.aupdate_state(config, {"messages": [HumanMessage(content=user_query)]})

    # Invoke graph - it will load checkpointed state with accumulated messages
    # Messages come from checkpoint (not initial_state) so conversation history persists
    result = await graph.ainvoke(initial_state, config)

    # Track search quota per user query (not per API call)
    if web_search_enabled:
        await _track_search_quota(db, user_id)

    # Save user message to chat history (session-based or file-based)
    if session_id:
        await ChatService.create_session_message(
            db,
            session_id,
            user_id,
            user_query,
            role="user"
        )
    else:
        await ChatService.create_message(
            db,
            file_id,
            user_id,
            user_query,
            role="user"
        )

    # Serialize routing_decision for metadata storage
    rd = result.get("routing_decision")
    routing_meta = rd.model_dump() if hasattr(rd, "model_dump") else (rd or {})

    # Save assistant response with metadata (session-based or file-based)
    final_response_text = result.get("final_response") or result.get("analysis", "")
    if session_id:
        await ChatService.create_session_message(
            db,
            session_id,
            user_id,
            final_response_text,
            role="assistant",
            message_type="agent_response",
            metadata_json={
                "generated_code": result.get("generated_code"),
                "execution_result": result.get("execution_result"),
                "error_count": result.get("error_count", 0),
                "error": result.get("error"),
                "routing_decision": routing_meta,
                "search_sources": result.get("search_sources", []),
                "follow_up_suggestions": result.get("follow_up_suggestions", []),
                "chart_specs": result.get("chart_specs", ""),
                "chart_error": result.get("chart_error", ""),
            }
        )
    else:
        await ChatService.create_message(
            db,
            file_id,
            user_id,
            final_response_text,
            role="assistant",
            message_type="agent_response",
            metadata_json={
                "generated_code": result.get("generated_code"),
                "execution_result": result.get("execution_result"),
                "error_count": result.get("error_count", 0),
                "error": result.get("error"),
                "routing_decision": routing_meta,
                "search_sources": result.get("search_sources", []),
                "follow_up_suggestions": result.get("follow_up_suggestions", []),
                "chart_specs": result.get("chart_specs", ""),
                "chart_error": result.get("chart_error", ""),
            }
        )

    # Return structured response
    return {
        "user_query": user_query,
        "generated_code": result.get("generated_code"),
        "execution_result": result.get("execution_result"),
        "analysis": final_response_text,
        "error": result.get("error"),
        "retry_count": result.get("error_count", 0),
        "chart_specs": result.get("chart_specs", ""),
        "chart_error": result.get("chart_error", ""),
    }


async def run_chat_query_stream(
    db: AsyncSession,
    file_id: UUID | None,
    user_id: UUID,
    user_query: str,
    checkpointer=None,
    web_search_enabled: bool = False,
    session_id: UUID | None = None,
) -> AsyncGenerator[dict, None]:
    """Run chat query through agent pipeline and yield SSE events.

    This streaming version of run_chat_query converts the synchronous graph.ainvoke()
    to graph.astream() and yields structured event dicts for the SSE endpoint to format.

    Events yielded:
    - Custom status events from get_stream_writer() (coding_started, validation_started, etc.)
    - Node completion events with intermediate results (generated_code, execution_result, etc.)
    - Search events from search tool (search_started, search_completed, search_failed)
    - Error events on failure
    - Completion event on success

    Chat history is saved atomically on successful stream completion with metadata.
    Failed streams save nothing to the database (clean failure state per CONTEXT.md).

    Supports both file-based (legacy) and session-based (v0.3) flows:
    - If session_id provided: uses session-based thread_id, saves messages with session_id
    - If session_id is None: uses file-based thread_id, saves messages with file_id (backward compat)

    Args:
        db: Database session (used for initial file validation only)
        file_id: File UUID (optional if session_id provided)
        user_id: User UUID (for access control)
        user_query: User's natural language query
        checkpointer: Optional PostgreSQL checkpointer
        web_search_enabled: Whether web search is enabled for this query
        session_id: Optional Session UUID (v0.3 multi-file conversations)

    Yields:
        dict: Event dictionaries with type, message, and event-specific fields

    Raises:
        Yields error event dict (does not raise exceptions)
    """
    logger.info(f"Starting chat stream for session_id={session_id}, file_id={file_id}, user_id={user_id}, query={user_query[:50]}...")

    # Load file record based on session_id or file_id
    if session_id:
        # Session-based flow: assemble multi-file context via ContextAssembler
        from app.services.chat_session import ChatSessionService
        from app.services.context_assembler import ContextAssembler
        session = await ChatSessionService.get_user_session(db, session_id, user_id)
        if not session:
            logger.error(f"Session not found: session_id={session_id}, user_id={user_id}")
            yield {"type": "error", "message": "Session not found"}
            return
        if not session.files:
            yield {
                "type": "error",
                "message": "No files linked to this session"
            }
            return
        # Use first file as primary (for legacy fields)
        file_record = session.files[0]

        # Assemble multi-file context -- fail with clear error if any file is missing/unreadable
        assembler = ContextAssembler()
        file_ids = [f.id for f in session.files]
        try:
            context_result = await assembler.assemble(db, file_ids, user_id)
        except ValueError as e:
            yield {"type": "error", "message": str(e)}
            return
    else:
        # File-based flow: get file directly (backward compatibility)
        file_record = await FileService.get_user_file(db, file_id, user_id)
        if not file_record:
            logger.error(f"File not found: file_id={file_id}, user_id={user_id}")
            yield {"type": "error", "message": "File not found"}
            return

    # Check that onboarding has completed
    if file_record.data_summary is None:
        yield {
            "type": "error",
            "message": "File not yet analyzed. Please wait for onboarding to complete."
        }
        return

    # Generate data profile JSON for coding agent (quick operation, only reads 5 rows)
    from app.agents.onboarding import OnboardingAgent
    agent = OnboardingAgent()
    try:
        data_profile = await agent.profile_data(
            file_path=file_record.file_path,
            file_type=file_record.file_type
        )
        # Serialize to JSON string for prompt
        import json
        data_profile_json = json.dumps(data_profile, indent=2)
    except Exception as e:
        logger.error(f"Failed to generate data profile: {e}")
        data_profile_json = "{}"

    # Get or create compiled graph with checkpointer
    graph = get_or_create_graph(checkpointer)

    # Build thread ID based on session_id or file_id
    if session_id:
        thread_id = f"session_{session_id}_user_{user_id}"
    else:
        thread_id = f"file_{file_id}_user_{user_id}"
    config = {"configurable": {"thread_id": thread_id}}

    # Build initial state: per-query fields only.
    # Fields like generated_code, execution_result, analysis are OMITTED so that
    # checkpoint values from previous queries persist — the Manager Agent needs
    # to see previous code/results for accurate routing decisions.
    # These fields use .get() with defaults throughout the graph, so missing on
    # first query (no checkpoint) is safe.
    from langchain_core.messages import HumanMessage

    # Build multi-file fields based on session vs file flow
    if session_id:
        multi_file_context = context_result["context_string"]
        file_metadata = [
            {
                "id": f["id"],
                "name": f["name"],
                "var_name": f["var_name"],
                "file_path": next(sf.file_path for sf in session.files if str(sf.id) == f["id"]),
                "file_type": next(sf.file_type for sf in session.files if str(sf.id) == f["id"]),
            }
            for f in context_result["files"]
        ]
        session_files = [f.original_filename for f in session.files]
    else:
        multi_file_context = ""
        file_metadata = []
        session_files = []

    initial_state = {
        "file_id": str(file_record.id),  # Always use actual file_id for execution
        "user_id": str(user_id),
        "user_query": user_query,
        "data_summary": file_record.data_summary,
        "data_profile": data_profile_json,
        "user_context": file_record.user_context or "",
        "file_path": file_record.file_path,
        "validation_result": "",
        "validation_errors": [],
        "error_count": 0,
        "max_steps": settings.agent_max_retries,
        "final_response": "",
        "error": "",
        "routing_decision": None,
        "previous_code": "",
        "web_search_enabled": web_search_enabled,
        "search_sources": [],
        "session_id": str(session_id) if session_id else None,
        # Multi-file fields (empty defaults for single-file backward compatibility)
        "multi_file_context": multi_file_context,
        "file_metadata": file_metadata,
        "session_files": session_files,
        # Visualization infrastructure defaults (v0.4 Phase 20)
        "visualization_requested": False,
        "chart_hint": "",
        "chart_code": "",
        "chart_specs": "",
        "chart_error": "",
    }

    # Add new user message to checkpoint using aupdate_state
    # This preserves existing messages and appends the new one via add_messages reducer
    # On first call (no checkpoint), creates checkpoint with this message
    # On subsequent calls, appends to existing checkpointed messages
    await graph.aupdate_state(config, {"messages": [HumanMessage(content=user_query)]})

    # Start timing for stream metadata
    start_time = time.monotonic()
    final_state = {}

    try:
        # Stream graph execution with combined mode: updates + custom
        async for mode, chunk in graph.astream(
            initial_state, config,
            stream_mode=["updates", "custom"],
        ):
            if mode == "custom":
                # Custom events from get_stream_writer() inside nodes
                # These are status, progress, retry, and search events emitted by agents/tools
                yield chunk
            elif mode == "updates":
                # State delta after a node completes
                # chunk is dict keyed by node name: {"coding_agent": {"generated_code": "..."}}
                for node_name, update in chunk.items():
                    # Serialize routing_decision Pydantic model to dict for JSON
                    if "routing_decision" in update and update["routing_decision"]:
                        rd = update["routing_decision"]
                        if hasattr(rd, "model_dump"):
                            update["routing_decision"] = rd.model_dump()
                    final_state.update(update)
                    # Yield node completion with relevant fields only
                    # (filter to user-visible data, exclude internal state)
                    yield {
                        "type": "node_complete",
                        "node": node_name,
                        **{k: v for k, v in update.items()
                           if k in ("generated_code", "execution_result",
                                    "analysis", "final_response", "error",
                                    "routing_decision", "follow_up_suggestions",
                                    "search_sources", "chart_specs", "chart_error")}
                    }

        # Stream completed successfully -- save atomically with fresh session
        # IMPORTANT: Use fresh session via async_session_maker() for persistence,
        # NOT the injected `db` session. The injected session is scoped to the
        # HTTP request and may timeout or lose its connection during the
        # potentially long-running stream (streams can run 2-3 minutes for
        # complex queries with retries). Creating a fresh session here prevents
        # "connection already closed" / "connection lost during query" errors
        # that occur when trying to write with a session that has been idle
        # throughout the entire streaming duration. See 04-RESEARCH.md Pitfall 7.
        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        # Track search quota per user query (not per API call)
        if web_search_enabled:
            async with async_session_maker() as quota_db:
                await _track_search_quota(quota_db, user_id)

        async with async_session_maker() as save_db:
            # Save user message (session-based or file-based)
            if session_id:
                await ChatService.create_session_message(
                    save_db, session_id, user_id, user_query, role="user"
                )
            else:
                await ChatService.create_message(
                    save_db, file_id, user_id, user_query, role="user"
                )

            # Serialize routing_decision for metadata storage
            rd = final_state.get("routing_decision")
            routing_meta = rd.model_dump() if hasattr(rd, "model_dump") else (rd or {})

            # Save assistant response with stream metadata (session-based or file-based)
            response_text = final_state.get("final_response") or final_state.get("analysis", "")
            if session_id:
                await ChatService.create_session_message(
                    save_db, session_id, user_id, response_text,
                    role="assistant",
                    message_type="agent_response",
                    metadata_json={
                        "generated_code": final_state.get("generated_code"),
                        "execution_result": final_state.get("execution_result"),
                        "error_count": final_state.get("error_count", 0),
                        "routing_decision": routing_meta,
                        "follow_up_suggestions": final_state.get("follow_up_suggestions", []),
                        "search_sources": final_state.get("search_sources", []),
                        "chart_specs": final_state.get("chart_specs", ""),
                        "chart_error": final_state.get("chart_error", ""),
                        "stream_metadata": {
                            "duration_ms": elapsed_ms,
                            "retry_count": final_state.get("error_count", 0),
                            "error": final_state.get("error"),
                        }
                    }
                )
            else:
                await ChatService.create_message(
                    save_db, file_id, user_id, response_text,
                    role="assistant",
                    message_type="agent_response",
                    metadata_json={
                        "generated_code": final_state.get("generated_code"),
                        "execution_result": final_state.get("execution_result"),
                        "error_count": final_state.get("error_count", 0),
                        "routing_decision": routing_meta,
                        "follow_up_suggestions": final_state.get("follow_up_suggestions", []),
                        "search_sources": final_state.get("search_sources", []),
                        "chart_specs": final_state.get("chart_specs", ""),
                        "chart_error": final_state.get("chart_error", ""),
                        "stream_metadata": {
                            "duration_ms": elapsed_ms,
                            "retry_count": final_state.get("error_count", 0),
                            "error": final_state.get("error"),
                        }
                    }
                )

        # Yield completion event
        yield {
            "type": "completed",
            "message": "Analysis complete"
        }

    except Exception as e:
        # On failure, yield error event and save nothing to database
        # (clean failure state per CONTEXT.md decision)
        error_msg = str(e) if str(e) else f"{type(e).__name__}: {repr(e)}"
        logger.error(f"Stream error for file_id={file_id}: {error_msg}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        yield {
            "type": "error",
            "message": error_msg
        }


async def _track_search_quota(db: AsyncSession, user_id: UUID) -> None:
    """Track search quota per user query (not per API call).

    Increments the daily search count for the user. Creates a new row
    if no quota record exists for today.

    Args:
        db: Database session
        user_id: User UUID
    """
    from datetime import date
    from sqlalchemy import select
    from app.models.search_quota import SearchQuota

    today = date.today()

    try:
        result = await db.execute(
            select(SearchQuota).where(
                SearchQuota.user_id == user_id,
                SearchQuota.search_date == today,
            )
        )
        quota = result.scalar_one_or_none()

        if quota:
            quota.search_count += 1
        else:
            quota = SearchQuota(
                user_id=user_id,
                search_date=today,
                search_count=1,
            )
            db.add(quota)

        await db.commit()
    except Exception as e:
        logger.warning(f"Failed to track search quota for user {user_id}: {e}")
        # Don't fail the request if quota tracking fails
        await db.rollback()
