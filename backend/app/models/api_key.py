from sqlalchemy import String, Text, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import TYPE_CHECKING

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class ApiKey(Base):
    """API key model for programmatic access to Spectra."""

    __tablename__ = "api_keys"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_prefix: Mapped[str] = mapped_column(String(16))
    token_hash: Mapped[str] = mapped_column(
        String(128), unique=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    scopes: Mapped[list[str] | None] = mapped_column(
        PG_ARRAY(String), nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Admin tracking fields (Phase 39)
    created_by_admin_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Admin who created this key on behalf of user (NULL = self-created)",
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when key was revoked (is_active set to False)",
    )
    total_credits_used: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        server_default="0",
        comment="Denormalized credit usage counter (populated by Phase 40)",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="api_keys",
        foreign_keys=[user_id],
    )
    created_by_admin: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[created_by_admin_id],
    )
