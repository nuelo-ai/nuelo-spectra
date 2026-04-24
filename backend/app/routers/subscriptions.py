"""Subscription and credit purchase checkout endpoints."""
import json
import logging

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.dependencies import CurrentUser, DbSession
from app.exceptions.stripe import CheckoutValidationError, StripeConfigError
from app.models.payment_history import PaymentHistory
from app.models.subscription import Subscription
from app.schemas.subscription import (
    BillingHistoryItem,
    BillingHistoryResponse,
    CancelResponse,
    CheckoutResponse,
    PlanChangePreviewResponse,
    PlanChangeRequest,
    PlanChangeResponse,
    PlanInfo,
    PlanPricingResponse,
    SubscriptionCheckoutRequest,
    SubscriptionStatusResponse,
    TopupCheckoutRequest,
)
from app.services.platform_settings import get_all as get_platform_settings
from app.services.subscription import SubscriptionService
from app.services.user_class import get_class_config, get_user_classes

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post("/checkout", response_model=CheckoutResponse)
async def create_subscription_checkout(
    body: SubscriptionCheckoutRequest,
    db: DbSession,
    current_user: CurrentUser,
):
    """Create Stripe Checkout Session for subscription plan.

    Client sends plan_tier ("standard" or "premium"), server resolves
    the Stripe Price ID from platform_settings. Returns checkout URL.
    """
    settings = get_settings()
    try:
        url = await SubscriptionService.create_subscription_checkout(
            db=db,
            user_id=current_user.id,
            email=current_user.email,
            name=f"{current_user.first_name} {current_user.last_name}".strip() or None,
            plan_tier=body.plan_tier,
            success_url=f"{settings.frontend_url}/settings/billing?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.frontend_url}/settings/plan",
        )
    except CheckoutValidationError as e:
        raise HTTPException(status_code=400, detail={"detail": e.message, "code": e.code})
    except StripeConfigError as e:
        logger.error("Stripe not configured for checkout", extra={"error": str(e)})
        raise HTTPException(status_code=503, detail="Payment service not configured")

    return CheckoutResponse(checkout_url=url)


@router.get("/status", response_model=SubscriptionStatusResponse)
async def get_subscription_status(
    db: DbSession,
    current_user: CurrentUser,
):
    """Get the current user's subscription status."""
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == current_user.id)
    )
    sub = result.scalar_one_or_none()

    if not sub:
        return SubscriptionStatusResponse(has_subscription=False)

    return SubscriptionStatusResponse(
        has_subscription=True,
        plan_tier=sub.plan_tier,
        status=sub.status,
        cancel_at_period_end=sub.cancel_at_period_end,
        current_period_end=sub.current_period_end.isoformat() if sub.current_period_end else None,
    )


@router.get("/plans", response_model=PlanPricingResponse)
async def get_plans(db: DbSession, current_user: CurrentUser):
    """Return plan pricing for Plan Selection page.

    Dynamically builds plan list from user_classes.yaml config (D-14).
    Reads features from config instead of hardcoding (D-13).
    """
    platform_settings = await get_platform_settings(db)
    tiers = get_user_classes()

    plans = []

    # Special case: on_demand tier (has_plan: false but shown in plan selection)
    on_demand = tiers.get("on_demand")
    if on_demand:
        on_demand_features = list(on_demand.get("features", []))
        max_collections = on_demand.get("max_active_collections", 3)
        if max_collections > 0:
            on_demand_features.append(f"Up to {max_collections} active collections")
        plans.append(PlanInfo(
            tier_key="on_demand",
            display_name=on_demand.get("display_name", "On Demand"),
            price_cents=0,
            price_display="Pay as you go",
            credit_allocation=on_demand.get("credits", 0),
            features=on_demand_features,
            is_popular=False,
        ))

    # Dynamic tiers with has_plan: true
    for tier_name, tier_config in tiers.items():
        if not tier_config.get("has_plan"):
            continue

        price_key = f"price_{tier_name}_monthly_cents"
        price_cents = json.loads(
            platform_settings.get(price_key, str(tier_config.get("price_cents", 0)))
        )

        # Build features: start with credits/month, then config features, then collections
        features = [f"{tier_config.get('credits', 0)} credits/month"]
        features.extend(tier_config.get("features", []))
        max_collections = tier_config.get("max_active_collections", -1)
        if max_collections > 0:
            features.append(f"Up to {max_collections} active collections")

        plans.append(PlanInfo(
            tier_key=tier_name,
            display_name=tier_config.get("display_name", tier_name.title()),
            price_cents=price_cents,
            price_display=f"${price_cents / 100:.2f}/month" if price_cents > 0 else "Pay as you go",
            credit_allocation=tier_config.get("credits", 0),
            features=features,
            is_popular=(tier_name == "standard"),
        ))

    return PlanPricingResponse(plans=plans, current_tier=current_user.user_class)


@router.get("/preview-change", response_model=PlanChangePreviewResponse)
async def preview_plan_change(
    plan_tier: str, db: DbSession, current_user: CurrentUser,
):
    """Preview proration cost for a plan change without executing it.

    Calls Stripe's upcoming invoice API to get the exact prorated amount.
    """
    if plan_tier not in ("standard", "premium"):
        raise HTTPException(status_code=400, detail="Invalid plan tier")

    # Look up existing subscription
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == current_user.id,
            Subscription.status.in_(("active", "past_due")),
        )
    )
    sub = result.scalar_one_or_none()
    if not sub or not sub.stripe_subscription_id:
        raise HTTPException(status_code=400, detail="No active subscription")

    if sub.plan_tier == plan_tier:
        raise HTTPException(status_code=400, detail="Already on this plan")

    # Determine upgrade vs downgrade
    tier_order = {"standard": 1, "premium": 2}
    current_rank = tier_order.get(sub.plan_tier, 0)
    new_rank = tier_order.get(plan_tier, 0)
    is_upgrade = new_rank > current_rank

    # Get new price ID
    platform_settings = await get_platform_settings(db)
    price_key = f"stripe_price_{plan_tier}_monthly"
    price_id = json.loads(platform_settings.get(price_key, '""'))
    if not price_id:
        raise HTTPException(status_code=503, detail="Price not configured")

    # Get current subscription item ID from Stripe
    client = SubscriptionService._get_stripe_client()
    stripe_sub = client.v1.subscriptions.retrieve(sub.stripe_subscription_id)
    current_item_id = stripe_sub["items"]["data"][0]["id"]

    # Preview upcoming invoice with the proposed change (SDK v14: create_preview)
    try:
        preview = client.v1.invoices.create_preview(params={
            "customer": sub.stripe_customer_id,
            "subscription": sub.stripe_subscription_id,
            "subscription_details": {
                "items": [{"id": current_item_id, "price": price_id}],
                "proration_behavior": "always_invoice" if is_upgrade else "none",
            },
        })
        # Sum only proration line items (exclude the next full billing cycle)
        # The next cycle line starts at current_period_end; proration lines start earlier
        lines = preview.get("lines", {}).get("data", [])
        period_end = stripe_sub["items"]["data"][0]["current_period_end"]
        proration_amount = 0
        for line in lines:
            period = line.get("period", {})
            # Skip lines that start at or after the current period end (next cycle)
            if period.get("start", 0) >= period_end:
                continue
            proration_amount += line.get("amount", 0)
        # Ensure non-negative
        proration_amount = max(proration_amount, 0)
    except Exception as e:
        logger.exception("Failed to preview plan change: %s", str(e))
        proration_amount = 0

    display_names = {"standard": "Basic", "premium": "Premium"}
    class_config = get_class_config(plan_tier) or {}

    return PlanChangePreviewResponse(
        proration_amount_cents=proration_amount,
        proration_display=f"${proration_amount / 100:.2f}",
        new_plan_display=display_names.get(plan_tier, plan_tier),
        new_credit_allocation=class_config.get("credits", 0),
        change_type="upgrade" if is_upgrade else "downgrade",
        effective_at="immediately" if is_upgrade else (
            sub.current_period_end.isoformat() if sub.current_period_end else "end of billing cycle"
        ),
    )


@router.post("/change", response_model=PlanChangeResponse)
async def change_subscription_plan(
    body: PlanChangeRequest, db: DbSession, current_user: CurrentUser,
):
    """Change subscription plan (upgrade or downgrade).

    Upgrade: immediate with proration. Downgrade: end of billing cycle.
    """
    try:
        result = await SubscriptionService.change_plan(
            db=db, user_id=current_user.id, new_plan_tier=body.plan_tier,
        )
        await db.commit()
    except CheckoutValidationError as e:
        raise HTTPException(status_code=400, detail={"detail": e.message, "code": e.code})
    except StripeConfigError as e:
        logger.error("Stripe not configured for plan change", extra={"error": str(e)})
        raise HTTPException(status_code=503, detail="Payment service not configured")

    return PlanChangeResponse(**result)


@router.post("/cancel", response_model=CancelResponse)
async def cancel_subscription(db: DbSession, current_user: CurrentUser):
    """Cancel subscription at end of current billing period.

    Sets cancel_at_period_end=True on Stripe. Access continues until period end.
    """
    try:
        result = await SubscriptionService.cancel_subscription(
            db=db, user_id=current_user.id,
        )
        await db.commit()
    except CheckoutValidationError as e:
        raise HTTPException(status_code=400, detail={"detail": e.message, "code": e.code})
    except StripeConfigError as e:
        logger.error("Stripe not configured for cancel", extra={"error": str(e)})
        raise HTTPException(status_code=503, detail="Payment service not configured")

    return CancelResponse(**result)


@router.post("/select-on-demand")
async def select_on_demand(db: DbSession, current_user: CurrentUser):
    """Switch user to On Demand tier (no Stripe checkout needed).

    If user has an active subscription, cancels it at period end.
    If no subscription, just updates user_class.
    """
    from app.models.user import User

    # Check if user already on_demand
    if current_user.user_class == "on_demand":
        raise HTTPException(
            status_code=400,
            detail={"detail": "Already on On Demand plan", "code": "already_on_demand"},
        )

    # If user has active subscription, cancel it
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == current_user.id,
            Subscription.status.in_(("active", "past_due")),
        )
    )
    sub = result.scalar_one_or_none()
    if sub and sub.stripe_subscription_id:
        try:
            client = SubscriptionService._get_stripe_client()
            client.v1.subscriptions.update(
                sub.stripe_subscription_id,
                params={"cancel_at_period_end": True},
            )
            sub.cancel_at_period_end = True
        except Exception as e:
            logger.error("Failed to cancel subscription for on-demand switch", extra={"error": str(e)})

    # Update user class to on_demand (immediate for users without subscription)
    user_result = await db.execute(select(User).where(User.id == current_user.id))
    user = user_result.scalar_one_or_none()
    if user:
        if not sub or not sub.stripe_subscription_id:
            # No subscription -- switch immediately
            user.user_class = "on_demand"
        # If has subscription, user stays on current tier until period end
        # (webhook will handle the actual downgrade)

    await db.flush()
    await db.commit()
    return {"status": "ok", "message": "Switched to On Demand plan"}


@router.get("/billing-history", response_model=BillingHistoryResponse)
async def get_billing_history(db: DbSession, current_user: CurrentUser):
    """Return the user's payment history sorted by date descending."""
    result = await db.execute(
        select(PaymentHistory)
        .where(PaymentHistory.user_id == current_user.id)
        .order_by(PaymentHistory.created_at.desc())
        .limit(50)
    )
    rows = result.scalars().all()

    type_display_map = {
        "subscription": "Subscription",
        "topup": "Credit Top-up",
        "refund": "Refund",
    }

    items = [
        BillingHistoryItem(
            id=str(row.id),
            date=row.created_at.isoformat(),
            payment_type=row.payment_type,
            type_display=type_display_map.get(row.payment_type, row.payment_type.title()),
            amount_cents=row.amount_cents,
            amount_display=f"${row.amount_cents / 100:.2f}",
            credit_amount=float(row.credit_amount) if row.credit_amount is not None else None,
            status=row.status,
        )
        for row in rows
    ]

    return BillingHistoryResponse(items=items)
