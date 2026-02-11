from sqlalchemy import String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import TYPE_CHECKING, Any, Optional

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.file import File
    from app.models.chat_session import ChatSession


class ChatMessage(Base):
    """Chat message model with user and file isolation.

    Note: session_id is the new primary relationship for multi-file conversations.
    file_id is kept for backward compatibility during migration.
    """

    __tablename__ = "chat_messages"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    file_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("files.id", ondelete="SET NULL"),
        index=True,
        nullable=True
    )
    session_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=True  # Nullable for migration compatibility
    )
    role: Mapped[str] = mapped_column(String(20))  # user, assistant
    content: Mapped[str] = mapped_column(Text)
    message_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="chat_messages")
    file: Mapped[Optional["File"]] = relationship("File", back_populates="chat_messages")
    session: Mapped[Optional["ChatSession"]] = relationship("ChatSession", back_populates="messages")
