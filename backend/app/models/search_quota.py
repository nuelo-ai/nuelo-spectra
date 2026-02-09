"""Search quota model for daily per-user search usage tracking."""

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SearchQuota(Base):
    """Track daily search usage per user.

    Uses a composite primary key of (user_id, search_date) to track
    how many web searches each user has performed on a given day.
    """

    __tablename__ = "search_quotas"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    search_date: Mapped[date] = mapped_column(Date, primary_key=True)
    search_count: Mapped[int] = mapped_column(Integer, default=0)
