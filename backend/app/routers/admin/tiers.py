"""Admin tier endpoints — read-only tier summary."""

from fastapi import APIRouter
from sqlalchemy import func, select

from app.dependencies import CurrentAdmin, DbSession
from app.models.user import User
from app.schemas.platform_settings import TierSummaryResponse
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
