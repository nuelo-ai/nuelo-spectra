"""Chat session API endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.dependencies import CurrentUser, DbSession
from app.schemas.chat import ChatMessageList, ChatMessageResponse
from app.schemas.chat_session import (
    ChatSessionCreate,
    ChatSessionDetail,
    ChatSessionFileLink,
    ChatSessionList,
    ChatSessionResponse,
    ChatSessionUpdate,
    FileBasicInfo
)
from app.services.chat import ChatService
from app.services.chat_session import ChatSessionService

router = APIRouter(prefix="/sessions", tags=["Chat Sessions"])


@router.post("/", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    body: ChatSessionCreate,
    current_user: CurrentUser,
    db: DbSession
) -> ChatSessionResponse:
    """Create a new chat session.

    Args:
        body: Session creation data (title)
        current_user: Authenticated user
        db: Database session

    Returns:
        Created session
    """
    session = await ChatSessionService.create_session(
        db, current_user.id, body.title
    )

    return ChatSessionResponse(
        **{k: v for k, v in session.__dict__.items() if not k.startswith('_')},
        file_count=0
    )


@router.get("/", response_model=ChatSessionList)
async def list_sessions(
    current_user: CurrentUser,
    db: DbSession,
    limit: int = 50,
    offset: int = 0
) -> ChatSessionList:
    """List chat sessions for the current user.

    Args:
        current_user: Authenticated user
        db: Database session
        limit: Maximum number of sessions to return
        offset: Number of sessions to skip

    Returns:
        Paginated list of chat sessions with file counts
    """
    sessions, total = await ChatSessionService.list_user_sessions(
        db, current_user.id, limit, offset
    )

    return ChatSessionList(
        sessions=[
            ChatSessionResponse(
                **{k: v for k, v in s.__dict__.items() if not k.startswith('_')},
                file_count=len(s.files)
            )
            for s in sessions
        ],
        total=total
    )


@router.get("/{session_id}", response_model=ChatSessionDetail)
async def get_session(
    session_id: UUID,
    current_user: CurrentUser,
    db: DbSession
) -> ChatSessionDetail:
    """Get a specific session with linked files.

    Args:
        session_id: Session UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        Session detail with files

    Raises:
        HTTPException: 404 if session not found or not owned by user
    """
    session = await ChatSessionService.get_user_session(db, session_id, current_user.id)

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return ChatSessionDetail(
        **{k: v for k, v in session.__dict__.items() if not k.startswith('_')},
        files=[FileBasicInfo.model_validate(f) for f in session.files],
        file_count=len(session.files)
    )


@router.patch("/{session_id}", response_model=ChatSessionResponse)
async def update_session(
    session_id: UUID,
    body: ChatSessionUpdate,
    current_user: CurrentUser,
    db: DbSession
) -> ChatSessionResponse:
    """Update a chat session.

    Args:
        session_id: Session UUID
        body: Session update data (title)
        current_user: Authenticated user
        db: Database session

    Returns:
        Updated session

    Raises:
        HTTPException: 404 if session not found
    """
    session = await ChatSessionService.update_session(
        db, session_id, current_user.id, body.title
    )

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return ChatSessionResponse(
        **{k: v for k, v in session.__dict__.items() if not k.startswith('_')},
        file_count=len(session.files)
    )


@router.post("/{session_id}/generate-title", response_model=ChatSessionResponse)
async def generate_title(
    session_id: UUID,
    current_user: CurrentUser,
    db: DbSession
) -> ChatSessionResponse:
    """Generate a session title using LLM from the first user message in the session.

    Security: No request body accepted. The service reads the first user
    message directly from the database, preventing LLM proxy abuse.

    Only works if user hasn't manually renamed (user_modified=False).
    Fails silently -- returns current session even if LLM fails.
    """
    session = await ChatSessionService.generate_session_title(
        db, session_id, current_user.id
    )

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return ChatSessionResponse(
        **{k: v for k, v in session.__dict__.items() if not k.startswith('_')},
        file_count=len(session.files) if hasattr(session, 'files') and session.files else 0
    )


@router.delete("/{session_id}")
async def delete_session(
    session_id: UUID,
    current_user: CurrentUser,
    db: DbSession
) -> dict:
    """Delete a chat session and its messages.

    Args:
        session_id: Session UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        Confirmation message

    Raises:
        HTTPException: 404 if session not found

    Note:
        Cascade deletes related messages but not files.
    """
    deleted = await ChatSessionService.delete_session(db, session_id, current_user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return {"message": "Session deleted"}


@router.post("/{session_id}/files", response_model=ChatSessionDetail, status_code=status.HTTP_201_CREATED)
async def link_file_to_session(
    session_id: UUID,
    body: ChatSessionFileLink,
    current_user: CurrentUser,
    db: DbSession
) -> ChatSessionDetail:
    """Link a file to a chat session.

    Args:
        session_id: Session UUID
        body: File link data (file_id)
        current_user: Authenticated user
        db: Database session

    Returns:
        Updated session detail with files

    Raises:
        HTTPException: 404 if session or file not found
        HTTPException: 400 if file already linked or limit exceeded
    """
    try:
        session = await ChatSessionService.link_file_to_session(
            db, session_id, body.file_id, current_user.id
        )
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

    return ChatSessionDetail(
        **{k: v for k, v in session.__dict__.items() if not k.startswith('_')},
        files=[FileBasicInfo.model_validate(f) for f in session.files],
        file_count=len(session.files)
    )


@router.delete("/{session_id}/files/{file_id}", response_model=ChatSessionDetail)
async def unlink_file_from_session(
    session_id: UUID,
    file_id: UUID,
    current_user: CurrentUser,
    db: DbSession
) -> ChatSessionDetail:
    """Unlink a file from a chat session.

    Args:
        session_id: Session UUID
        file_id: File UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        Updated session detail

    Raises:
        HTTPException: 404 if session not found or file not linked

    Note:
        This does NOT delete messages - messages stay with session.
    """
    try:
        session = await ChatSessionService.unlink_file_from_session(
            db, session_id, file_id, current_user.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    return ChatSessionDetail(
        **{k: v for k, v in session.__dict__.items() if not k.startswith('_')},
        files=[FileBasicInfo.model_validate(f) for f in session.files],
        file_count=len(session.files)
    )


@router.get("/{session_id}/messages", response_model=ChatMessageList)
async def list_session_messages(
    session_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
    limit: int = 50,
    offset: int = 0
) -> ChatMessageList:
    """List chat messages for a session.

    Args:
        session_id: Session UUID
        current_user: Authenticated user
        db: Database session
        limit: Maximum number of messages to return
        offset: Number of messages to skip

    Returns:
        Paginated list of chat messages

    Raises:
        HTTPException: 404 if session not found
    """
    # Verify session exists and belongs to user
    session = await ChatSessionService.get_user_session(db, session_id, current_user.id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Get messages
    messages, total = await ChatService.list_session_messages(
        db, session_id, current_user.id, limit, offset
    )

    return ChatMessageList(
        messages=[ChatMessageResponse.model_validate(m) for m in messages],
        total=total
    )
