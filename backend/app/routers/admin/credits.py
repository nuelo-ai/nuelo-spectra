"""Admin credit management endpoints.

Provides endpoints for viewing user credit balances, transaction history,
adjusting credits (with password re-entry), manual resets, and aggregation
queries (distribution by class, low-balance users).
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request

from app.dependencies import CurrentAdmin, DbSession
from app.models.user import User
from app.schemas.credit import (
    CreditAdjustmentRequest,
    CreditBalanceResponse,
    CreditManualResetRequest,
    CreditTransactionResponse,
)
from app.services.admin.audit import log_admin_action
from app.services.credit import CreditService
from app.utils.security import verify_password

router = APIRouter(prefix="/credits", tags=["admin-credits"])


@router.get("/users/{user_id}", response_model=CreditBalanceResponse)
async def get_user_credit_balance(
    user_id: UUID,
    db: DbSession,
    current_admin: CurrentAdmin,
) -> CreditBalanceResponse:
    """View a user's credit balance (CREDIT-06)."""
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return await CreditService.get_balance(db, user_id, user.user_class)


@router.get(
    "/users/{user_id}/transactions",
    response_model=list[CreditTransactionResponse],
)
async def get_user_transaction_history(
    user_id: UUID,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[CreditTransactionResponse]:
    """View a user's credit transaction history (CREDIT-08)."""
    transactions = await CreditService.get_transaction_history(
        db, user_id, limit, offset
    )

    # Audit log
    client_ip = request.client.host if request.client else None
    await log_admin_action(
        db=db,
        admin_id=current_admin.id,
        action="view_credit_history",
        target_type="user_credit",
        target_id=str(user_id),
        ip_address=client_ip,
    )
    await db.commit()

    return transactions


@router.post("/users/{user_id}/adjust", response_model=CreditBalanceResponse)
async def adjust_user_credits(
    user_id: UUID,
    body: CreditAdjustmentRequest,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
) -> CreditBalanceResponse:
    """Adjust a user's credits with password re-entry (CREDIT-07).

    Admin must re-enter their password to confirm the adjustment.
    """
    # Verify admin password (per locked decision: password re-entry required)
    if not verify_password(body.password, current_admin.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid password")

    result = await CreditService.admin_adjust(
        db, user_id, body.amount, body.reason, current_admin.id
    )

    # Audit log
    client_ip = request.client.host if request.client else None
    await log_admin_action(
        db=db,
        admin_id=current_admin.id,
        action="credit_adjustment",
        target_type="user_credit",
        target_id=str(user_id),
        details={
            "amount": float(body.amount),
            "reason": body.reason,
            "balance_after": float(result.balance),
        },
        ip_address=client_ip,
    )
    await db.commit()

    return result


@router.post("/users/{user_id}/reset", response_model=CreditBalanceResponse)
async def manual_reset_user_credits(
    user_id: UUID,
    body: CreditManualResetRequest,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
) -> CreditBalanceResponse:
    """Manually reset a user's credits with password re-entry (CREDIT-12, CREDIT-13).

    Restarts the user's credit cycle from today.
    """
    # Verify admin password
    if not verify_password(body.password, current_admin.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid password")

    result = await CreditService.manual_reset(db, user_id, current_admin.id)

    # Audit log
    client_ip = request.client.host if request.client else None
    await log_admin_action(
        db=db,
        admin_id=current_admin.id,
        action="credit_manual_reset",
        target_type="user_credit",
        target_id=str(user_id),
        ip_address=client_ip,
    )
    await db.commit()

    return result


@router.get("/distribution")
async def get_credit_distribution(
    db: DbSession,
    current_admin: CurrentAdmin,
) -> list[dict]:
    """Get credit distribution by user class (CREDIT-09 backend)."""
    return await CreditService.get_credit_distribution(db)


@router.get("/low-balance")
async def get_low_balance_users(
    db: DbSession,
    current_admin: CurrentAdmin,
    threshold_pct: float = Query(default=0.1, ge=0.0, le=1.0),
) -> list[dict]:
    """Get users with low credit balance (CREDIT-10 backend)."""
    return await CreditService.get_low_credit_users(db, threshold_pct)
