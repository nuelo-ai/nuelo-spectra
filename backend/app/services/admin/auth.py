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


async def seed_admin(
    db: AsyncSession,
    email: str,
    password: str,
    first_name: str = "Admin",
    last_name: str = "User",
) -> User:
    """Create or update the seeded admin user. Idempotent.

    If a user with the given email exists, resets their password and
    ensures is_admin=True with names populated. If not, creates a new admin user.

    Args:
        db: Database session
        email: Admin email
        password: Plain text password
        first_name: Admin first name
        last_name: Admin last name

    Returns:
        The created or updated admin user
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        user.hashed_password = hash_password(password)
        user.is_admin = True
        if not user.first_name:
            user.first_name = first_name
        if not user.last_name:
            user.last_name = last_name
    else:
        user = User(
            email=email,
            hashed_password=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            is_admin=True,
            user_class="free",
        )
        db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
