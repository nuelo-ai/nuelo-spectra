"""Password reset token model for database-backed single-use tokens."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import String, DateTime, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PasswordResetToken(Base):
    """Store hashed password reset tokens with expiry and usage tracking.

    Tokens are stored as SHA-256 hashes for security. The raw token is sent
    to the user via email and never stored. On verification, the submitted
    token is hashed and compared against the stored hash.
    """

    __tablename__ = "password_reset_tokens"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), index=True)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_password_reset_tokens_email_active", "email", "is_active"),
    )
