"""Admin user management service.

Provides list, detail, activity queries, and account actions for admin user management.
"""

import math
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select, func, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import clear_user_deactivation, mark_user_deactivated
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.models.file import File
from app.models.password_reset import PasswordResetToken
from app.models.user import User
from app.models.user_credit import UserCredit
from app.services.email import create_reset_token, send_password_reset_email


async def list_users(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 20,
    search: str | None = None,
    is_active: bool | None = None,
    user_class: str | None = None,
    signup_after: datetime | None = None,
    signup_before: datetime | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> dict:
    """List users with search, filtering, sorting, and pagination.

    Args:
        db: Database session.
        page: Page number (1-based).
        per_page: Items per page.
        search: Partial match on email, first_name, or last_name.
        is_active: Filter by active status.
        user_class: Filter by user class.
        signup_after: Filter users created after this date.
        signup_before: Filter users created before this date.
        sort_by: Column to sort by.
        sort_order: 'asc' or 'desc'.

    Returns:
        Dict matching UserListResponse schema.
    """
    # Build base query with LEFT JOIN for credit balance
    credit_subq = (
        select(
            UserCredit.user_id,
            UserCredit.balance.label("credit_balance"),
        )
        .subquery()
    )

    query = (
        select(
            User,
            func.coalesce(credit_subq.c.credit_balance, 0).label("credit_balance"),
        )
        .outerjoin(credit_subq, User.id == credit_subq.c.user_id)
    )

    # Search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                User.email.ilike(search_pattern),
                User.first_name.ilike(search_pattern),
                User.last_name.ilike(search_pattern),
            )
        )

    # Status filter
    if is_active is not None:
        query = query.where(User.is_active == is_active)

    # User class filter
    if user_class is not None:
        query = query.where(User.user_class == user_class)

    # Signup date range filters
    if signup_after is not None:
        query = query.where(User.created_at >= signup_after)
    if signup_before is not None:
        query = query.where(User.created_at <= signup_before)

    # Count total (before pagination)
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Sorting
    sort_column_map = {
        "created_at": User.created_at,
        "last_login_at": User.last_login_at,
        "first_name": User.first_name,
        "credit_balance": credit_subq.c.credit_balance,
    }
    sort_col = sort_column_map.get(sort_by, User.created_at)
    if sort_order == "asc":
        query = query.order_by(sort_col.asc().nullslast())
    else:
        query = query.order_by(sort_col.desc().nullslast())

    # Pagination
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    rows = result.all()

    users = []
    for row in rows:
        user = row[0]
        balance = float(row[1]) if row[1] is not None else 0.0
        users.append(
            {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_active": user.is_active,
                "user_class": user.user_class,
                "created_at": user.created_at,
                "last_login_at": user.last_login_at,
                "credit_balance": balance,
            }
        )

    total_pages = max(1, math.ceil(total / per_page))

    return {
        "users": users,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


async def get_user_detail(db: AsyncSession, user_id: UUID) -> dict:
    """Get full user detail with aggregated counts.

    Args:
        db: Database session.
        user_id: UUID of the user.

    Returns:
        Dict matching UserDetailResponse schema.

    Raises:
        ValueError: If user not found.
    """
    # Fetch user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise ValueError("User not found")

    # Aggregate counts
    file_count_result = await db.execute(
        select(func.count(File.id)).where(File.user_id == user_id)
    )
    file_count = file_count_result.scalar_one()

    session_count_result = await db.execute(
        select(func.count(ChatSession.id)).where(ChatSession.user_id == user_id)
    )
    session_count = session_count_result.scalar_one()

    message_count_result = await db.execute(
        select(func.count(ChatMessage.id)).where(ChatMessage.user_id == user_id)
    )
    message_count = message_count_result.scalar_one()

    # Last message timestamp
    last_message_result = await db.execute(
        select(func.max(ChatMessage.created_at)).where(
            ChatMessage.user_id == user_id
        )
    )
    last_message_at = last_message_result.scalar_one_or_none()

    # Credit balance
    credit_result = await db.execute(
        select(UserCredit.balance).where(UserCredit.user_id == user_id)
    )
    credit_balance = credit_result.scalar_one_or_none()
    credit_balance = float(credit_balance) if credit_balance is not None else 0.0

    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
        "user_class": user.user_class,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "last_login_at": user.last_login_at,
        "credit_balance": credit_balance,
        "file_count": file_count,
        "session_count": session_count,
        "message_count": message_count,
        "last_message_at": last_message_at,
    }


async def get_user_activity(
    db: AsyncSession, user_id: UUID, months: int = 12
) -> dict:
    """Get monthly activity timeline for a user.

    Args:
        db: Database session.
        user_id: UUID of the user.
        months: Number of months to look back.

    Returns:
        Dict matching UserActivityResponse schema.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=months * 30)

    # Messages by month
    msg_result = await db.execute(
        select(
            func.date_trunc("month", ChatMessage.created_at).label("month"),
            func.count(ChatMessage.id).label("count"),
        )
        .where(ChatMessage.user_id == user_id, ChatMessage.created_at >= cutoff)
        .group_by(func.date_trunc("month", ChatMessage.created_at))
        .order_by(func.date_trunc("month", ChatMessage.created_at))
    )
    msg_rows = msg_result.all()

    # Sessions by month
    sess_result = await db.execute(
        select(
            func.date_trunc("month", ChatSession.created_at).label("month"),
            func.count(ChatSession.id).label("count"),
        )
        .where(ChatSession.user_id == user_id, ChatSession.created_at >= cutoff)
        .group_by(func.date_trunc("month", ChatSession.created_at))
        .order_by(func.date_trunc("month", ChatSession.created_at))
    )
    sess_rows = sess_result.all()

    # Merge into monthly activity
    activity_map: dict[str, dict] = {}
    for row in msg_rows:
        month_key = row.month.strftime("%Y-%m")
        activity_map.setdefault(month_key, {"message_count": 0, "session_count": 0})
        activity_map[month_key]["message_count"] = row.count

    for row in sess_rows:
        month_key = row.month.strftime("%Y-%m")
        activity_map.setdefault(month_key, {"message_count": 0, "session_count": 0})
        activity_map[month_key]["session_count"] = row.count

    # Sort by month and build list
    activity_months = [
        {"month": k, **v}
        for k, v in sorted(activity_map.items())
    ]

    return {
        "user_id": user_id,
        "months": activity_months,
    }


async def deactivate_user(db: AsyncSession, user_id: UUID) -> User:
    """Deactivate a user account and trigger immediate token invalidation.

    Args:
        db: Database session (caller manages transaction/commit).
        user_id: UUID of the user to deactivate.

    Returns:
        The deactivated User instance.

    Raises:
        ValueError: If user not found or already inactive.
    """
    result = await db.execute(
        select(User).where(User.id == user_id).with_for_update()
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise ValueError("User not found")
    if not user.is_active:
        raise ValueError("User is already deactivated")

    user.is_active = False
    await db.flush()

    # Immediate token invalidation via in-memory revocation set
    mark_user_deactivated(user_id)

    return user


async def activate_user(db: AsyncSession, user_id: UUID) -> User:
    """Activate a previously deactivated user account.

    Args:
        db: Database session (caller manages transaction/commit).
        user_id: UUID of the user to activate.

    Returns:
        The activated User instance.

    Raises:
        ValueError: If user not found or already active.
    """
    result = await db.execute(
        select(User).where(User.id == user_id).with_for_update()
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise ValueError("User not found")
    if user.is_active:
        raise ValueError("User is already active")

    user.is_active = True
    await db.flush()

    # Clear from revocation set so user can log in again
    clear_user_deactivation(user_id)

    return user


async def trigger_password_reset(
    db: AsyncSession, user_id: UUID, settings: Settings
) -> str:
    """Trigger a password reset email for a user (admin action).

    Reuses the same token generation and email flow as the user-facing
    forgot-password endpoint.

    Args:
        db: Database session (caller manages transaction/commit).
        user_id: UUID of the user.
        settings: Application settings (for frontend_url and SMTP config).

    Returns:
        The user's email address (for confirmation).

    Raises:
        ValueError: If user not found.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise ValueError("User not found")

    # Invalidate any existing active reset tokens for this email
    await db.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.email == user.email,
            PasswordResetToken.is_active == True,  # noqa: E712
        )
        .values(is_active=False)
    )

    # Generate new reset token
    raw_token, token_hash = create_reset_token()

    # Store token in DB (10-minute expiry)
    db_token = PasswordResetToken(
        email=user.email,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
    )
    db.add(db_token)
    await db.flush()

    # Build reset link and send email
    reset_link = f"{settings.frontend_url}/reset-password?token={raw_token}"
    await send_password_reset_email(user.email, user.first_name, reset_link, settings)

    return user.email
