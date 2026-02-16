"""Admin authentication and audit log schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class AdminLoginRequest(BaseModel):
    """Request schema for admin login."""

    email: EmailStr
    password: str = Field(..., min_length=8)


class AdminLoginResponse(BaseModel):
    """Response schema for admin login."""

    access_token: str
    token_type: str = "bearer"


class AdminAuditLogEntry(BaseModel):
    """Schema for admin audit log entries."""

    id: UUID
    admin_id: UUID | None
    action: str
    target_type: str
    target_id: str | None
    details: dict | None
    ip_address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
