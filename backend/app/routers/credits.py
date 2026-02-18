"""Public credit endpoints for authenticated users."""

from fastapi import APIRouter

from app.dependencies import CurrentUser, DbSession
from app.schemas.credit import CreditBalanceResponse
from app.services.credit import CreditService

router = APIRouter(prefix="/api/credits", tags=["credits"])


@router.get("/balance", response_model=CreditBalanceResponse)
async def get_my_credit_balance(
    db: DbSession,
    current_user: CurrentUser,
) -> CreditBalanceResponse:
    """Get the authenticated user's own credit balance.

    This is the endpoint the frontend sidebar will call (Phase 31).
    """
    return await CreditService.get_balance(
        db, current_user.id, current_user.user_class
    )
