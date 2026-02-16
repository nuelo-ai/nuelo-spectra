"""Pydantic schemas for admin user management endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserSummary(BaseModel):
    """User summary for list view."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    first_name: str | None
    last_name: str | None
    is_active: bool
    user_class: str
    created_at: datetime
    last_login_at: datetime | None
    credit_balance: float  # From LEFT JOIN with user_credits


class UserListResponse(BaseModel):
    """Paginated user list response."""

    users: list[UserSummary]
    total: int
    page: int
    per_page: int
    total_pages: int


class UserDetailResponse(BaseModel):
    """Full user detail with aggregated counts."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    first_name: str | None
    last_name: str | None
    is_active: bool
    is_admin: bool
    user_class: str
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None
    credit_balance: float
    file_count: int
    session_count: int
    message_count: int
    last_message_at: datetime | None


class ActivityMonth(BaseModel):
    """Single month of activity data."""

    month: str  # ISO format "2026-01"
    message_count: int
    session_count: int


class UserActivityResponse(BaseModel):
    """Activity timeline for a user."""

    user_id: UUID
    months: list[ActivityMonth]
