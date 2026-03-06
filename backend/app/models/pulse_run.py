from sqlalchemy import Table, Column, String, Text, DateTime, ForeignKey, NUMERIC
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import TYPE_CHECKING

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.collection import Collection
    from app.models.file import File
    from app.models.signal import Signal
    from app.models.report import Report


# Association table for M2M relationship between PulseRun and File
pulse_run_files = Table(
    "pulse_run_files",
    Base.metadata,
    Column(
        "pulse_run_id",
        ForeignKey("pulse_runs.id", ondelete="CASCADE"),
        primary_key=True
    ),
    Column(
        "file_id",
        ForeignKey("files.id", ondelete="CASCADE"),
        primary_key=True
    )
)


class PulseRun(Base):
    """Tracks a single Pulse detection execution against a collection."""

    __tablename__ = "pulse_runs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    collection_id: Mapped[UUID] = mapped_column(
        ForeignKey("collections.id", ondelete="CASCADE"),
        index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="pending")
    credit_cost: Mapped[float] = mapped_column(NUMERIC(10, 1))
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    collection: Mapped["Collection"] = relationship(
        "Collection", back_populates="pulse_runs"
    )
    files: Mapped[list["File"]] = relationship(
        "File", secondary=pulse_run_files
    )
    signals: Mapped[list["Signal"]] = relationship(
        "Signal",
        back_populates="pulse_run",
        cascade="all, delete-orphan"
    )
    reports: Mapped[list["Report"]] = relationship(
        "Report", back_populates="pulse_run"
    )
