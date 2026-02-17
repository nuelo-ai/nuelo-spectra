"""Admin invitation management service.

Provides create, list, revoke, and resend operations for user invitations
with token generation, expiry management, and cooldown enforcement.
"""

import time
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invitation import Invitation
from app.models.user import User
from app.services.email import create_reset_token
from app.services.platform_settings import get as get_setting


# Module-level resend cooldown tracking (same pattern as _reset_cooldowns in auth.py)
_resend_cooldowns: dict[str, float] = {}

_RESEND_COOLDOWN_SECONDS = 600  # 10 minutes


class DuplicateInviteError(Exception):
    """Raised when a pending invitation already exists for the email."""

    def __init__(self, email: str, invite_id: UUID):
        self.email = email
        self.invite_id = invite_id
        super().__init__(f"A pending invitation already exists for {email}")


async def create_invitation(
    db: AsyncSession,
    email: str,
    admin_id: UUID,
    settings: object,  # app.config.Settings
) -> dict:
    """Create a new invitation for the given email.

    Args:
        db: Database session (caller manages commit).
        email: Email address to invite.
        admin_id: UUID of the admin creating the invitation.
        settings: Application settings.

    Returns:
        Dict with 'invitation' (Invitation model) and 'raw_token' (str).

    Raises:
        ValueError: If email is already registered or max pending invites exceeded.
        DuplicateInviteError: If a pending invitation already exists for the email.
    """
    # Check if email already registered
    existing_user = await db.execute(
        select(User).where(func.lower(User.email) == email.lower())
    )
    if existing_user.scalar_one_or_none() is not None:
        raise ValueError("This email is already registered")

    # Check for existing pending invitation
    now = datetime.now(timezone.utc)
    existing_invite = await db.execute(
        select(Invitation).where(
            func.lower(Invitation.email) == email.lower(),
            Invitation.status == "pending",
            Invitation.expires_at > now,
        )
    )
    existing = existing_invite.scalar_one_or_none()
    if existing is not None:
        raise DuplicateInviteError(email, existing.id)

    # Check max_pending_invites platform setting
    max_pending = await get_setting(db, "max_pending_invites")
    if max_pending is not None:
        pending_count_result = await db.execute(
            select(func.count(Invitation.id)).where(
                Invitation.status == "pending",
                Invitation.expires_at > now,
            )
        )
        pending_count = pending_count_result.scalar_one()
        if pending_count >= max_pending:
            raise ValueError(
                f"Maximum pending invitations ({max_pending}) reached. "
                "Please revoke or wait for existing invitations to expire."
            )

    # Generate token
    raw_token, token_hash = create_reset_token()

    # Read invite_expiry_days from platform settings
    expiry_days = await get_setting(db, "invite_expiry_days")
    if expiry_days is None:
        expiry_days = 7

    # Create Invitation row
    invitation = Invitation(
        email=email.lower(),
        token_hash=token_hash,
        invited_by=admin_id,
        status="pending",
        expires_at=now + timedelta(days=expiry_days),
    )
    db.add(invitation)
    await db.flush()  # Get the ID without committing (caller commits after audit log)

    return {"invitation": invitation, "raw_token": raw_token}


async def list_invitations(
    db: AsyncSession,
    status_filter: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """List invitations with optional status filter and pagination.

    Args:
        db: Database session.
        status_filter: Optional filter: 'pending', 'accepted', or 'expired'.
        page: Page number (1-based).
        page_size: Items per page.

    Returns:
        Dict with 'items' (list of Invitation), 'total', 'page', 'page_size'.
    """
    now = datetime.now(timezone.utc)
    query = select(Invitation)

    if status_filter == "pending":
        # Truly pending: status=pending AND not yet expired
        query = query.where(
            Invitation.status == "pending",
            Invitation.expires_at > now,
        )
    elif status_filter == "expired":
        # Expired includes both explicitly expired AND silently expired pending
        from sqlalchemy import or_, and_

        query = query.where(
            or_(
                Invitation.status == "expired",
                and_(
                    Invitation.status == "pending",
                    Invitation.expires_at <= now,
                ),
            )
        )
    elif status_filter == "accepted":
        query = query.where(Invitation.status == "accepted")
    # No filter: return all

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Order and paginate
    query = query.order_by(Invitation.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


async def revoke_invitation(
    db: AsyncSession,
    invite_id: UUID,
) -> Invitation:
    """Revoke a pending invitation by setting status to expired.

    Args:
        db: Database session (caller manages commit).
        invite_id: UUID of the invitation to revoke.

    Returns:
        The updated Invitation.

    Raises:
        ValueError: If invitation not found, not pending, or already expired.
    """
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Invitation).where(Invitation.id == invite_id)
    )
    invitation = result.scalar_one_or_none()

    if invitation is None:
        raise ValueError("Invitation not found")

    if invitation.status != "pending":
        raise ValueError(f"Cannot revoke invitation with status '{invitation.status}'")

    if invitation.expires_at <= now:
        raise ValueError("Invitation has already expired")

    invitation.status = "expired"
    await db.flush()

    return invitation


async def resend_invitation(
    db: AsyncSession,
    invite_id: UUID,
    admin_id: UUID,
    settings: object,  # app.config.Settings
) -> dict:
    """Resend an invitation by invalidating the old one and creating a new one.

    Args:
        db: Database session (caller manages commit).
        invite_id: UUID of the original invitation.
        admin_id: UUID of the admin performing the resend.
        settings: Application settings.

    Returns:
        Dict with 'invitation' (new Invitation) and 'raw_token' (str).

    Raises:
        ValueError: If invitation not found, not pending, or cooldown not met.
    """
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Invitation).where(Invitation.id == invite_id)
    )
    invitation = result.scalar_one_or_none()

    if invitation is None:
        raise ValueError("Invitation not found")

    if invitation.status != "pending":
        raise ValueError(f"Cannot resend invitation with status '{invitation.status}'")

    # Check resend cooldown
    email_lower = invitation.email.lower()
    last_resend = _resend_cooldowns.get(email_lower)
    now_ts = time.time()
    if last_resend is not None and (now_ts - last_resend) < _RESEND_COOLDOWN_SECONDS:
        raise ValueError(
            "Please wait before resending. Minimum 10 minutes between resends."
        )

    # Invalidate old invitation
    invitation.status = "expired"

    # Generate new token
    raw_token, token_hash = create_reset_token()

    # Read invite_expiry_days from platform settings
    expiry_days = await get_setting(db, "invite_expiry_days")
    if expiry_days is None:
        expiry_days = 7

    # Create new invitation with fresh token and full expiry
    new_invitation = Invitation(
        email=email_lower,
        token_hash=token_hash,
        invited_by=admin_id,
        status="pending",
        expires_at=now + timedelta(days=expiry_days),
    )
    db.add(new_invitation)
    await db.flush()

    # Update cooldown tracker
    _resend_cooldowns[email_lower] = now_ts

    return {"invitation": new_invitation, "raw_token": raw_token}
