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
    BulkActionResult,
    BulkCreditAdjustRequest,
    BulkDeleteRequest,
    BulkTierChangeRequest,
    BulkUserActionRequest,
    DeleteChallengeResponse,
    DeleteConfirmRequest,
    PasswordResetTriggerResponse,
    UserActivityResponse,
    UserDetailResponse,
    UserListResponse,
)
from app.schemas.platform_settings import TierChangeRequest
from app.services.admin.audit import log_admin_action
from app.services.admin.tiers import change_user_tier
from app.services.admin.users import (
    activate_user,
    bulk_activate,
    bulk_adjust_credits,
    bulk_change_tier,
    bulk_deactivate,
    bulk_delete,
    deactivate_user,
    delete_user,
    generate_challenge_code,
    get_user_activity,
    get_user_detail,
    list_users,
    trigger_password_reset,
    verify_challenge_code,
)
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


# ---------------------------------------------------------------------------
# Bulk operations (MUST be registered before /{user_id} to avoid path conflicts)
# ---------------------------------------------------------------------------


@router.post("/bulk/activate", response_model=BulkActionResult)
async def bulk_activate_endpoint(
    body: BulkUserActionRequest,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
) -> BulkActionResult:
    """Bulk activate multiple users (up to 100)."""
    result = await bulk_activate(db, body.user_ids)

    client_ip = request.client.host if request.client else None
    await log_admin_action(
        db,
        admin_id=current_admin.id,
        action="bulk_activate",
        target_type="users",
        details={
            "user_ids": [str(uid) for uid in body.user_ids],
            "result": result,
        },
        ip_address=client_ip,
    )
    await db.commit()

    return BulkActionResult(**result)


@router.post("/bulk/deactivate", response_model=BulkActionResult)
async def bulk_deactivate_endpoint(
    body: BulkUserActionRequest,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
) -> BulkActionResult:
    """Bulk deactivate multiple users with immediate token invalidation (up to 100)."""
    result = await bulk_deactivate(db, body.user_ids)

    client_ip = request.client.host if request.client else None
    await log_admin_action(
        db,
        admin_id=current_admin.id,
        action="bulk_deactivate",
        target_type="users",
        details={
            "user_ids": [str(uid) for uid in body.user_ids],
            "result": result,
        },
        ip_address=client_ip,
    )
    await db.commit()

    return BulkActionResult(**result)


@router.post("/bulk/tier-change", response_model=BulkActionResult)
async def bulk_tier_change_endpoint(
    body: BulkTierChangeRequest,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
) -> BulkActionResult:
    """Bulk change tier for multiple users with credit reset (up to 100)."""
    result = await bulk_change_tier(
        db, body.user_ids, body.user_class, current_admin.id
    )

    client_ip = request.client.host if request.client else None
    await log_admin_action(
        db,
        admin_id=current_admin.id,
        action="bulk_tier_change",
        target_type="users",
        details={
            "user_ids": [str(uid) for uid in body.user_ids],
            "new_class": body.user_class,
            "result": result,
        },
        ip_address=client_ip,
    )
    await db.commit()

    return BulkActionResult(**result)


@router.post("/bulk/credit-adjust", response_model=BulkActionResult)
async def bulk_credit_adjust_endpoint(
    body: BulkCreditAdjustRequest,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
) -> BulkActionResult:
    """Bulk credit adjustment -- set exact amount OR add/deduct delta (up to 100 users)."""
    result = await bulk_adjust_credits(
        db, body.user_ids, body.amount, body.delta, body.reason, current_admin.id
    )

    client_ip = request.client.host if request.client else None
    await log_admin_action(
        db,
        admin_id=current_admin.id,
        action="bulk_credit_adjust",
        target_type="users",
        details={
            "user_ids": [str(uid) for uid in body.user_ids],
            "amount": str(body.amount) if body.amount is not None else None,
            "delta": str(body.delta) if body.delta is not None else None,
            "reason": body.reason,
            "result": result,
        },
        ip_address=client_ip,
    )
    await db.commit()

    return BulkActionResult(**result)


@router.post("/bulk/delete-challenge", response_model=DeleteChallengeResponse)
async def bulk_delete_challenge_endpoint(
    body: BulkUserActionRequest,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
) -> DeleteChallengeResponse:
    """Generate a challenge code for bulk delete confirmation."""
    code = generate_challenge_code(
        current_admin.id, f"bulk_delete_{len(body.user_ids)}"
    )
    return DeleteChallengeResponse(challenge_code=code, expires_in=300)


@router.post("/bulk/delete", response_model=BulkActionResult)
async def bulk_delete_endpoint(
    body: BulkDeleteRequest,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
) -> BulkActionResult:
    """Bulk hard delete users with challenge code confirmation (up to 100)."""
    if not verify_challenge_code(
        current_admin.id,
        f"bulk_delete_{len(body.user_ids)}",
        body.challenge_code,
    ):
        raise HTTPException(
            status_code=400, detail="Invalid or expired challenge code"
        )

    result = await bulk_delete(db, body.user_ids, current_admin.id)
    await db.commit()

    return BulkActionResult(**result)


# ---------------------------------------------------------------------------
# Individual user endpoints
# ---------------------------------------------------------------------------


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


@router.post("/{user_id}/delete-challenge", response_model=DeleteChallengeResponse)
async def delete_challenge_endpoint(
    user_id: UUID,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
) -> DeleteChallengeResponse:
    """Generate a 6-char challenge code for delete confirmation (USER-13)."""
    code = generate_challenge_code(
        current_admin.id, f"delete_user_{user_id}"
    )
    return DeleteChallengeResponse(challenge_code=code, expires_in=300)


@router.delete("/{user_id}")
async def delete_user_endpoint(
    user_id: UUID,
    body: DeleteConfirmRequest,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
) -> dict:
    """Hard delete a user with challenge code confirmation (USER-13).

    The admin must first call POST /{user_id}/delete-challenge to get a code,
    then submit that code here. Deletes all user data, anonymizes audit logs,
    and removes physical files from disk.
    """
    if not verify_challenge_code(
        current_admin.id, f"delete_user_{user_id}", body.challenge_code
    ):
        raise HTTPException(
            status_code=400, detail="Invalid or expired challenge code"
        )

    try:
        anon_label = await delete_user(db, user_id, current_admin.id)
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg)
        raise HTTPException(status_code=400, detail=error_msg)

    await db.commit()

    return {"message": "User deleted", "anonymized_as": anon_label}


