from sqlalchemy import Table, Column, ForeignKey, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import TYPE_CHECKING

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.file import File
    from app.models.chat_message import ChatMessage


# Association table for M2M relationship between ChatSession and File
session_files = Table(
    "session_files",
    Base.metadata,
    Column(
        "session_id",
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        primary_key=True
    ),
    Column(
        "file_id",
        ForeignKey("files.id", ondelete="CASCADE"),
        primary_key=True
    )
)


class ChatSession(Base):
    """Chat session model for multi-file conversations with user isolation."""

    __tablename__ = "chat_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    title: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    user_modified: Mapped[bool] = mapped_column(default=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="chat_sessions")
    files: Mapped[list["File"]] = relationship(
        "File",
        secondary=session_files,
        back_populates="sessions"
    )
    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at"
    )
