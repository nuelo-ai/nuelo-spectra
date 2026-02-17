"""Authentication API endpoints."""

import hashlib
import time
from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.database import get_db
from app.dependencies import CurrentUser
from app.models.password_reset import PasswordResetToken
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    InviteRegisterRequest,
    InviteValidateResponse,
    LoginRequest,
    MessageResponse,
    ProfileUpdateRequest,
    RefreshRequest,
    ResetPasswordRequest,
    SignupRequest,
    TokenResponse
)
from app.schemas.user import UserResponse
from app.services import auth as auth_service
from app.services.email import create_reset_token, send_password_reset_email
from app.utils.security import (
    create_tokens,
    hash_password,
    verify_token
)

# Per-email cooldown tracking (email -> last request timestamp)
_reset_cooldowns: dict[str, float] = {}

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/signup-status")
async def get_signup_status(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Public endpoint: check if signup is allowed. No auth required."""
    from app.services import platform_settings
    allowed = await platform_settings.get(db, "allow_public_signup")
    return {"signup_allowed": allowed}


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    signup_data: SignupRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)]
) -> TokenResponse:
    """Create a new user account and return authentication tokens.

    Args:
        signup_data: User signup information (email, password, optional names)
        db: Database session
        settings: Application settings

    Returns:
        Access and refresh tokens for immediate login

    Raises:
        HTTPException: 409 if email already registered
    """
    # Check if public signup is allowed
    from app.services import platform_settings
    allow_signup = await platform_settings.get(db, "allow_public_signup")

    if not allow_signup:
        invite_token = getattr(signup_data, "invite_token", None)
        if not invite_token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Public registration is currently disabled. An invitation is required.",
            )
        # Validate invite token
        token_hash = hashlib.sha256(invite_token.encode()).hexdigest()
        from app.models.invitation import Invitation
        result = await db.execute(
            select(Invitation).where(
                Invitation.token_hash == token_hash,
                Invitation.status == "pending",
                Invitation.expires_at > datetime.now(timezone.utc),
            )
        )
        invitation = result.scalar_one_or_none()
        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or expired invitation token.",
            )
        # Mark invitation as accepted
        invitation.status = "accepted"
        invitation.accepted_at = datetime.now(timezone.utc)

    # Read default user class from platform settings
    default_class = await platform_settings.get(db, "default_user_class")

    # Create user (raises 409 if email exists)
    user = await auth_service.create_user(db, signup_data, default_class=default_class)

    # Auto-login: create tokens for new user
    tokens = create_tokens(str(user.id), settings)

    return TokenResponse(**tokens)


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)]
) -> TokenResponse:
    """Authenticate user and return access and refresh tokens.

    Args:
        login_data: User credentials (email and password)
        db: Database session
        settings: Application settings

    Returns:
        Access and refresh tokens

    Raises:
        HTTPException: 401 if credentials are invalid
    """
    # Authenticate user
    user = await auth_service.authenticate_user(
        db,
        login_data.email,
        login_data.password
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Track last login time
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    # Create tokens
    tokens = create_tokens(str(user.id), settings)

    return TokenResponse(**tokens)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    refresh_data: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)]
) -> TokenResponse:
    """Generate new access and refresh tokens from a valid refresh token.

    Args:
        refresh_data: Refresh token
        db: Database session
        settings: Application settings

    Returns:
        New access and refresh tokens

    Raises:
        HTTPException: 401 if refresh token is invalid or user not found/inactive
    """
    # Verify refresh token and extract user_id
    user_id_str = verify_token(refresh_data.refresh_token, "refresh", settings)

    # Convert to UUID
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Get user from database
    user = await auth_service.get_user_by_id(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Create new token pair
    tokens = create_tokens(str(user.id), settings)

    return TokenResponse(**tokens)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: CurrentUser
) -> UserResponse:
    """Get current authenticated user information.

    This endpoint validates the entire auth chain works end-to-end.

    Args:
        current_user: Authenticated user from JWT token

    Returns:
        User profile information
    """
    return UserResponse.model_validate(current_user)


@router.post("/forgot-password", response_model=MessageResponse, status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)]
) -> MessageResponse:
    """Request a password reset email.

    ALWAYS returns 202 regardless of whether the email exists, to prevent
    user enumeration attacks. Enforces 2-minute per-email cooldown.

    Args:
        request: Email address to send reset link to
        db: Database session
        settings: Application settings

    Returns:
        Generic success message (always same response)
    """
    now = time.time()

    # Clean up expired cooldown entries (older than 120 seconds)
    expired_keys = [k for k, v in _reset_cooldowns.items() if now - v >= 120]
    for k in expired_keys:
        del _reset_cooldowns[k]

    # Cooldown check: if same email requested within 2 minutes, return 202 silently
    last_request = _reset_cooldowns.get(request.email)
    if last_request is not None and now - last_request < 120:
        return MessageResponse(
            message="If the email exists, a reset link has been sent"
        )

    # Query user by email
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    user = result.scalar_one_or_none()

    # If user exists, create DB token and send reset email
    if user:
        # Invalidate all previous active tokens for this email
        await db.execute(
            update(PasswordResetToken)
            .where(
                PasswordResetToken.email == request.email,
                PasswordResetToken.is_active == True,  # noqa: E712
            )
            .values(is_active=False)
        )

        # Generate new token
        raw_token, token_hash = create_reset_token()

        # Store token in DB (10-minute expiry)
        db_token = PasswordResetToken(
            email=request.email,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        )
        db.add(db_token)
        await db.commit()

        # Build reset link
        reset_link = f"{settings.frontend_url}/reset-password?token={raw_token}"

        # Send email with first_name for personalized greeting
        await send_password_reset_email(user.email, user.first_name, reset_link, settings)

        # Record cooldown
        _reset_cooldowns[request.email] = time.time()

    # ALWAYS return same response (prevent email enumeration)
    return MessageResponse(
        message="If the email exists, a reset link has been sent"
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    """Reset user password using a valid DB-backed reset token.

    Validates token hash against database (single-use, not expired, active).

    Args:
        request: Reset token and new password
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: 400 if token is invalid, expired, or already used
    """
    # Hash incoming token for DB lookup
    token_hash = hashlib.sha256(request.token.encode()).hexdigest()

    # Look up token in DB: must be active, unused, and not expired
    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.is_active == True,  # noqa: E712
            PasswordResetToken.is_used == False,  # noqa: E712
            PasswordResetToken.expires_at > datetime.now(timezone.utc),
        )
    )
    token_record = result.scalar_one_or_none()

    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Look up user by token's email
    user_result = await db.execute(
        select(User).where(User.email == token_record.email)
    )
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Mark token as used (single-use)
    token_record.is_used = True

    # Update password
    user.hashed_password = hash_password(request.new_password)

    # Commit both changes
    await db.commit()

    return MessageResponse(message="Password reset successful")


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    profile_data: ProfileUpdateRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserResponse:
    """Update current user profile information.

    Args:
        profile_data: Profile update request (first_name and/or last_name)
        current_user: Authenticated user from JWT token
        db: Database session

    Returns:
        Updated user profile information

    Raises:
        HTTPException: 500 if user not found (should never happen for authenticated user)
    """
    try:
        updated_user = await auth_service.update_user_profile(
            db,
            current_user.id,
            profile_data.first_name,
            profile_data.last_name
        )
        return UserResponse.model_validate(updated_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/change-password", response_model=MessageResponse)
async def change_password_endpoint(
    password_data: ChangePasswordRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> MessageResponse:
    """Change current user password.

    Args:
        password_data: Password change request (current and new password)
        current_user: Authenticated user from JWT token
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: 401 if current password is incorrect
        HTTPException: 500 if user not found (should never happen for authenticated user)
    """
    try:
        success = await auth_service.change_password(
            db,
            current_user.id,
            password_data.current_password,
            password_data.new_password
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )

        return MessageResponse(message="Password changed successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/invite-validate", response_model=InviteValidateResponse)
async def invite_validate(
    token: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InviteValidateResponse:
    """Public endpoint: validate an invite token and return the associated email.

    Used to pre-fill the registration form with the invited email address.
    Read-only check -- does not modify the invitation.

    Args:
        token: Raw invite token from the URL
        db: Database session

    Returns:
        Email associated with the invitation

    Raises:
        HTTPException: 400 if token is invalid or expired
    """
    from app.models.invitation import Invitation

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    result = await db.execute(
        select(Invitation).where(
            Invitation.token_hash == token_hash,
            Invitation.status == "pending",
            Invitation.expires_at > datetime.now(timezone.utc),
        )
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invite has expired. Contact your administrator for a new one.",
        )

    return InviteValidateResponse(email=invitation.email, valid=True)


@router.post("/invite-register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def invite_register(
    body: InviteRegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    """Register a new user via invitation token and return auth tokens (auto-login).

    The email is taken from the invitation record (not user input) to prevent
    email enumeration. The invitation is marked as accepted (single-use).
    A FOR UPDATE lock prevents concurrent registration with the same token.

    Args:
        body: Invite registration data (token, display_name, password)
        db: Database session
        settings: Application settings

    Returns:
        Access and refresh tokens for immediate login

    Raises:
        HTTPException: 403 if token is invalid or expired
        HTTPException: 409 if email already registered
    """
    from app.models.invitation import Invitation
    from app.services import platform_settings

    # Hash token and look up invitation with pessimistic lock
    token_hash = hashlib.sha256(body.token.encode()).hexdigest()
    result = await db.execute(
        select(Invitation).where(
            Invitation.token_hash == token_hash,
            Invitation.status == "pending",
            Invitation.expires_at > datetime.now(timezone.utc),
        ).with_for_update()
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invite has expired. Contact your administrator for a new one.",
        )

    # Mark invitation as accepted (single-use)
    invitation.status = "accepted"
    invitation.accepted_at = datetime.now(timezone.utc)

    # Read default user class from platform settings
    default_class = await platform_settings.get(db, "default_user_class")

    # Build a SignupRequest-compatible object with email from invitation record
    signup_data = SignupRequest(
        email=invitation.email,
        password=body.password,
        first_name=body.display_name.strip(),
        last_name=None,
    )

    # Create user (raises 409 if email already exists)
    user = await auth_service.create_user(db, signup_data, default_class=default_class)

    # Auto-login: generate tokens
    tokens = create_tokens(str(user.id), settings)

    return TokenResponse(**tokens)
