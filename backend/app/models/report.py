from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import TYPE_CHECKING

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.collection import Collection
    from app.models.pulse_run import PulseRun


class Report(Base):
    """A report generated from Pulse detection results."""

    __tablename__ = "reports"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    collection_id: Mapped[UUID] = mapped_column(
        ForeignKey("collections.id", ondelete="CASCADE"),
        index=True
    )
    pulse_run_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("pulse_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    report_type: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    collection: Mapped["Collection"] = relationship(
        "Collection", back_populates="reports"
    )
    pulse_run: Mapped["PulseRun"] = relationship(
        "PulseRun", back_populates="reports"
    )
