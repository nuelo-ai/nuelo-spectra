"""Authentication service layer for business logic."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.auth import SignupRequest
from app.utils.security import hash_password, verify_password


async def create_user(db: AsyncSession, signup: SignupRequest) -> User:
    """Create a new user account.

    Args:
        db: Database session
        signup: Signup request data

    Returns:
        Created user instance

    Raises:
        HTTPException: If email already exists (409 Conflict)
    """
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == signup.email)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # Hash password and create user
    hashed_password = hash_password(signup.password)
    user = User(
        email=signup.email,
        hashed_password=hashed_password,
        first_name=signup.first_name,
        last_name=signup.last_name
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    """Authenticate a user with email and password.

    Args:
        db: Database session
        email: User email
        password: Plain text password

    Returns:
        User instance if authentication successful, None otherwise

    Note:
        Uses constant-time comparison to prevent timing attacks
    """
    # Query user by email
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()

    # Always hash a dummy password to prevent timing attacks that reveal email existence
    if not user:
        hash_password("dummy_password_for_constant_time")
        return None

    # Verify password (pwdlib uses constant-time comparison internally)
    if not verify_password(password, user.hashed_password):
        return None

    return user


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    """Get a user by their ID.

    Args:
        db: Database session
        user_id: User UUID

    Returns:
        User instance if found, None otherwise
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()
