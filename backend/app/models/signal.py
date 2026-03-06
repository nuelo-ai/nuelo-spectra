from sqlalchemy import String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import TYPE_CHECKING

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.collection import Collection
    from app.models.pulse_run import PulseRun


class Signal(Base):
    """A detection signal produced by Pulse analysis."""

    __tablename__ = "signals"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    collection_id: Mapped[UUID] = mapped_column(
        ForeignKey("collections.id", ondelete="CASCADE"),
        index=True
    )
    pulse_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("pulse_runs.id", ondelete="CASCADE"),
        index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    severity: Mapped[str] = mapped_column(String(20))
    category: Mapped[str] = mapped_column(String(50))
    analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    chart_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    chart_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    collection: Mapped["Collection"] = relationship(
        "Collection", back_populates="signals"
    )
    pulse_run: Mapped["PulseRun"] = relationship(
        "PulseRun", back_populates="signals"
    )
