"""Admin user management endpoints.

Provides endpoints for listing, searching, filtering users,
viewing user detail, user activity timeline, and account actions
(activate, deactivate, password reset, tier change, credit adjustment).
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.config import Settings, get_settings
from app.dependencies import CurrentAdmin, DbSession
from app.schemas.admin_users import (
    ActivateDeactivateResponse,
    CreditAdjustRequest,
    PasswordResetTriggerResponse,
    UserActivityResponse,
    UserDetailResponse,
    UserListResponse,
)
from app.schemas.credit import CreditBalanceResponse
from app.schemas.platform_settings import TierChangeRequest
from app.services.admin.audit import log_admin_action
from app.services.admin.tiers import change_user_tier
from app.services.admin.users import (
    activate_user,
    deactivate_user,
    get_user_activity,
    get_user_detail,
    list_users,
    trigger_password_reset,
)
from app.services.credit import CreditService

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


@router.post("/{user_id}/deactivate", response_model=ActivateDeactivateResponse)
async def deactivate_user_endpoint(
    user_id: UUID,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
) -> ActivateDeactivateResponse:
    """Deactivate a user account with immediate token invalidation (USER-09).

    The user is immediately logged out -- any subsequent API call with their
    existing JWT will return 401, even before the token expires.
    """
    try:
        await deactivate_user(db, user_id)
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg)
        raise HTTPException(status_code=400, detail=error_msg)

    client_ip = request.client.host if request.client else None
    await log_admin_action(
        db,
        admin_id=current_admin.id,
        action="deactivate_user",
        target_type="user",
        target_id=str(user_id),
        ip_address=client_ip,
    )
    await db.commit()

    return ActivateDeactivateResponse(
        user_id=user_id,
        is_active=False,
        message="User deactivated and logged out",
    )


@router.post("/{user_id}/activate", response_model=ActivateDeactivateResponse)
async def activate_user_endpoint(
    user_id: UUID,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
) -> ActivateDeactivateResponse:
    """Activate a previously deactivated user account (USER-09)."""
    try:
        await activate_user(db, user_id)
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg)
        raise HTTPException(status_code=400, detail=error_msg)

    client_ip = request.client.host if request.client else None
    await log_admin_action(
        db,
        admin_id=current_admin.id,
        action="activate_user",
        target_type="user",
        target_id=str(user_id),
        ip_address=client_ip,
    )
    await db.commit()

    return ActivateDeactivateResponse(
        user_id=user_id,
        is_active=True,
        message="User activated",
    )


@router.post("/{user_id}/password-reset", response_model=PasswordResetTriggerResponse)
async def trigger_password_reset_endpoint(
    user_id: UUID,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
    settings: Settings = Depends(get_settings),
) -> PasswordResetTriggerResponse:
    """Trigger a password reset email for a user (USER-10).

    Admin does NOT set the password directly. A reset email is sent
    to the user with a secure token link.
    """
    try:
        email = await trigger_password_reset(db, user_id, settings)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    client_ip = request.client.host if request.client else None
    await log_admin_action(
        db,
        admin_id=current_admin.id,
        action="trigger_password_reset",
        target_type="user",
        target_id=str(user_id),
        ip_address=client_ip,
    )
    await db.commit()

    return PasswordResetTriggerResponse(
        user_id=user_id,
        email=email,
        message="Password reset email sent",
    )


@router.put("/{user_id}/tier")
async def change_user_tier_endpoint(
    user_id: UUID,
    body: TierChangeRequest,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
) -> dict:
    """Change a user's tier, resetting credit balance to new tier's allocation (USER-11).

    Per locked decision: tier change always resets credit balance.
    """
    try:
        result = await change_user_tier(db, user_id, body.user_class, current_admin.id)
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        raise HTTPException(status_code=400, detail=error_msg)

    client_ip = request.client.host if request.client else None
    await log_admin_action(
        db,
        admin_id=current_admin.id,
        action="change_user_tier",
        target_type="user",
        target_id=str(user_id),
        details={"old_class": result["old_class"], "new_class": result["new_class"]},
        ip_address=client_ip,
    )
    await db.commit()

    return result


@router.post("/{user_id}/credits/adjust", response_model=CreditBalanceResponse)
async def adjust_credits_endpoint(
    user_id: UUID,
    body: CreditAdjustRequest,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
) -> CreditBalanceResponse:
    """Adjust a user's credit balance with a reason note (USER-12)."""
    try:
        result = await CreditService.admin_adjust(
            db, user_id, body.amount, body.reason, current_admin.id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    client_ip = request.client.host if request.client else None
    await log_admin_action(
        db,
        admin_id=current_admin.id,
        action="credit_adjustment",
        target_type="user",
        target_id=str(user_id),
        details={"amount": str(body.amount), "reason": body.reason},
        ip_address=client_ip,
    )
    await db.commit()

    return result
