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

    # Update file record with summary and context
    file_record.data_summary = result.data_summary
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
    file_id: UUID,
    user_id: UUID,
    user_query: str
) -> dict:
    """Run chat query through the full agent pipeline.

    This function orchestrates the complete AI analysis workflow:
    1. Load file and verify onboarding completed
    2. Invoke LangGraph workflow (Coding Agent -> Code Checker -> Execute -> Data Analysis)
    3. Save user message and agent response to chat history
    4. Return structured response with code, execution result, and analysis

    Args:
        db: Database session
        file_id: File UUID
        user_id: User UUID (for access control)
        user_query: User's natural language query

    Returns:
        dict: Agent response with user_query, generated_code, execution_result,
              analysis, error (if any), and retry_count

    Raises:
        HTTPException: If file not found or not yet onboarded (data_summary is None)
    """
    # Load file record with access control
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

    # Get or create compiled graph
    graph = get_or_create_graph()

    # Build thread ID for per-file per-user memory isolation
    thread_id = f"file_{file_id}_user_{user_id}"
    config = {"configurable": {"thread_id": thread_id}}

    # Build initial state
    initial_state = {
        "file_id": str(file_id),
        "user_id": str(user_id),
        "user_query": user_query,
        "data_summary": file_record.data_summary,
        "user_context": file_record.user_context or "",
        "file_path": file_record.file_path,
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

    # Invoke graph
    result = await graph.ainvoke(initial_state, config)

    # Save user message to chat history
    await ChatService.create_message(
        db,
        file_id,
        user_id,
        user_query,
        role="user"
    )

    # Save assistant response with metadata
    final_response_text = result.get("final_response") or result.get("analysis", "")
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
            "error": result.get("error")
        }
    )

    # Return structured response
    return {
        "user_query": user_query,
        "generated_code": result.get("generated_code"),
        "execution_result": result.get("execution_result"),
        "analysis": final_response_text,
        "error": result.get("error"),
        "retry_count": result.get("error_count", 0)
    }


async def run_chat_query_stream(
    db: AsyncSession,
    file_id: UUID,
    user_id: UUID,
    user_query: str
) -> AsyncGenerator[dict, None]:
    """Run chat query through agent pipeline and yield SSE events.

    This streaming version of run_chat_query converts the synchronous graph.ainvoke()
    to graph.astream() and yields structured event dicts for the SSE endpoint to format.

    Events yielded:
    - Custom status events from get_stream_writer() (coding_started, validation_started, etc.)
    - Node completion events with intermediate results (generated_code, execution_result, etc.)
    - Error events on failure
    - Completion event on success

    Chat history is saved atomically on successful stream completion with metadata.
    Failed streams save nothing to the database (clean failure state per CONTEXT.md).

    Args:
        db: Database session (used for initial file validation only)
        file_id: File UUID
        user_id: User UUID (for access control)
        user_query: User's natural language query

    Yields:
        dict: Event dictionaries with type, message, and event-specific fields

    Raises:
        Yields error event dict (does not raise exceptions)
    """
    logger.info(f"Starting chat stream for file_id={file_id}, user_id={user_id}, query={user_query[:50]}...")

    # Load file record with access control (uses injected db for quick read)
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

    # Get or create compiled graph
    graph = get_or_create_graph()

    # Build thread ID for per-file per-user memory isolation
    thread_id = f"file_{file_id}_user_{user_id}"
    config = {"configurable": {"thread_id": thread_id}}

    # Build initial state (identical to run_chat_query)
    initial_state = {
        "file_id": str(file_id),
        "user_id": str(user_id),
        "user_query": user_query,
        "data_summary": file_record.data_summary,
        "user_context": file_record.user_context or "",
        "file_path": file_record.file_path,
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
                # These are status, progress, and retry events emitted by agents
                yield chunk
            elif mode == "updates":
                # State delta after a node completes
                # chunk is dict keyed by node name: {"coding_agent": {"generated_code": "..."}}
                for node_name, update in chunk.items():
                    final_state.update(update)
                    # Yield node completion with relevant fields only
                    # (filter to user-visible data, exclude internal state)
                    yield {
                        "type": "node_complete",
                        "node": node_name,
                        **{k: v for k, v in update.items()
                           if k in ("generated_code", "execution_result",
                                    "analysis", "final_response", "error")}
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

        async with async_session_maker() as save_db:
            # Save user message
            await ChatService.create_message(
                save_db, file_id, user_id, user_query, role="user"
            )
            # Save assistant response with stream metadata
            response_text = final_state.get("final_response") or final_state.get("analysis", "")
            await ChatService.create_message(
                save_db, file_id, user_id, response_text,
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
