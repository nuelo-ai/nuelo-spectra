"""Admin billing management endpoints.

Provides endpoints for viewing user billing details, force-setting tier,
admin subscription cancellation, and issuing refunds.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.dependencies import CurrentAdmin, DbSession
from app.exceptions.stripe import CheckoutValidationError
from app.models.payment_history import PaymentHistory
from app.models.stripe_event import StripeEvent
from app.models.subscription import Subscription
from app.schemas.admin_billing import (
    AdminCancelResponse,
    ForceSetTierRequest,
    ForceSetTierResponse,
    PaymentHistoryItem,
    RefundRequest,
    RefundResponse,
    StripeEventItem,
    SubscriptionStatusResponse,
    UserBillingDetailResponse,
)
from app.services.subscription import SubscriptionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["admin-billing"])


@router.get("/users/{user_id}", response_model=UserBillingDetailResponse)
async def get_user_billing_detail(
    user_id: UUID,
    admin: CurrentAdmin,
    db: DbSession,
):
    """Get a user's subscription status, payment history, and Stripe event log."""
    # Subscription
    sub_result = await db.execute(
        select(Subscription).where(Subscription.user_id == user_id)
    )
    sub = sub_result.scalar_one_or_none()

    if sub:
        subscription = SubscriptionStatusResponse(
            has_subscription=True,
            plan_tier=sub.plan_tier,
            status=sub.status,
            stripe_customer_id=sub.stripe_customer_id,
            stripe_subscription_id=sub.stripe_subscription_id,
            current_period_start=sub.current_period_start,
            current_period_end=sub.current_period_end,
            cancel_at_period_end=sub.cancel_at_period_end,
        )
    else:
        subscription = SubscriptionStatusResponse(has_subscription=False)

    # Payment history
    payment_result = await db.execute(
        select(PaymentHistory)
        .where(PaymentHistory.user_id == user_id)
        .order_by(PaymentHistory.created_at.desc())
    )
    payments = [
        PaymentHistoryItem(
            id=str(p.id),
            created_at=p.created_at,
            payment_type=p.payment_type,
            amount_cents=p.amount_cents,
            currency=p.currency,
            credit_amount=float(p.credit_amount) if p.credit_amount is not None else None,
            status=p.status,
            stripe_payment_intent_id=p.stripe_payment_intent_id,
        )
        for p in payment_result.scalars().all()
    ]

    # Stripe events
    event_result = await db.execute(
        select(StripeEvent)
        .where(StripeEvent.user_id == user_id)
        .order_by(StripeEvent.processed_at.desc())
    )
    stripe_events = [
        StripeEventItem(
            id=str(e.id),
            stripe_event_id=e.stripe_event_id,
            event_type=e.event_type,
            processed_at=e.processed_at,
        )
        for e in event_result.scalars().all()
    ]

    return UserBillingDetailResponse(
        subscription=subscription,
        payments=payments,
        stripe_events=stripe_events,
    )


@router.post("/users/{user_id}/force-set-tier", response_model=ForceSetTierResponse)
async def force_set_tier(
    user_id: UUID,
    body: ForceSetTierRequest,
    admin: CurrentAdmin,
    db: DbSession,
):
    """Force-set a user's tier with mandatory reason and Stripe sync."""
    try:
        result = await SubscriptionService.admin_force_set_tier(
            db, user_id, body.new_tier, body.reason, admin.id
        )
        await db.commit()
        return ForceSetTierResponse(**result)
    except CheckoutValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/users/{user_id}/cancel", response_model=AdminCancelResponse)
async def admin_cancel_subscription(
    user_id: UUID,
    admin: CurrentAdmin,
    db: DbSession,
):
    """Cancel a user's subscription on their behalf."""
    try:
        result = await SubscriptionService.admin_cancel_subscription(
            db, user_id, admin.id
        )
        await db.commit()
        return AdminCancelResponse(**result)
    except CheckoutValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/users/{user_id}/refund", response_model=RefundResponse)
async def admin_refund(
    user_id: UUID,
    body: RefundRequest,
    admin: CurrentAdmin,
    db: DbSession,
):
    """Issue a full or partial refund with proportional credit deduction."""
    try:
        result = await SubscriptionService.admin_refund(
            db, user_id, body.payment_id, body.amount_cents, admin.id
        )
        await db.commit()
        return RefundResponse(**result)
    except CheckoutValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
