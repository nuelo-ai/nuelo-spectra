"""Pydantic schemas for invitation management."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class CreateInviteRequest(BaseModel):
    """Request schema for creating an invitation."""

    email: EmailStr


class InviteResponse(BaseModel):
    """Response schema for a single invitation."""

    id: UUID
    email: str
    status: str
    created_at: datetime
    expires_at: datetime
    accepted_at: datetime | None = None


class InviteListResponse(BaseModel):
    """Paginated list of invitations."""

    items: list[InviteResponse]
    total: int
    page: int
    page_size: int


class InviteDetailResponse(BaseModel):
    """Detailed invitation response with inviter info."""

    id: UUID
    email: str
    status: str
    created_at: datetime
    expires_at: datetime
    accepted_at: datetime | None = None
    invited_by: UUID | None = None


class DuplicateInviteWarning(BaseModel):
    """Warning response for duplicate pending invitation."""

    message: str
    existing_invite_id: UUID
