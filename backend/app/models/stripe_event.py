"""StripeEvent model for webhook idempotency deduplication."""

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.models.base import Base


class StripeEvent(Base):
    """Tracks processed Stripe webhook events to prevent duplicate processing."""

    __tablename__ = "stripe_events"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    stripe_event_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True
    )
    event_type: Mapped[str] = mapped_column(String(100))
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
