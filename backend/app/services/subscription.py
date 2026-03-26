"""SubscriptionService for all Stripe payment operations.

Handles customer creation, checkout session creation, and all webhook event
processing. This is the single point of contact with the Stripe API.
"""

import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.exceptions.stripe import (
    CheckoutValidationError,
    StripeConfigError,
)
from app.models.credit_package import CreditPackage
from app.models.credit_transaction import CreditTransaction
from app.models.payment_history import PaymentHistory
from app.models.subscription import Subscription
from app.models.user import User
from app.models.user_credit import UserCredit
from app.services.admin.audit import log_admin_action
from app.services.credit import CreditService
from app.services.email import (
    send_payment_failed_email,
    send_renewal_confirmation_email,
    send_subscription_confirmation_email,
    send_topup_confirmation_email,
)
from app.services.platform_settings import get_all as get_platform_settings
from app.services.user_class import get_class_config

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Service for Stripe subscription and payment operations.

    All methods are @staticmethod async, following the established
    single-service-per-domain pattern (like CreditService).
    """

    @staticmethod
    def _get_stripe_client() -> stripe.StripeClient:
        """Create a StripeClient instance with the configured secret key.

        Raises:
            StripeConfigError: If stripe_secret_key is empty or not configured.
        """
        settings = get_settings()
        if not settings.stripe_secret_key:
            raise StripeConfigError("Stripe secret key is not configured")
        return stripe.StripeClient(settings.stripe_secret_key)

    @staticmethod
    async def get_or_create_customer(
        db: AsyncSession, user_id: UUID, email: str, name: str | None = None
    ) -> str:
        """Get existing Stripe customer ID or create a new customer.

        Checks the Subscription table for an existing stripe_customer_id.
        If not found, creates a new Stripe customer. Does NOT create a
        Subscription row (that happens on checkout.session.completed).

        Returns:
            Stripe customer ID string.
        """
        # Check for existing customer ID in Subscription table
        result = await db.execute(
            select(Subscription.stripe_customer_id).where(
                Subscription.user_id == user_id
            )
        )
        existing_customer_id = result.scalar_one_or_none()

        if existing_customer_id:
            logger.info(
                "Found existing Stripe customer",
                extra={"user_id": str(user_id), "customer_id": existing_customer_id},
            )
            return existing_customer_id

        # Create new Stripe customer
        client = SubscriptionService._get_stripe_client()
        customer = client.v1.customers.create(
            params={
                "email": email,
                "name": name or email,
                "metadata": {"user_id": str(user_id)},
            }
        )

        logger.info(
            "Created new Stripe customer",
            extra={"user_id": str(user_id), "customer_id": customer.id},
        )
        return customer.id

    @staticmethod
    async def create_subscription_checkout(
        db: AsyncSession,
        user_id: UUID,
        email: str,
        name: str | None,
        plan_tier: str,
        success_url: str,
        cancel_url: str,
    ) -> str:
        """Create a Stripe Checkout Session for a subscription.

        Validates plan tier, checks for existing subscription, looks up
        price ID from platform settings, and creates the checkout session.

        Returns:
            Checkout session URL string.

        Raises:
            CheckoutValidationError: If plan_tier is invalid or user already subscribed.
            StripeConfigError: If price ID is not configured.
        """
        # Validate plan tier
        if plan_tier not in ("standard", "premium"):
            raise CheckoutValidationError(
                f"Invalid plan tier: {plan_tier}. Must be 'standard' or 'premium'.",
                "invalid_plan_tier",
            )

        # Check for existing active subscription
        result = await db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.status.in_(("active", "trialing")),
            )
        )
        existing_sub = result.scalar_one_or_none()
        if existing_sub and existing_sub.plan_tier == plan_tier:
            raise CheckoutValidationError(
                "Already subscribed to this plan", "already_subscribed"
            )

        # Look up price ID from platform settings
        platform_settings = await get_platform_settings(db)
        price_key = f"stripe_price_{plan_tier}_monthly"
        price_id = json.loads(platform_settings.get(price_key, '""'))
        if not price_id:
            raise StripeConfigError(
                f"Stripe price ID not configured for {plan_tier} plan"
            )

        # Get or create Stripe customer
        customer_id = await SubscriptionService.get_or_create_customer(
            db, user_id, email, name
        )

        # Create checkout session
        client = SubscriptionService._get_stripe_client()
        session = client.v1.checkout.sessions.create(
            params={
                "mode": "subscription",
                "customer": customer_id,
                "line_items": [{"price": price_id, "quantity": 1}],
                "success_url": success_url,
                "cancel_url": cancel_url,
                "client_reference_id": str(user_id),
                "metadata": {
                    "user_id": str(user_id),
                    "plan_tier": plan_tier,
                },
                "allow_promotion_codes": True,
                "subscription_data": {
                    "metadata": {
                        "user_id": str(user_id),
                        "plan_tier": plan_tier,
                    }
                },
            }
        )

        logger.info(
            "Created subscription checkout session",
            extra={
                "user_id": str(user_id),
                "plan_tier": plan_tier,
                "session_id": session.id,
            },
        )
        return session.url

    @staticmethod
    async def create_topup_checkout(
        db: AsyncSession,
        user_id: UUID,
        email: str,
        name: str | None,
        user_class: str,
        package_id: UUID,
        success_url: str,
        cancel_url: str,
    ) -> str:
        """Create a Stripe Checkout Session for a credit top-up.

        Validates user eligibility and package, then creates a one-time
        payment checkout session.

        Returns:
            Checkout session URL string.

        Raises:
            CheckoutValidationError: If user is on free trial or package invalid.
            StripeConfigError: If package has no stripe_price_id.
        """
        if user_class == "free_trial":
            raise CheckoutValidationError(
                "Credit top-ups not available during free trial",
                "trial_topup_blocked",
            )

        # Look up credit package
        result = await db.execute(
            select(CreditPackage).where(CreditPackage.id == package_id)
        )
        package = result.scalar_one_or_none()
        if not package or not package.is_active:
            raise CheckoutValidationError(
                "Credit package not found or inactive", "invalid_package"
            )

        if not package.stripe_price_id:
            raise StripeConfigError(
                f"Stripe price ID not configured for package '{package.name}'"
            )

        # Get or create Stripe customer
        customer_id = await SubscriptionService.get_or_create_customer(
            db, user_id, email, name
        )

        # Create checkout session
        client = SubscriptionService._get_stripe_client()
        session = client.v1.checkout.sessions.create(
            params={
                "mode": "payment",
                "customer": customer_id,
                "line_items": [{"price": package.stripe_price_id, "quantity": 1}],
                "success_url": success_url,
                "cancel_url": cancel_url,
                "client_reference_id": str(user_id),
                "allow_promotion_codes": True,
                "metadata": {
                    "user_id": str(user_id),
                    "package_id": str(package_id),
                    "credit_amount": str(package.credit_amount),
                    "payment_type": "topup",
                },
            }
        )

        logger.info(
            "Created top-up checkout session",
            extra={
                "user_id": str(user_id),
                "package_id": str(package_id),
                "session_id": session.id,
            },
        )
        return session.url

    @staticmethod
    async def change_plan(
        db: AsyncSession, user_id: UUID, new_plan_tier: str
    ) -> dict:
        """Change subscription plan (upgrade or downgrade).

        Upgrade: proration_behavior="always_invoice" (immediate charge).
        Downgrade: proration_behavior="none" (takes effect at period end).

        CRITICAL: Uses stripe.subscriptions.update() -- NOT a new checkout session.
        Card is already on file from initial subscription.
        """
        if new_plan_tier not in ("standard", "premium"):
            raise CheckoutValidationError(
                f"Invalid plan tier: {new_plan_tier}", "invalid_plan_tier"
            )

        # Look up existing active subscription
        result = await db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.status.in_(("active", "past_due")),
            )
        )
        sub = result.scalar_one_or_none()
        if not sub or not sub.stripe_subscription_id:
            raise CheckoutValidationError(
                "No active subscription to change", "no_subscription"
            )

        if sub.plan_tier == new_plan_tier:
            raise CheckoutValidationError(
                "Already on this plan", "same_plan"
            )

        # Determine upgrade vs downgrade
        tier_order = {"standard": 1, "premium": 2}
        current_rank = tier_order.get(sub.plan_tier, 0)
        new_rank = tier_order.get(new_plan_tier, 0)
        is_upgrade = new_rank > current_rank

        # Resolve new price ID from platform settings
        platform_settings = await get_platform_settings(db)
        price_key = f"stripe_price_{new_plan_tier}_monthly"
        price_id = json.loads(platform_settings.get(price_key, '""'))
        if not price_id:
            raise StripeConfigError(
                f"Stripe price ID not configured for {new_plan_tier} plan"
            )

        # Get current subscription item ID from Stripe
        client = SubscriptionService._get_stripe_client()
        stripe_sub = client.v1.subscriptions.retrieve(sub.stripe_subscription_id)
        current_item_id = stripe_sub["items"]["data"][0]["id"]

        # Update subscription on Stripe
        update_params = {
            "items": [{"id": current_item_id, "price": price_id}],
            "metadata": {"plan_tier": new_plan_tier, "user_id": str(user_id)},
        }

        if is_upgrade:
            update_params["proration_behavior"] = "always_invoice"
        else:
            update_params["proration_behavior"] = "none"

        updated_sub = client.v1.subscriptions.update(
            sub.stripe_subscription_id, params=update_params
        )

        # Get proration amount from the latest invoice's proration line items
        proration_amount = 0
        latest_invoice_id = updated_sub.get("latest_invoice")
        if latest_invoice_id and is_upgrade:
            try:
                invoice = client.v1.invoices.retrieve(latest_invoice_id)
                # Sum only proration lines (exclude next full cycle)
                period_end = updated_sub["items"]["data"][0]["current_period_end"]
                for line in invoice.get("lines", {}).get("data", []):
                    period = line.get("period", {})
                    if period.get("start", 0) >= period_end:
                        continue
                    proration_amount += line.get("amount", 0)
                proration_amount = max(proration_amount, 0)
            except Exception:
                pass  # Non-critical — billing history will show $0

        # Update local subscription record
        sub.plan_tier = new_plan_tier

        # Update user class
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if user:
            user.user_class = new_plan_tier

        # For upgrades: reset credits to new tier allocation
        allocation = None
        if is_upgrade:
            class_config = get_class_config(new_plan_tier)
            allocation = class_config.get("credits", 0) if class_config else 0
            logger.info(
                "Upgrade credit reset",
                extra={"user_id": str(user_id), "new_tier": new_plan_tier, "allocation": allocation},
            )
            credit_result = await db.execute(
                select(UserCredit).where(UserCredit.user_id == user_id).with_for_update()
            )
            credit = credit_result.scalar_one_or_none()
            if credit:
                logger.info(
                    "Credit before reset",
                    extra={"balance": str(credit.balance), "user_id": str(user_id)},
                )
                await CreditService.execute_reset(db, credit, allocation, "plan_upgrade")
                logger.info(
                    "Credit after reset",
                    extra={"balance": str(credit.balance), "user_id": str(user_id)},
                )
            else:
                logger.warning("No UserCredit row found for upgrade reset", extra={"user_id": str(user_id)})
        else:
            logger.info(
                "Downgrade — no credit reset",
                extra={"user_id": str(user_id), "is_upgrade": is_upgrade, "current_rank": current_rank, "new_rank": new_rank},
            )

        # Record plan change in payment history
        change_type = "upgrade" if is_upgrade else "downgrade"
        display_names = {"standard": "Basic", "premium": "Premium"}
        db.add(
            PaymentHistory(
                user_id=user_id,
                stripe_payment_intent_id=None,
                amount_cents=proration_amount if is_upgrade else 0,
                currency="usd",
                payment_type=f"plan_{change_type}",
                credit_amount=allocation if is_upgrade else None,
                status="succeeded",
            )
        )

        await db.flush()

        return {
            "change_type": change_type,
            "new_plan": display_names.get(new_plan_tier, new_plan_tier),
            "effective_at": "immediately" if is_upgrade else (
                sub.current_period_end.isoformat() if sub.current_period_end else "end of billing cycle"
            ),
        }

    @staticmethod
    async def cancel_subscription(db: AsyncSession, user_id: UUID) -> dict:
        """Cancel subscription at end of billing period.

        CRITICAL: Uses stripe.subscriptions.update(cancel_at_period_end=True)
        -- NOT stripe.subscriptions.cancel() which immediately terminates.
        """
        result = await db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.status.in_(("active", "past_due")),
            )
        )
        sub = result.scalar_one_or_none()
        if not sub or not sub.stripe_subscription_id:
            raise CheckoutValidationError(
                "No active subscription to cancel", "no_subscription"
            )

        client = SubscriptionService._get_stripe_client()
        client.v1.subscriptions.update(
            sub.stripe_subscription_id,
            params={"cancel_at_period_end": True},
        )

        sub.cancel_at_period_end = True
        await db.flush()

        return {
            "cancel_at": sub.current_period_end.isoformat() if sub.current_period_end else None,
        }

    @staticmethod
    async def handle_checkout_completed(db: AsyncSession, session: dict) -> None:
        """Handle checkout.session.completed webhook event.

        For subscription checkouts: creates/updates Subscription, updates user
        class, resets credits, and records payment history.
        For top-up checkouts: adds purchased credits and records payment history.
        """
        user_id = UUID(session["client_reference_id"])
        mode = session["mode"]

        logger.info(
            "Processing checkout.session.completed",
            extra={"user_id": str(user_id), "mode": mode},
        )

        if mode == "subscription":
            await SubscriptionService._handle_subscription_checkout(db, session, user_id)
        elif mode == "payment":
            await SubscriptionService._handle_topup_checkout(db, session, user_id)

    @staticmethod
    async def _handle_subscription_checkout(
        db: AsyncSession, session: dict, user_id: UUID
    ) -> None:
        """Process subscription checkout completion."""
        subscription_id = session["subscription"]
        plan_tier = session.get("metadata", {}).get("plan_tier", "standard")
        customer_id = session["customer"]
        amount_total = session.get("amount_total", 0)

        # Retrieve subscription details from Stripe
        client = SubscriptionService._get_stripe_client()
        stripe_sub = client.v1.subscriptions.retrieve(subscription_id)

        # Parse period dates from subscription item (SDK v14+: period is on items, not top-level)
        sub_item = stripe_sub["items"]["data"][0]
        period_start = datetime.fromtimestamp(
            sub_item["current_period_start"], tz=timezone.utc
        )
        period_end = datetime.fromtimestamp(
            sub_item["current_period_end"], tz=timezone.utc
        )

        # Upsert Subscription row
        result = await db.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        sub = result.scalar_one_or_none()

        if sub:
            sub.stripe_subscription_id = subscription_id
            sub.stripe_customer_id = customer_id
            sub.plan_tier = plan_tier
            sub.status = "active"
            sub.current_period_start = period_start
            sub.current_period_end = period_end
            sub.cancel_at_period_end = False
        else:
            sub = Subscription(
                user_id=user_id,
                stripe_subscription_id=subscription_id,
                stripe_customer_id=customer_id,
                plan_tier=plan_tier,
                status="active",
                current_period_start=period_start,
                current_period_end=period_end,
                cancel_at_period_end=False,
            )
            db.add(sub)

        # Update User.user_class to the plan tier
        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if user:
            user.user_class = plan_tier

        # Reset subscription credits to tier allocation
        class_config = get_class_config(plan_tier)
        allocation = class_config.get("credits", 0) if class_config else 0

        credit_result = await db.execute(
            select(UserCredit)
            .where(UserCredit.user_id == user_id)
            .with_for_update()
        )
        credit = credit_result.scalar_one_or_none()
        if credit:
            await CreditService.execute_reset(
                db, credit, allocation, "subscription_activation"
            )

        # Resolve payment_intent for the initial subscription payment.
        # Subscription-mode checkout sessions have payment_intent=None because
        # the actual charge goes through an invoice.  Retrieve the invoice to
        # get the real payment_intent so refunds can reference it.
        payment_intent_id = session.get("payment_intent")
        invoice_id = session.get("invoice")
        if not payment_intent_id and invoice_id:
            # Stripe API 2026-02-25: Invoice no longer has a top-level payment_intent.
            # Payment info is under invoice.payments.data[].payment.payment_intent.
            try:
                inv = client.v1.invoices.retrieve(
                    invoice_id, params={"expand": ["payments.data.payment.payment_intent"]}
                )
                payments_data = getattr(inv, "payments", None)
                if payments_data and payments_data.get("data"):
                    first_payment = payments_data["data"][0]
                    payment_obj = getattr(first_payment, "payment", None) or first_payment.get("payment", {})
                    pi = payment_obj.get("payment_intent") if isinstance(payment_obj, dict) else getattr(payment_obj, "payment_intent", None)
                    if pi:
                        payment_intent_id = pi if isinstance(pi, str) else getattr(pi, "id", str(pi))
            except Exception as e:
                logger.warning(f"Could not resolve payment_intent from invoice: {e}")

        # Record payment history
        db.add(
            PaymentHistory(
                user_id=user_id,
                stripe_payment_intent_id=payment_intent_id,
                amount_cents=amount_total,
                currency=session.get("currency", "usd"),
                payment_type="subscription",
                credit_amount=allocation,
                status="succeeded",
            )
        )

        await db.flush()

        # Send confirmation email
        display_names = {"standard": "Basic", "premium": "Premium"}
        plan_display = display_names.get(plan_tier, plan_tier.title())
        amount_display = f"${amount_total / 100:.2f}" if amount_total else "$0.00"

        if user:
            settings = get_settings()
            await send_subscription_confirmation_email(
                user.email, user.first_name, plan_display, amount_display, settings
            )

        logger.info(
            "Subscription activated",
            extra={
                "user_id": str(user_id),
                "plan_tier": plan_tier,
                "subscription_id": subscription_id,
            },
        )

    @staticmethod
    async def _handle_topup_checkout(
        db: AsyncSession, session: dict, user_id: UUID
    ) -> None:
        """Process top-up checkout completion."""
        metadata = session.get("metadata", {})
        package_id = metadata.get("package_id")
        credit_amount = Decimal(metadata.get("credit_amount", "0"))
        amount_total = session.get("amount_total", 0)

        # Add purchased credits with SELECT FOR UPDATE
        credit_result = await db.execute(
            select(UserCredit)
            .where(UserCredit.user_id == user_id)
            .with_for_update()
        )
        credit = credit_result.scalar_one_or_none()
        if credit:
            old_purchased = Decimal(str(credit.purchased_balance))
            credit.purchased_balance = old_purchased + credit_amount

            # Log credit transaction
            db.add(
                CreditTransaction(
                    user_id=user_id,
                    amount=credit_amount,
                    balance_after=Decimal(str(credit.purchased_balance)),
                    transaction_type="topup",
                    balance_pool="purchased",
                )
            )

        # Record payment history
        db.add(
            PaymentHistory(
                user_id=user_id,
                stripe_payment_intent_id=session.get("payment_intent"),
                amount_cents=amount_total,
                currency=session.get("currency", "usd"),
                payment_type="topup",
                credit_amount=float(credit_amount),
                status="succeeded",
            )
        )

        await db.flush()

        # Send confirmation email
        amount_display = f"${amount_total / 100:.2f}" if amount_total else "$0.00"
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if user:
            settings = get_settings()
            await send_topup_confirmation_email(
                user.email, user.first_name, int(credit_amount), amount_display, settings
            )

        logger.info(
            "Top-up credits added",
            extra={
                "user_id": str(user_id),
                "credit_amount": str(credit_amount),
                "package_id": package_id,
            },
        )

    @staticmethod
    async def handle_invoice_paid(db: AsyncSession, invoice: dict) -> None:
        """Handle invoice.paid webhook event.

        Resets subscription credits for renewal billing cycles.
        Skips subscription_create (handled by checkout.session.completed).
        """
        subscription_id = invoice.get("subscription")
        if not subscription_id:
            return  # Not subscription-related

        # Look up Subscription
        result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == subscription_id
            )
        )
        sub = result.scalar_one_or_none()
        if not sub:
            logger.warning(
                "Subscription not found for invoice.paid",
                extra={"subscription_id": subscription_id},
            )
            return

        # Skip initial subscription creation (handled by checkout.session.completed)
        billing_reason = invoice.get("billing_reason")
        if billing_reason == "subscription_create":
            logger.info(
                "Skipping subscription_create invoice (handled by checkout)",
                extra={"subscription_id": subscription_id},
            )
            return

        # Only process renewal and update invoices
        if billing_reason not in ("subscription_cycle", "subscription_update"):
            logger.info(
                "Skipping non-renewal invoice",
                extra={
                    "subscription_id": subscription_id,
                    "billing_reason": billing_reason,
                },
            )
            return

        logger.info(
            "Processing invoice.paid for renewal",
            extra={
                "subscription_id": subscription_id,
                "billing_reason": billing_reason,
            },
        )

        # Update period dates from Stripe subscription (SDK v14+: period is on items)
        client = SubscriptionService._get_stripe_client()
        stripe_sub = client.v1.subscriptions.retrieve(subscription_id)
        sub_item = stripe_sub["items"]["data"][0]
        sub.current_period_start = datetime.fromtimestamp(
            sub_item["current_period_start"], tz=timezone.utc
        )
        sub.current_period_end = datetime.fromtimestamp(
            sub_item["current_period_end"], tz=timezone.utc
        )

        # Look up tier allocation and reset credits
        class_config = get_class_config(sub.plan_tier)
        allocation = class_config.get("credits", 0) if class_config else 0

        credit_result = await db.execute(
            select(UserCredit)
            .where(UserCredit.user_id == sub.user_id)
            .with_for_update()
        )
        credit = credit_result.scalar_one_or_none()
        if credit:
            await CreditService.execute_reset(
                db, credit, allocation, "billing_cycle_reset"
            )

        # Record payment history
        db.add(
            PaymentHistory(
                user_id=sub.user_id,
                stripe_payment_intent_id=invoice.get("payment_intent"),
                amount_cents=invoice.get("amount_paid", 0),
                currency=invoice.get("currency", "usd"),
                payment_type="subscription",
                credit_amount=allocation,
                status="succeeded",
            )
        )

        await db.flush()

        # Send renewal confirmation email
        display_names = {"standard": "Basic", "premium": "Premium"}
        plan_display = display_names.get(sub.plan_tier, sub.plan_tier.title())
        amount_display = f"${invoice.get('amount_paid', 0) / 100:.2f}"

        user_result = await db.execute(select(User).where(User.id == sub.user_id))
        user = user_result.scalar_one_or_none()
        if user:
            settings = get_settings()
            await send_renewal_confirmation_email(
                user.email, user.first_name, plan_display, amount_display, allocation, settings
            )

        logger.info(
            "Invoice paid processed — credits reset",
            extra={
                "user_id": str(sub.user_id),
                "subscription_id": subscription_id,
                "allocation": allocation,
            },
        )

    @staticmethod
    async def handle_invoice_payment_failed(db: AsyncSession, invoice: dict) -> None:
        """Handle invoice.payment_failed webhook event.

        Marks subscription as past_due and sends payment failure email.
        """
        subscription_id = invoice.get("subscription")
        if not subscription_id:
            return

        # Look up Subscription
        result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == subscription_id
            )
        )
        sub = result.scalar_one_or_none()
        if not sub:
            logger.warning(
                "Subscription not found for invoice.payment_failed",
                extra={"subscription_id": subscription_id},
            )
            return

        logger.info(
            "Processing invoice.payment_failed",
            extra={"subscription_id": subscription_id, "user_id": str(sub.user_id)},
        )

        # Mark subscription as past_due
        sub.status = "past_due"

        # Look up user for email notification
        user_result = await db.execute(
            select(User).where(User.id == sub.user_id)
        )
        user = user_result.scalar_one_or_none()
        if user:
            settings = get_settings()
            await send_payment_failed_email(user.email, user.first_name, settings)

        # Record payment history
        db.add(
            PaymentHistory(
                user_id=sub.user_id,
                stripe_payment_intent_id=invoice.get("payment_intent"),
                amount_cents=invoice.get("amount_due", 0),
                currency=invoice.get("currency", "usd"),
                payment_type="subscription",
                credit_amount=None,
                status="failed",
            )
        )

        await db.flush()
        logger.info(
            "Subscription marked past_due",
            extra={"user_id": str(sub.user_id), "subscription_id": subscription_id},
        )

    @staticmethod
    async def handle_subscription_updated(db: AsyncSession, sub_data: dict) -> None:
        """Handle customer.subscription.updated webhook event.

        Updates subscription status, cancel_at_period_end, plan tier, and
        period dates. If plan tier changed, also updates User.user_class.
        """
        stripe_sub_id = sub_data["id"]

        result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == stripe_sub_id
            )
        )
        sub = result.scalar_one_or_none()
        if not sub:
            logger.warning(
                "Subscription not found for subscription.updated",
                extra={"stripe_subscription_id": stripe_sub_id},
            )
            return

        logger.info(
            "Processing customer.subscription.updated",
            extra={"stripe_subscription_id": stripe_sub_id, "user_id": str(sub.user_id)},
        )

        # Update status and cancel_at_period_end
        sub.status = sub_data.get("status", sub.status)
        sub.cancel_at_period_end = sub_data.get(
            "cancel_at_period_end", sub.cancel_at_period_end
        )

        # Determine new plan tier from metadata or price lookup_key
        new_plan_tier = None
        metadata = sub_data.get("metadata", {})
        if metadata.get("plan_tier"):
            new_plan_tier = metadata["plan_tier"]
        else:
            # Try to get from price lookup_key
            items = sub_data.get("items", {}).get("data", [])
            if items:
                lookup_key = items[0].get("price", {}).get("lookup_key")
                if lookup_key:
                    new_plan_tier = lookup_key

        # Update plan tier if changed
        if new_plan_tier and new_plan_tier != sub.plan_tier:
            old_tier = sub.plan_tier
            sub.plan_tier = new_plan_tier

            # Update User.user_class
            user_result = await db.execute(
                select(User).where(User.id == sub.user_id)
            )
            user = user_result.scalar_one_or_none()
            if user:
                user.user_class = new_plan_tier

            logger.info(
                "Plan tier changed",
                extra={
                    "user_id": str(sub.user_id),
                    "old_tier": old_tier,
                    "new_tier": new_plan_tier,
                },
            )

        # Update period dates
        if sub_data.get("current_period_start"):
            sub.current_period_start = datetime.fromtimestamp(
                sub_data["current_period_start"], tz=timezone.utc
            )
        if sub_data.get("current_period_end"):
            sub.current_period_end = datetime.fromtimestamp(
                sub_data["current_period_end"], tz=timezone.utc
            )

        await db.flush()

    @staticmethod
    async def handle_subscription_deleted(db: AsyncSession, sub_data: dict) -> None:
        """Handle customer.subscription.deleted webhook event.

        Cancels subscription, downgrades user to on_demand, and zeroes out
        subscription credits (purchased credits are preserved).
        """
        stripe_sub_id = sub_data["id"]

        result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == stripe_sub_id
            )
        )
        sub = result.scalar_one_or_none()
        if not sub:
            logger.warning(
                "Subscription not found for subscription.deleted",
                extra={"stripe_subscription_id": stripe_sub_id},
            )
            return

        logger.info(
            "Processing customer.subscription.deleted",
            extra={"stripe_subscription_id": stripe_sub_id, "user_id": str(sub.user_id)},
        )

        # Mark subscription as canceled
        sub.status = "canceled"
        sub.cancel_at_period_end = False

        # Downgrade user to on_demand
        user_result = await db.execute(
            select(User).where(User.id == sub.user_id)
        )
        user = user_result.scalar_one_or_none()
        if user:
            user.user_class = "on_demand"

        # Zero out subscription credits (preserve purchased)
        credit_result = await db.execute(
            select(UserCredit)
            .where(UserCredit.user_id == sub.user_id)
            .with_for_update()
        )
        credit = credit_result.scalar_one_or_none()
        if credit:
            old_balance = Decimal(str(credit.balance))
            if old_balance > 0:
                credit.balance = Decimal("0")

                # Log the credit zeroing transaction
                db.add(
                    CreditTransaction(
                        user_id=sub.user_id,
                        amount=-old_balance,
                        balance_after=Decimal("0"),
                        transaction_type="subscription_canceled",
                        balance_pool="subscription",
                    )
                )

        await db.flush()
        logger.info(
            "Subscription deleted — user downgraded to on_demand",
            extra={"user_id": str(sub.user_id), "stripe_subscription_id": stripe_sub_id},
        )

    # ---------------------------------------------------------------
    # Admin billing methods
    # ---------------------------------------------------------------

    @staticmethod
    async def admin_force_set_tier(
        db: AsyncSession,
        user_id: UUID,
        new_tier: str,
        reason: str,
        admin_id: UUID,
    ) -> dict:
        """Force-set a user's tier with Stripe sync and mandatory reason.

        - If downgrading to free_trial/on_demand and user has active sub: cancel Stripe sub immediately.
        - If upgrading to standard/premium with existing sub on different tier: update Stripe price.
        - If upgrading to standard/premium without sub: just set user_class (no Stripe billing created).
        """
        # Get current user
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise CheckoutValidationError("User not found", "user_not_found")

        old_tier = user.user_class
        if old_tier == new_tier:
            raise CheckoutValidationError("Already on this tier", "same_tier")

        stripe_synced = False
        stripe_action = None

        # Check for active subscription
        sub_result = await db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.status.in_(("active", "past_due", "trialing")),
            )
        )
        active_sub = sub_result.scalar_one_or_none()

        if new_tier in ("free_trial", "on_demand"):
            # Downgrade: cancel any active Stripe subscription immediately
            if active_sub and active_sub.stripe_subscription_id:
                try:
                    client = SubscriptionService._get_stripe_client()
                    client.v1.subscriptions.cancel(active_sub.stripe_subscription_id)
                    active_sub.status = "canceled"
                    active_sub.cancel_at_period_end = False
                    stripe_synced = True
                    stripe_action = "subscription_cancelled"
                except Exception as e:
                    logger.warning(
                        "Failed to cancel Stripe subscription during force-set-tier: %s",
                        str(e),
                    )
                    stripe_synced = False
        elif new_tier in ("standard", "premium"):
            if active_sub and active_sub.stripe_subscription_id:
                # Update Stripe subscription to new price (no proration for admin override)
                try:
                    platform_settings = await get_platform_settings(db)
                    price_key = f"stripe_price_{new_tier}_monthly"
                    price_id = json.loads(platform_settings.get(price_key, '""'))

                    if price_id:
                        client = SubscriptionService._get_stripe_client()
                        stripe_sub = client.v1.subscriptions.retrieve(
                            active_sub.stripe_subscription_id
                        )
                        current_item_id = stripe_sub["items"]["data"][0]["id"]
                        client.v1.subscriptions.update(
                            active_sub.stripe_subscription_id,
                            params={
                                "items": [{"id": current_item_id, "price": price_id}],
                                "proration_behavior": "none",
                                "metadata": {"plan_tier": new_tier, "user_id": str(user_id)},
                            },
                        )
                        active_sub.plan_tier = new_tier
                        stripe_synced = True
                        stripe_action = "subscription_updated"
                except Exception as e:
                    logger.warning(
                        "Failed to update Stripe subscription during force-set-tier: %s",
                        str(e),
                    )
                    stripe_synced = False
            else:
                # No active subscription — just set tier locally (no billing created)
                stripe_synced = True
                stripe_action = None

        # Update user_class
        user.user_class = new_tier

        # Log admin action
        await log_admin_action(
            db,
            admin_id,
            action="force_set_tier",
            target_type="user",
            target_id=str(user_id),
            details={
                "previous_tier": old_tier,
                "new_tier": new_tier,
                "reason": reason,
            },
        )

        await db.flush()

        return {
            "previous_tier": old_tier,
            "new_tier": new_tier,
            "stripe_synced": stripe_synced,
            "stripe_action": stripe_action,
        }

    @staticmethod
    async def admin_cancel_subscription(
        db: AsyncSession, user_id: UUID, admin_id: UUID
    ) -> dict:
        """Admin-initiated subscription cancellation with audit logging."""
        result = await SubscriptionService.cancel_subscription(db, user_id)

        await log_admin_action(
            db,
            admin_id,
            action="admin_cancel_subscription",
            target_type="user",
            target_id=str(user_id),
            details={"cancel_at": result.get("cancel_at")},
        )

        await db.flush()
        return result

    @staticmethod
    async def admin_refund(
        db: AsyncSession,
        user_id: UUID,
        payment_id: str,
        amount_cents: int | None,
        admin_id: UUID,
    ) -> dict:
        """Issue a full or partial refund with proportional credit deduction.

        Steps:
        1. Validate payment belongs to user
        2. Issue Stripe refund
        3. Calculate and deduct proportional credits from purchased_balance
        4. Record refund in payment history
        5. Log admin action
        """
        from uuid import UUID as _UUID

        # Look up payment
        payment_result = await db.execute(
            select(PaymentHistory).where(
                PaymentHistory.id == _UUID(payment_id),
                PaymentHistory.user_id == user_id,
            )
        )
        payment = payment_result.scalar_one_or_none()
        if not payment:
            raise CheckoutValidationError(
                "Payment not found for this user", "payment_not_found"
            )

        if not payment.stripe_payment_intent_id:
            raise CheckoutValidationError(
                "Payment has no Stripe payment intent (cannot refund)",
                "no_payment_intent",
            )

        # Determine refund amount
        refund_amount = amount_cents if amount_cents is not None else payment.amount_cents
        if refund_amount <= 0:
            raise CheckoutValidationError(
                "Refund amount must be positive", "invalid_refund_amount"
            )
        if refund_amount > payment.amount_cents:
            raise CheckoutValidationError(
                "Refund amount exceeds original payment", "refund_exceeds_payment"
            )

        is_full_refund = refund_amount == payment.amount_cents

        # Issue Stripe refund
        client = SubscriptionService._get_stripe_client()
        refund_params: dict = {
            "payment_intent": payment.stripe_payment_intent_id,
            "reason": "requested_by_customer",
        }
        if not is_full_refund:
            refund_params["amount"] = refund_amount

        stripe_refund = client.v1.refunds.create(params=refund_params)

        # Calculate proportional credit deduction
        credits_to_deduct = Decimal("0")
        if payment.credit_amount and payment.amount_cents > 0:
            credits_to_deduct = (
                Decimal(str(refund_amount))
                / Decimal(str(payment.amount_cents))
                * Decimal(str(payment.credit_amount))
            )
            credits_to_deduct = max(Decimal("0"), credits_to_deduct)

        # Deduct from purchased_balance
        if credits_to_deduct > 0:
            credit_result = await db.execute(
                select(UserCredit)
                .where(UserCredit.user_id == user_id)
                .with_for_update()
            )
            credit = credit_result.scalar_one_or_none()
            if credit:
                credit.purchased_balance = max(
                    Decimal("0"),
                    Decimal(str(credit.purchased_balance)) - credits_to_deduct,
                )

                # Record credit transaction
                db.add(
                    CreditTransaction(
                        user_id=user_id,
                        amount=-credits_to_deduct,
                        balance_after=Decimal(str(credit.purchased_balance)),
                        transaction_type="refund",
                        balance_pool="purchased",
                        reason=f"Refund for payment {payment_id}",
                    )
                )

        # Update original payment status
        payment.status = "refunded" if is_full_refund else "partial_refund"

        # Record refund in payment history
        db.add(
            PaymentHistory(
                user_id=user_id,
                stripe_payment_intent_id=None,
                amount_cents=-refund_amount,
                currency=payment.currency,
                payment_type="refund",
                credit_amount=-float(credits_to_deduct) if credits_to_deduct else None,
                status="succeeded",
            )
        )

        # Log admin action
        await log_admin_action(
            db,
            admin_id,
            action="admin_refund",
            target_type="payment",
            target_id=payment_id,
            details={
                "user_id": str(user_id),
                "refund_amount_cents": refund_amount,
                "credits_deducted": float(credits_to_deduct),
                "is_full_refund": is_full_refund,
            },
        )

        await db.flush()

        return {
            "refund_amount_cents": refund_amount,
            "credits_deducted": float(credits_to_deduct),
            "stripe_refund_id": stripe_refund.id,
        }
