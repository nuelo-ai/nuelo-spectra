"""Pydantic schemas for API key endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)


class ApiKeyCreateResponse(BaseModel):
    id: UUID
    name: str
    key_prefix: str
    full_key: str  # ONLY returned from POST -- never from GET
    created_at: datetime


class ApiKeyListItem(BaseModel):
    id: UUID
    name: str
    description: str | None
    key_prefix: str
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None

    model_config = {"from_attributes": True}
