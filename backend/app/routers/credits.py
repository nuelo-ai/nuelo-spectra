"""Public credit endpoints for authenticated users."""

import logging

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.config import get_settings
from app.dependencies import CurrentUser, DbSession
from app.exceptions.stripe import CheckoutValidationError, StripeConfigError
from app.models.credit_package import CreditPackage
from app.models.user import User
from app.schemas.credit import CreditBalanceResponse
from app.schemas.subscription import CheckoutResponse, CreditPackageResponse, TopupCheckoutRequest
from app.services.credit import CreditService
from app.services.subscription import SubscriptionService

logger = logging.getLogger(__name__)


def check_topup_eligible(user: User) -> None:
    """Raise 403 if user is on free_trial tier (cannot purchase top-ups)."""
    if user.user_class == "free_trial":
        raise HTTPException(
            status_code=403,
            detail={
                "detail": "Credit top-ups not available during free trial",
                "code": "trial_topup_blocked",
            },
        )

router = APIRouter(prefix="/credits", tags=["credits"])


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


@router.post("/purchase", response_model=CheckoutResponse)
async def purchase_credits(
    body: TopupCheckoutRequest,
    db: DbSession,
    current_user: CurrentUser,
):
    """Create Stripe Checkout Session for credit top-up package.

    Client sends package_id, server resolves the Stripe Price ID from
    the CreditPackage table. Returns checkout URL. Trial users blocked.
    """
    settings = get_settings()
    try:
        url = await SubscriptionService.create_topup_checkout(
            db=db,
            user_id=current_user.id,
            email=current_user.email,
            name=f"{current_user.first_name} {current_user.last_name}".strip() or None,
            user_class=current_user.user_class,
            package_id=body.package_id,
            success_url=f"{settings.frontend_url}/settings/billing?topup=success",
            cancel_url=f"{settings.frontend_url}/settings/billing",
        )
    except CheckoutValidationError as e:
        raise HTTPException(status_code=400, detail={"detail": e.message, "code": e.code})
    except StripeConfigError as e:
        logger.error("Stripe not configured for top-up", extra={"error": str(e)})
        raise HTTPException(status_code=503, detail="Payment service not configured")

    return CheckoutResponse(checkout_url=url)


@router.get("/packages", response_model=list[CreditPackageResponse])
async def get_credit_packages(db: DbSession, current_user: CurrentUser):
    """Return available credit packages for purchase.

    Returns only active packages, sorted by display_order ascending.
    """
    result = await db.execute(
        select(CreditPackage)
        .where(CreditPackage.is_active == True)  # noqa: E712
        .order_by(CreditPackage.display_order.asc())
    )
    packages = result.scalars().all()

    return [
        CreditPackageResponse(
            id=str(pkg.id),
            name=pkg.name,
            credit_amount=pkg.credit_amount,
            price_cents=pkg.price_cents,
            price_display=f"${pkg.price_cents / 100:.2f}",
        )
        for pkg in packages
    ]
