"""Authentication API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.database import get_db
from app.dependencies import CurrentUser
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    SignupRequest,
    TokenResponse
)
from app.schemas.user import UserResponse
from app.services import auth as auth_service
from app.utils.security import create_tokens, verify_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


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
    # Create user (raises 409 if email exists)
    user = await auth_service.create_user(db, signup_data)

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
