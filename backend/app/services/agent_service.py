"""Service layer for agent invocation and orchestration."""

import os
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.onboarding import OnboardingAgent
from app.config import get_settings
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
