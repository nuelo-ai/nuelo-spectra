"""File response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FileUploadResponse(BaseModel):
    """Response schema for file upload."""

    id: UUID
    original_filename: str
    file_size: int
    file_type: str
    created_at: datetime
    data_summary: str | None = None
    user_context: str | None = None

    model_config = ConfigDict(from_attributes=True)


class FileListItem(BaseModel):
    """Response schema for file list item."""

    id: UUID
    original_filename: str
    file_size: int
    file_type: str
    created_at: datetime
    updated_at: datetime
    has_summary: bool = False

    model_config = ConfigDict(from_attributes=True)


class FileDetailResponse(BaseModel):
    """Response schema for file detail."""

    id: UUID
    original_filename: str
    stored_filename: str
    file_size: int
    file_type: str
    created_at: datetime
    updated_at: datetime
    data_summary: str | None = None
    user_context: str | None = None

    model_config = ConfigDict(from_attributes=True)
