"""DiscountCode model for admin-managed discount/promotion codes."""

from sqlalchemy import String, DateTime, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.models.base import Base


class DiscountCode(Base):
    """Admin-created discount codes synced with Stripe coupons/promotion codes."""

    __tablename__ = "discount_codes"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    discount_type: Mapped[str] = mapped_column(String(20))  # "percent_off" or "amount_off"
    discount_value: Mapped[int] = mapped_column(Integer)  # percent (1-100) or cents (> 0)
    currency: Mapped[str] = mapped_column(String(3), default="usd")
    stripe_coupon_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_promotion_code_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    max_redemptions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    times_redeemed: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
