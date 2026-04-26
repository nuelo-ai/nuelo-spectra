"""Stripe webhook endpoint with signature verification and event deduplication."""

import logging

import stripe
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy import select

from uuid import UUID as _UUID

from app.config import get_settings
from app.database import get_db
from app.models.stripe_event import StripeEvent
from app.models.subscription import Subscription
from app.services.subscription import SubscriptionService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["webhooks"])

EVENT_HANDLERS = {
    "checkout.session.completed": SubscriptionService.handle_checkout_completed,
    "invoice.paid": SubscriptionService.handle_invoice_paid,
    "invoice.payment_failed": SubscriptionService.handle_invoice_payment_failed,
    "customer.subscription.updated": SubscriptionService.handle_subscription_updated,
    "customer.subscription.deleted": SubscriptionService.handle_subscription_deleted,
}


@router.post("/webhooks/stripe", status_code=200)
async def stripe_webhook(request: Request):
    """Process Stripe webhook events with signature verification and deduplication.

    1. Verify Stripe-Signature header against webhook secret
    2. Check stripe_events table for duplicate event ID
    3. Dispatch to appropriate handler based on event type
    4. Record event in stripe_events table
    """
    settings = get_settings()
    payload = await request.body()  # Raw bytes -- do NOT parse before verification
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    # Verify signature
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_id = event["id"]
    event_type = event["type"]

    logger.info(
        "Stripe webhook received",
        extra={"event_id": event_id, "event_type": event_type},
    )

    # Get DB session
    async for db in get_db():
        # Deduplication check
        existing = await db.execute(
            select(StripeEvent).where(StripeEvent.stripe_event_id == event_id)
        )
        if existing.scalar_one_or_none():
            logger.info("Duplicate event skipped", extra={"event_id": event_id})
            return {"status": "already_processed"}

        # Dispatch to handler
        handler = EVENT_HANDLERS.get(event_type)
        if handler:
            try:
                await handler(db, event["data"]["object"])
                logger.info(
                    "Event processed",
                    extra={"event_id": event_id, "event_type": event_type},
                )
            except Exception as e:
                logger.exception(
                    "Webhook handler failed: %s", str(e),
                )
                raise HTTPException(
                    status_code=500, detail="Webhook processing failed"
                )
        else:
            logger.info("Unhandled event type", extra={"event_type": event_type})

        # Extract user_id from event data for per-user event log
        webhook_user_id = None
        event_data = event["data"]["object"]
        if event_type.startswith("checkout.session"):
            webhook_user_id = event_data.get("client_reference_id")
        elif event_type.startswith("invoice.") or event_type.startswith(
            "customer.subscription."
        ):
            # Look up user from subscription
            sub_id = event_data.get("subscription") or event_data.get("id")
            if sub_id:
                sub_result = await db.execute(
                    select(Subscription.user_id).where(
                        Subscription.stripe_subscription_id == sub_id
                    )
                )
                sub_user = sub_result.scalar_one_or_none()
                if sub_user:
                    webhook_user_id = str(sub_user)

        # Record processed event
        db.add(
            StripeEvent(
                stripe_event_id=event_id,
                event_type=event_type,
                user_id=_UUID(webhook_user_id) if webhook_user_id else None,
            )
        )
        await db.commit()

    return {"status": "success"}
