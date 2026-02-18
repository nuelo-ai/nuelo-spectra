"""Pydantic schemas for admin audit log listing."""

import math
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AuditLogEntry(BaseModel):
    """Single audit log entry with admin email resolution."""

    id: UUID
    admin_id: UUID | None
    admin_email: str | None
    action: str
    target_type: str | None
    target_id: str | None
    details: dict | None
    ip_address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    """Paginated audit log response."""

    items: list[AuditLogEntry]
    total: int
    page: int
    page_size: int
    total_pages: int
