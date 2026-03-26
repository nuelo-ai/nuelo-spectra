"""Admin discount code CRUD endpoints.

Provides endpoints for listing, creating, updating, deactivating,
and deleting discount codes with Stripe Coupon/Promotion Code sync.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from app.dependencies import CurrentAdmin, DbSession
from app.schemas.discount_code import (
    CreateDiscountCodeRequest,
    DiscountCodeListResponse,
    DiscountCodeResponse,
    UpdateDiscountCodeRequest,
)
from app.services.admin.audit import log_admin_action
from app.services.discount_code import DiscountCodeService

router = APIRouter(prefix="/discount-codes", tags=["admin-discount-codes"])


@router.get("", response_model=DiscountCodeListResponse)
async def list_discount_codes(
    db: DbSession,
    current_admin: CurrentAdmin,
) -> DiscountCodeListResponse:
    """List all discount codes ordered by created_at desc."""
    codes, total = await DiscountCodeService.list_all(db)
    return DiscountCodeListResponse(
        items=[
            DiscountCodeResponse(
                id=str(code.id),
                code=code.code,
                discount_type=code.discount_type,
                discount_value=code.discount_value,
                currency=code.currency,
                stripe_coupon_id=code.stripe_coupon_id,
                stripe_promotion_code_id=code.stripe_promotion_code_id,
                max_redemptions=code.max_redemptions,
                times_redeemed=code.times_redeemed,
                expires_at=code.expires_at,
                is_active=code.is_active,
                created_at=code.created_at,
                updated_at=code.updated_at,
            )
            for code in codes
        ],
        total=total,
    )


@router.post("", response_model=DiscountCodeResponse, status_code=201)
async def create_discount_code(
    body: CreateDiscountCodeRequest,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
) -> DiscountCodeResponse:
    """Create a discount code with Stripe Coupon + Promotion Code sync."""
    try:
        code = await DiscountCodeService.create(
            db,
            code=body.code,
            discount_type=body.discount_type,
            discount_value=body.discount_value,
            max_redemptions=body.max_redemptions,
            expires_at=body.expires_at,
            admin_id=current_admin.id,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    client_ip = request.client.host if request.client else None
    await log_admin_action(
        db,
        admin_id=current_admin.id,
        action="create_discount_code",
        target_type="discount_code",
        target_id=str(code.id),
        details={"code": code.code, "discount_type": code.discount_type},
        ip_address=client_ip,
    )
    await db.commit()

    return DiscountCodeResponse(
        id=str(code.id),
        code=code.code,
        discount_type=code.discount_type,
        discount_value=code.discount_value,
        currency=code.currency,
        stripe_coupon_id=code.stripe_coupon_id,
        stripe_promotion_code_id=code.stripe_promotion_code_id,
        max_redemptions=code.max_redemptions,
        times_redeemed=code.times_redeemed,
        expires_at=code.expires_at,
        is_active=code.is_active,
        created_at=code.created_at,
        updated_at=code.updated_at,
    )


@router.put("/{code_id}", response_model=DiscountCodeResponse)
async def update_discount_code(
    code_id: UUID,
    body: UpdateDiscountCodeRequest,
    db: DbSession,
    current_admin: CurrentAdmin,
) -> DiscountCodeResponse:
    """Update a discount code's max_redemptions and/or expires_at."""
    try:
        code = await DiscountCodeService.update(
            db,
            discount_code_id=code_id,
            max_redemptions=body.max_redemptions,
            expires_at=body.expires_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    await db.commit()

    return DiscountCodeResponse(
        id=str(code.id),
        code=code.code,
        discount_type=code.discount_type,
        discount_value=code.discount_value,
        currency=code.currency,
        stripe_coupon_id=code.stripe_coupon_id,
        stripe_promotion_code_id=code.stripe_promotion_code_id,
        max_redemptions=code.max_redemptions,
        times_redeemed=code.times_redeemed,
        expires_at=code.expires_at,
        is_active=code.is_active,
        created_at=code.created_at,
        updated_at=code.updated_at,
    )


@router.post("/{code_id}/deactivate", response_model=DiscountCodeResponse)
async def deactivate_discount_code(
    code_id: UUID,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
) -> DiscountCodeResponse:
    """Deactivate a discount code locally and in Stripe."""
    try:
        code = await DiscountCodeService.deactivate(db, discount_code_id=code_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    client_ip = request.client.host if request.client else None
    await log_admin_action(
        db,
        admin_id=current_admin.id,
        action="deactivate_discount_code",
        target_type="discount_code",
        target_id=str(code.id),
        details={"code": code.code},
        ip_address=client_ip,
    )
    await db.commit()

    return DiscountCodeResponse(
        id=str(code.id),
        code=code.code,
        discount_type=code.discount_type,
        discount_value=code.discount_value,
        currency=code.currency,
        stripe_coupon_id=code.stripe_coupon_id,
        stripe_promotion_code_id=code.stripe_promotion_code_id,
        max_redemptions=code.max_redemptions,
        times_redeemed=code.times_redeemed,
        expires_at=code.expires_at,
        is_active=code.is_active,
        created_at=code.created_at,
        updated_at=code.updated_at,
    )


@router.delete("/{code_id}", status_code=204)
async def delete_discount_code(
    code_id: UUID,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
) -> None:
    """Delete a discount code from DB and Stripe."""
    try:
        await DiscountCodeService.delete(db, discount_code_id=code_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    client_ip = request.client.host if request.client else None
    await log_admin_action(
        db,
        admin_id=current_admin.id,
        action="delete_discount_code",
        target_type="discount_code",
        target_id=str(code_id),
        ip_address=client_ip,
    )
    await db.commit()
