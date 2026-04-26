"""PaymentHistory model for recording all payment events."""

from sqlalchemy import String, DateTime, Integer, ForeignKey, NUMERIC
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.models.base import Base


class PaymentHistory(Base):
    """One row per payment event (subscription, top-up, refund)."""

    __tablename__ = "payment_history"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True
    )
    amount_cents: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="usd")
    payment_type: Mapped[str] = mapped_column(String(30))  # subscription, topup, refund
    credit_amount: Mapped[float | None] = mapped_column(
        NUMERIC(10, 1), nullable=True
    )
    status: Mapped[str] = mapped_column(String(30))  # succeeded, failed, refunded, partial_refund
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
