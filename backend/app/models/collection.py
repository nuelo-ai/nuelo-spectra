from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import TYPE_CHECKING

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.file import File
    from app.models.signal import Signal
    from app.models.report import Report
    from app.models.pulse_run import PulseRun


class Collection(Base):
    """Collection of files for Pulse detection analysis."""

    __tablename__ = "collections"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="collections")
    collection_files: Mapped[list["CollectionFile"]] = relationship(
        "CollectionFile",
        back_populates="collection",
        cascade="all, delete-orphan"
    )
    pulse_runs: Mapped[list["PulseRun"]] = relationship(
        "PulseRun",
        back_populates="collection",
        cascade="all, delete-orphan"
    )
    signals: Mapped[list["Signal"]] = relationship(
        "Signal",
        back_populates="collection",
        cascade="all, delete-orphan"
    )
    reports: Mapped[list["Report"]] = relationship(
        "Report",
        back_populates="collection",
        cascade="all, delete-orphan"
    )


class CollectionFile(Base):
    """Junction between Collection and File with metadata."""

    __tablename__ = "collection_files"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    collection_id: Mapped[UUID] = mapped_column(
        ForeignKey("collections.id", ondelete="CASCADE"),
        index=True
    )
    file_id: Mapped[UUID] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE"),
        index=True
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    collection: Mapped["Collection"] = relationship(
        "Collection", back_populates="collection_files"
    )
    file: Mapped["File"] = relationship("File")
