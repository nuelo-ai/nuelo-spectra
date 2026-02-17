"""Authentication request and response schemas."""

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    """Request schema for user signup."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str | None = None
    last_name: str | None = None
    invite_token: str | None = None


class LoginRequest(BaseModel):
    """Request schema for user login."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Response schema for token endpoints."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Request schema for token refresh."""

    refresh_token: str


class MessageResponse(BaseModel):
    """Generic message response schema."""

    message: str


class ForgotPasswordRequest(BaseModel):
    """Request schema for password reset request."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Request schema for password reset."""

    token: str
    new_password: str = Field(..., min_length=8)


class ProfileUpdateRequest(BaseModel):
    """Request schema for profile update."""

    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)

    def model_post_init(self, __context) -> None:
        """Validate that at least one field is provided."""
        if self.first_name is None and self.last_name is None:
            raise ValueError("At least one field (first_name or last_name) must be provided")


class ChangePasswordRequest(BaseModel):
    """Request schema for password change."""

    current_password: str
    new_password: str = Field(..., min_length=8)


class InviteRegisterRequest(BaseModel):
    """Request schema for invite-based registration."""

    token: str
    display_name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8)


class InviteValidateResponse(BaseModel):
    """Response schema for invite token validation."""

    email: str
    valid: bool = True
