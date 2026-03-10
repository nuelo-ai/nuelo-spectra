"""Pydantic schemas for platform settings and tier summary APIs."""

from pydantic import BaseModel, ConfigDict, model_validator


class SettingsResponse(BaseModel):
    """Response schema for GET /api/admin/settings."""

    allow_public_signup: bool
    default_user_class: str
    invite_expiry_days: int
    default_credit_cost: float
    max_pending_invites: int
    workspace_credit_cost_pulse: float


class SettingsUpdateRequest(BaseModel):
    """Request schema for PATCH /api/admin/settings.

    All fields are optional; at least one must be provided.
    Extra fields are forbidden.
    """

    model_config = ConfigDict(extra="forbid")

    allow_public_signup: bool | None = None
    default_user_class: str | None = None
    invite_expiry_days: int | None = None
    default_credit_cost: float | None = None
    max_pending_invites: int | None = None
    workspace_credit_cost_pulse: float | None = None

    @model_validator(mode="after")
    def at_least_one_field(self) -> "SettingsUpdateRequest":
        """Ensure at least one field is provided."""
        if all(
            v is None
            for v in [
                self.allow_public_signup,
                self.default_user_class,
                self.invite_expiry_days,
                self.default_credit_cost,
                self.max_pending_invites,
                self.workspace_credit_cost_pulse,
            ]
        ):
            raise ValueError("At least one setting must be provided")
        return self


class TierChangeRequest(BaseModel):
    """Request schema for PUT /api/admin/tiers/users/{user_id}."""

    user_class: str


class TierSummaryResponse(BaseModel):
    """Response schema for GET /api/admin/tiers."""

    name: str
    display_name: str
    credits: int
    reset_policy: str
    user_count: int
