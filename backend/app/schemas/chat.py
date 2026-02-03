"""Chat message schemas."""

from datetime import datetime
from enum import Enum
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


class StreamEventType(str, Enum):
    """SSE event types for streaming agent execution status."""

    # Status events - agent phase transitions
    CODING_STARTED = "coding_started"
    VALIDATION_STARTED = "validation_started"
    EXECUTION_STARTED = "execution_started"
    ANALYSIS_STARTED = "analysis_started"

    # Progress events
    PROGRESS = "progress"
    RETRY = "retry"

    # Content events
    CONTENT_CHUNK = "content_chunk"
    NODE_COMPLETE = "node_complete"

    # Terminal events
    COMPLETED = "completed"
    ERROR = "error"


class StreamEvent(BaseModel):
    """Typed SSE event payload for agent streaming."""

    type: StreamEventType
    event: str | None = None  # Specific event name (coding_started, etc.)
    message: str | None = None  # User-facing message
    step: int | None = None  # Current step (1-4)
    total_steps: int | None = None  # Total steps (4)
    node: str | None = None  # Node name for node_complete events
    text: str | None = None  # Content text for chunk events
    attempt: int | None = None  # Retry attempt number
    max_attempts: int | None = None  # Max retry attempts
    data: dict | None = None  # Additional data payload
