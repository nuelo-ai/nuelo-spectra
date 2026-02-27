"""Pydantic schemas for admin user management endpoints."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


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
    api_query_count: int
    last_message_at: datetime | None


class ActivityMonth(BaseModel):
    """Single month of activity data."""

    month: str  # ISO format "2026-01"
    message_count: int
    session_count: int
    api_query_count: int = 0


class UserActivityResponse(BaseModel):
    """Activity timeline for a user."""

    user_id: UUID
    months: list[ActivityMonth]


class ActivateDeactivateResponse(BaseModel):
    """Response for activate/deactivate user actions."""

    user_id: UUID
    is_active: bool
    message: str


class PasswordResetTriggerResponse(BaseModel):
    """Response for admin-triggered password reset."""

    user_id: UUID
    email: str
    message: str


class CreditAdjustRequest(BaseModel):
    """Request for admin credit adjustment."""

    amount: Decimal = Field(description="Positive to add, negative to deduct")
    reason: str = Field(..., min_length=1, max_length=500)


class DeleteChallengeResponse(BaseModel):
    """Response containing a challenge code for delete confirmation."""

    challenge_code: str
    expires_in: int  # seconds


class DeleteConfirmRequest(BaseModel):
    """Request to confirm user deletion with challenge code."""

    challenge_code: str = Field(..., min_length=6, max_length=6)


class BulkUserActionRequest(BaseModel):
    """Request for bulk activate/deactivate actions."""

    user_ids: list[UUID] = Field(..., min_length=1, max_length=100)


class BulkTierChangeRequest(BaseModel):
    """Request for bulk tier change."""

    user_ids: list[UUID] = Field(..., min_length=1, max_length=100)
    user_class: str


class BulkCreditAdjustRequest(BaseModel):
    """Request for bulk credit adjustment (set exact OR add/deduct delta)."""

    user_ids: list[UUID] = Field(..., min_length=1, max_length=100)
    amount: Decimal | None = None  # Set exact amount (mutually exclusive with delta)
    delta: Decimal | None = None  # Add/deduct from current (mutually exclusive with amount)
    reason: str = Field(..., min_length=1, max_length=500)

    @model_validator(mode="after")
    def exactly_one_mode(self):
        if (self.amount is None) == (self.delta is None):
            raise ValueError(
                "Provide exactly one of 'amount' (set exact) or 'delta' (add/deduct)"
            )
        return self


class BulkDeleteRequest(BaseModel):
    """Request for bulk delete with challenge code confirmation."""

    user_ids: list[UUID] = Field(..., min_length=1, max_length=100)
    challenge_code: str = Field(..., min_length=6, max_length=6)


class BulkActionResult(BaseModel):
    """Result of a bulk operation with success/failure counts."""

    succeeded: int
    failed: int
    errors: list[dict]  # [{user_id, error}]
