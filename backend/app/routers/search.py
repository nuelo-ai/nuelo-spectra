"""Search configuration API endpoints."""

from datetime import date

from fastapi import APIRouter
from sqlalchemy import select

from app.config import get_settings
from app.dependencies import CurrentUser, DbSession
from app.models.search_quota import SearchQuota

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/search/config")
async def get_search_config(
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    """Get search configuration and quota status for the current user.

    Returns whether search is configured, enabled, and the user's
    current daily quota usage.

    Args:
        current_user: Authenticated user from JWT token.
        db: Database session.

    Returns:
        Search configuration and quota status:
        - configured: Whether Serper API key is set
        - enabled: Whether search feature is enabled (configured + within quota)
        - daily_quota: Maximum searches per day
        - used_today: Number of searches used today
        - quota_exceeded: Whether daily quota has been exceeded
    """
    settings = get_settings()
    configured = bool(settings.serper_api_key)

    # Query today's usage for the current user
    used_today = 0
    if configured:
        result = await db.execute(
            select(SearchQuota.search_count).where(
                SearchQuota.user_id == current_user.id,
                SearchQuota.search_date == date.today(),
            )
        )
        row = result.scalar_one_or_none()
        if row is not None:
            used_today = row

    daily_quota = settings.search_daily_quota
    quota_exceeded = used_today >= daily_quota

    return {
        "configured": configured,
        "enabled": configured and not quota_exceeded,
        "daily_quota": daily_quota,
        "used_today": used_today,
        "quota_exceeded": quota_exceeded,
    }
