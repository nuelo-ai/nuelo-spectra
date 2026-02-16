"""Admin tier endpoints.

Provides tier summary with live user counts, and tier change for individual users.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import func, select

from app.dependencies import CurrentAdmin, DbSession
from app.models.user import User
from app.schemas.platform_settings import TierChangeRequest, TierSummaryResponse
from app.services.admin.audit import log_admin_action
from app.services.admin.tiers import change_user_tier
from app.services.user_class import get_user_classes

router = APIRouter(prefix="/tiers", tags=["admin-tiers"])


@router.get("", response_model=list[TierSummaryResponse])
async def get_tiers(
    db: DbSession,
    current_admin: CurrentAdmin,
) -> list[TierSummaryResponse]:
    """Return all tiers with user counts (TIER-05, TIER-07).

    Tier definitions come from user_classes.yaml.
    User counts are queried live from the database.
    """
    # Get user counts per class from DB
    result = await db.execute(
        select(User.user_class, func.count(User.id).label("user_count"))
        .where(User.is_active == True)  # noqa: E712
        .group_by(User.user_class)
    )
    counts = {row.user_class: row.user_count for row in result.all()}

    # Get tier definitions from yaml
    classes = get_user_classes()

    # Build response
    tiers = []
    for class_name, config in classes.items():
        tiers.append(
            TierSummaryResponse(
                name=class_name,
                display_name=config.get("display_name", class_name),
                credits=config.get("credits", 0),
                reset_policy=config.get("reset_policy", "none"),
                user_count=counts.get(class_name, 0),
            )
        )

    return tiers


@router.put("/users/{user_id}")
async def change_tier(
    user_id: UUID,
    body: TierChangeRequest,
    current_admin: CurrentAdmin,
    db: DbSession,
    request: Request,
) -> dict:
    """Change a user's tier and atomically reset their credit balance (TIER-04).

    Args:
        user_id: UUID of the user to change.
        body: TierChangeRequest with new user_class.
        current_admin: Authenticated admin user.
        db: Database session.
        request: FastAPI request for client IP.

    Returns:
        Dict with old_class, new_class, and new_balance.

    Raises:
        HTTPException: 400 if user class is unknown or user not found.
    """
    try:
        result = await change_user_tier(db, user_id, body.user_class, current_admin.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Audit log
    client_ip = request.client.host if request.client else None
    await log_admin_action(
        db,
        admin_id=current_admin.id,
        action="change_user_tier",
        target_type="user",
        target_id=str(user_id),
        details={
            "old_class": result["old_class"],
            "new_class": result["new_class"],
        },
        ip_address=client_ip,
    )

    await db.commit()
    return result
