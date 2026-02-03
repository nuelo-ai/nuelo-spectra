"""Chat message schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class ChatMessageCreate(BaseModel):
    """Request schema for creating a chat message."""

    content: str
    role: str = "user"

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role is either 'user' or 'assistant'."""
        if v not in {"user", "assistant"}:
            raise ValueError("Role must be either 'user' or 'assistant'")
        return v


class ChatMessageResponse(BaseModel):
    """Response schema for a chat message."""

    id: UUID
    file_id: UUID
    role: str
    content: str
    message_type: str | None
    metadata_json: dict | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatMessageList(BaseModel):
    """Response schema for list of chat messages."""

    messages: list[ChatMessageResponse]
    total: int


class ChatQueryRequest(BaseModel):
    """Request schema for AI chat query."""

    content: str


class ChatAgentResponse(BaseModel):
    """Response schema for AI chat query with agent execution details."""

    user_query: str
    generated_code: str | None = None
    execution_result: str | None = None
    analysis: str
    error: str | None = None
    retry_count: int = 0
