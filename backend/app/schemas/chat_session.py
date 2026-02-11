"""Chat session schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ChatSessionCreate(BaseModel):
    """Request schema for creating a chat session."""

    title: str = "New Chat"


class ChatSessionUpdate(BaseModel):
    """Request schema for updating a chat session."""

    title: str | None = None


class ChatSessionFileLink(BaseModel):
    """Request schema for linking/unlinking a file to/from a session."""

    file_id: UUID


class FileBasicInfo(BaseModel):
    """Basic file information for session detail view."""

    id: UUID
    original_filename: str
    file_type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatSessionResponse(BaseModel):
    """Response schema for a chat session."""

    id: UUID
    user_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    file_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ChatSessionDetail(ChatSessionResponse):
    """Detailed response schema for a chat session with files."""

    files: list[FileBasicInfo] = []


class ChatSessionList(BaseModel):
    """Response schema for list of chat sessions."""

    sessions: list[ChatSessionResponse]
    total: int
