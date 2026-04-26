"""User response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    """Response schema for user data."""

    id: UUID
    email: str
    first_name: str | None
    last_name: str | None
    is_active: bool
    is_admin: bool = False
    created_at: datetime
    user_class: str = "free_trial"
    trial_expires_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
