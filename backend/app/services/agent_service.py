"""Service layer for agent invocation and orchestration."""

import os
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import get_or_create_graph
from app.agents.onboarding import OnboardingAgent
from app.config import get_settings
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
