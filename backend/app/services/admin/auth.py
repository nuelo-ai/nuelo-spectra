"""Admin authentication service layer."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.auth import authenticate_user
from app.utils.security import hash_password


async def authenticate_admin(db: AsyncSession, email: str, password: str) -> User | None:
    """Authenticate user and verify is_admin flag in database.

    Delegates credential verification to the existing authenticate_user service,
    then checks the is_admin flag as a second gate.

    Args:
        db: Database session
        email: Admin email
        password: Plain text password

    Returns:
        User instance if admin authentication successful, None otherwise
    """
    user = await authenticate_user(db, email, password)
    if user is None:
        return None
    if not user.is_admin:
        return None  # Valid credentials but not admin
    return user


async def seed_admin(db: AsyncSession, email: str, password: str) -> User:
    """Create or update the seeded admin user. Idempotent.

    If a user with the given email exists, resets their password and
    ensures is_admin=True. If not, creates a new admin user.

    Args:
        db: Database session
        email: Admin email
        password: Plain text password

    Returns:
        The created or updated admin user
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        user.hashed_password = hash_password(password)
        user.is_admin = True
    else:
        user = User(
            email=email,
            hashed_password=hash_password(password),
            is_admin=True,
            user_class="free",
        )
        db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
