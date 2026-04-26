"""Authentication service layer for business logic."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.user_credit import UserCredit
from app.schemas.auth import SignupRequest
from app.services.user_class import get_class_config, get_default_class
from app.utils.security import hash_password, verify_password


async def create_user(
    db: AsyncSession, signup: SignupRequest, default_class: str | None = None
) -> User:
    """Create a new user account.

    Args:
        db: Database session
        signup: Signup request data
        default_class: Override default user class (from platform_settings).
            Falls back to get_default_class() if None.

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

    # Use provided default_class or fall back to yaml-based default
    if default_class is None:
        default_class = get_default_class()

    user = User(
        email=signup.email,
        hashed_password=hashed_password,
        first_name=signup.first_name,
        last_name=signup.last_name,
        user_class=default_class,
    )

    # Set trial expiration for free_trial users
    if default_class == "free_trial":
        class_cfg = get_class_config(default_class)
        trial_days = class_cfg.get("trial_duration_days", 7) if class_cfg else 7
        user.trial_expires_at = datetime.now(timezone.utc) + timedelta(days=trial_days)

    db.add(user)
    await db.flush()  # Flush to get user.id for UserCredit FK

    # Create UserCredit row with initial balance from tier config
    class_config = get_class_config(default_class)
    if class_config and class_config.get("reset_policy") == "unlimited":
        initial_balance = Decimal("-1")  # Sentinel for unlimited users
    elif class_config:
        initial_balance = Decimal(str(class_config.get("credits", 0)))
    else:
        initial_balance = Decimal("0")

    credit = UserCredit(user_id=user.id, balance=initial_balance, purchased_balance=Decimal("0"))
    db.add(credit)

    # TODO: Existing users have balance=0 from migration backfill. Consider a
    # one-time script or migration to set balance to tier allocation.

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


async def update_user_profile(
    db: AsyncSession,
    user_id: UUID,
    first_name: str | None,
    last_name: str | None
) -> User:
    """Update user profile fields.

    Args:
        db: Database session
        user_id: User UUID
        first_name: New first name (if provided)
        last_name: New last name (if provided)

    Returns:
        Updated user instance

    Raises:
        ValueError: If user not found
    """
    # Query user by id
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise ValueError(f"User {user_id} not found")

    # Update only provided fields
    if first_name is not None:
        user.first_name = first_name
    if last_name is not None:
        user.last_name = last_name

    # Commit and refresh
    await db.commit()
    await db.refresh(user)

    return user


async def change_password(
    db: AsyncSession,
    user_id: UUID,
    current_password: str,
    new_password: str
) -> bool:
    """Change user password after verifying current password.

    Args:
        db: Database session
        user_id: User UUID
        current_password: Current password for verification
        new_password: New password to set

    Returns:
        True if password changed successfully, False if current password invalid

    Raises:
        ValueError: If user not found
    """
    # Query user by id
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise ValueError(f"User {user_id} not found")

    # Verify current password
    if not verify_password(current_password, user.hashed_password):
        return False

    # Hash and update new password
    user.hashed_password = hash_password(new_password)

    # Commit
    await db.commit()

    return True
