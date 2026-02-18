from sqlalchemy import DateTime, ForeignKey, NUMERIC
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.models.base import Base


class UserCredit(Base):
    """Per-user credit balance for metered usage."""

    __tablename__ = "user_credits"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True
    )
    balance: Mapped[float] = mapped_column(NUMERIC(10, 1), default=0)
    last_reset_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
