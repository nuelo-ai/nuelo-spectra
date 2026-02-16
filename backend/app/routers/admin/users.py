"""Admin user management endpoints.

Provides endpoints for listing, searching, filtering users,
viewing user detail, and user activity timeline.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.dependencies import CurrentAdmin, DbSession
from app.schemas.admin_users import (
    UserActivityResponse,
    UserDetailResponse,
    UserListResponse,
)
from app.services.admin.users import get_user_activity, get_user_detail, list_users

router = APIRouter(prefix="/users", tags=["admin-users"])


@router.get("", response_model=UserListResponse)
async def list_users_endpoint(
    db: DbSession,
    current_admin: CurrentAdmin,
    page: int = Query(default=1, ge=1),
    search: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    user_class: str | None = Query(default=None),
    signup_after: datetime | None = Query(default=None),
    signup_before: datetime | None = Query(default=None),
    sort_by: str = Query(
        default="created_at",
        pattern="^(created_at|last_login_at|first_name|credit_balance)$",
    ),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
) -> UserListResponse:
    """List users with search, filtering, sorting, and pagination (USER-01, USER-02, USER-03).

    Fixed page size of 20 per locked decision.
    """
    result = await list_users(
        db,
        page=page,
        per_page=20,
        search=search,
        is_active=is_active,
        user_class=user_class,
        signup_after=signup_after,
        signup_before=signup_before,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return UserListResponse(**result)


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user_detail_endpoint(
    user_id: UUID,
    db: DbSession,
    current_admin: CurrentAdmin,
) -> UserDetailResponse:
    """Get full user detail with profile, status, tier, credits, and usage counts (USER-04 to USER-08)."""
    try:
        result = await get_user_detail(db, user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found")
    return UserDetailResponse(**result)


@router.get("/{user_id}/activity", response_model=UserActivityResponse)
async def get_user_activity_endpoint(
    user_id: UUID,
    db: DbSession,
    current_admin: CurrentAdmin,
    months: int = Query(default=12, ge=1, le=24),
) -> UserActivityResponse:
    """Get monthly activity timeline for a user (USER-07, USER-08)."""
    result = await get_user_activity(db, user_id, months)
    return UserActivityResponse(**result)
