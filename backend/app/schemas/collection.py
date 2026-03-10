"""Pydantic v2 schemas for collections, collection files, and reports."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# --- Request schemas ---


class CollectionCreate(BaseModel):
    """Create a new collection."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class CollectionUpdate(BaseModel):
    """Partial update for a collection."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class FileLinkRequest(BaseModel):
    """Request to link a file to a collection."""

    file_id: UUID


# --- Response schemas ---


class CollectionListItem(BaseModel):
    """Collection summary with aggregated counts for list view."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    file_count: int
    signal_count: int


class CollectionDetailResponse(BaseModel):
    """Collection detail with full aggregated counts."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    file_count: int
    signal_count: int
    report_count: int


class CollectionFileResponse(BaseModel):
    """A file linked to a collection with file metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    file_id: UUID
    added_at: datetime
    filename: str
    file_size: int | None = None
    data_summary: str | None = None


class ReportListItem(BaseModel):
    """Report summary for list view."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    report_type: str
    created_at: datetime
    pulse_run_id: UUID | None


class ReportDetailResponse(BaseModel):
    """Report detail with signal count."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    report_type: str
    content: str | None
    created_at: datetime
    pulse_run_id: UUID | None
    signal_count: int
