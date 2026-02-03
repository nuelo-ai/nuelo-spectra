"""Chat message API endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.dependencies import CurrentUser, DbSession
from app.schemas.chat import (
    ChatAgentResponse,
    ChatMessageCreate,
    ChatMessageList,
    ChatMessageResponse,
    ChatQueryRequest
)
from app.services import agent_service
from app.services.chat import ChatService
from app.services.file import FileService

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.get("/{file_id}/messages", response_model=ChatMessageList)
async def list_messages(
    file_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
    limit: int = 50,
    offset: int = 0
) -> ChatMessageList:
    """List chat messages for a specific file.

    Args:
        file_id: File UUID
        current_user: Authenticated user
        db: Database session
        limit: Maximum number of messages to return
        offset: Number of messages to skip

    Returns:
        Paginated list of chat messages

    Raises:
        HTTPException: 404 if file not found or doesn't belong to user
    """
    # Verify file ownership
    file = await FileService.get_user_file(db, file_id, current_user.id)
    if file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Get messages
    messages, total = await ChatService.list_file_messages(
        db, file_id, current_user.id, limit, offset
    )

    return ChatMessageList(
        messages=[ChatMessageResponse.model_validate(m) for m in messages],
        total=total
    )


@router.post("/{file_id}/messages", response_model=ChatMessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    file_id: UUID,
    body: ChatMessageCreate,
    current_user: CurrentUser,
    db: DbSession
) -> ChatMessageResponse:
    """Create a new chat message for a specific file (direct message, no AI).

    This endpoint is for direct message creation without AI processing.
    For AI-powered queries, use POST /chat/{file_id}/query instead.

    Args:
        file_id: File UUID
        body: Message content and role
        current_user: Authenticated user
        db: Database session

    Returns:
        Created message

    Raises:
        HTTPException: 404 if file not found or doesn't belong to user
    """
    # Verify file ownership
    file = await FileService.get_user_file(db, file_id, current_user.id)
    if file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Create message
    message = await ChatService.create_message(
        db, file_id, current_user.id, body.content, body.role
    )

    return ChatMessageResponse.model_validate(message)


@router.post("/{file_id}/query", response_model=ChatAgentResponse)
async def query_with_ai(
    file_id: UUID,
    body: ChatQueryRequest,
    current_user: CurrentUser,
    db: DbSession
) -> ChatAgentResponse:
    """Run AI-powered query through the complete agent pipeline.

    This endpoint orchestrates the full analysis workflow:
    1. Coding Agent generates Python code from natural language query
    2. Code Checker validates code with AST + LLM logical check
    3. Execute runs code in restricted namespace (stub, Phase 5 adds sandbox)
    4. Data Analysis Agent interprets results in natural language

    The response includes generated code, execution result, and AI explanation.
    Both user query and agent response are automatically saved to chat history.

    Args:
        file_id: File UUID
        body: Chat query request with user's natural language query
        current_user: Authenticated user
        db: Database session

    Returns:
        Agent response with code, execution result, and analysis

    Raises:
        HTTPException: 404 if file not found or doesn't belong to user
        HTTPException: 400 if file hasn't been onboarded yet
    """
    # Verify file ownership (done inside agent_service.run_chat_query)
    # Run chat query through agent pipeline
    result = await agent_service.run_chat_query(
        db, file_id, current_user.id, body.content
    )

    return ChatAgentResponse(**result)
