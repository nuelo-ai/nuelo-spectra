"""Tests for Stripe webhook endpoint and all webhook handlers (STRIPE-04 through STRIPE-10).

All tests use mocks for Stripe SDK calls and database sessions. No running
database or Stripe account is required.
"""

import json
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import stripe


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_event(event_type: str, event_id: str = "evt_test_123", data_object: dict | None = None):
    """Build a fake Stripe event dict."""
    return {
        "id": event_id,
        "type": event_type,
        "data": {"object": data_object or {}},
    }


def _mock_db_session():
    """Create a mock AsyncSession with common DB patterns."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    return db


# ---------------------------------------------------------------------------
# TestWebhookSignatureVerification (STRIPE-04)
# ---------------------------------------------------------------------------

class TestWebhookSignatureVerification:
    """STRIPE-04: Webhook signature verification."""

    @pytest.mark.asyncio
    @patch("app.routers.webhooks.get_db")
    @patch("stripe.Webhook.construct_event")
    async def test_valid_signature_accepted(self, mock_construct, mock_get_db):
        """Valid signature with unhandled event type returns 200."""
        from httpx import ASGITransport, AsyncClient
        from fastapi import FastAPI
        from app.routers.webhooks import router

        app = FastAPI()
        app.include_router(router)

        mock_construct.return_value = _make_event("unhandled.event.type")

        # Mock DB session that yields an async session
        mock_db = _mock_db_session()
        mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))

        async def fake_get_db():
            yield mock_db

        mock_get_db.side_effect = fake_get_db

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/webhooks/stripe",
                content=b'{"test": "payload"}',
                headers={"stripe-signature": "t=123,v1=abc"},
            )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_missing_signature_returns_400(self):
        """POST without Stripe-Signature header returns 400."""
        from httpx import ASGITransport, AsyncClient
        from fastapi import FastAPI
        from app.routers.webhooks import router

        app = FastAPI()
        app.include_router(router)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/webhooks/stripe",
                content=b'{"test": "payload"}',
            )

        assert response.status_code == 400
        assert "Missing Stripe-Signature header" in response.json()["detail"]

    @pytest.mark.asyncio
    @patch("stripe.Webhook.construct_event")
    async def test_invalid_signature_returns_400(self, mock_construct):
        """Invalid signature raises 400."""
        from httpx import ASGITransport, AsyncClient
        from fastapi import FastAPI
        from app.routers.webhooks import router

        app = FastAPI()
        app.include_router(router)

        mock_construct.side_effect = stripe.SignatureVerificationError(
            "Invalid", "sig_header"
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/webhooks/stripe",
                content=b'{"test": "payload"}',
                headers={"stripe-signature": "t=123,v1=bad"},
            )

        assert response.status_code == 400


# ---------------------------------------------------------------------------
# TestWebhookDeduplication (STRIPE-05)
# ---------------------------------------------------------------------------

class TestWebhookDeduplication:
    """STRIPE-05: Event deduplication via stripe_events table."""

    @pytest.mark.asyncio
    @patch("app.routers.webhooks.get_db")
    @patch("stripe.Webhook.construct_event")
    async def test_duplicate_event_returns_already_processed(
        self, mock_construct, mock_get_db
    ):
        """Duplicate event ID returns already_processed without calling handler."""
        from httpx import ASGITransport, AsyncClient
        from fastapi import FastAPI
        from app.routers.webhooks import router

        app = FastAPI()
        app.include_router(router)

        mock_construct.return_value = _make_event(
            "checkout.session.completed", event_id="evt_dup_001"
        )

        # Mock DB returns existing StripeEvent (duplicate)
        mock_db = _mock_db_session()
        existing_event = MagicMock()
        mock_db.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=existing_event))
        )

        async def fake_get_db():
            yield mock_db

        mock_get_db.side_effect = fake_get_db

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/webhooks/stripe",
                content=b"{}",
                headers={"stripe-signature": "t=123,v1=abc"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "already_processed"

    @pytest.mark.asyncio
    @patch("app.routers.webhooks.SubscriptionService")
    @patch("app.routers.webhooks.get_db")
    @patch("stripe.Webhook.construct_event")
    async def test_new_event_processed_and_recorded(
        self, mock_construct, mock_get_db, mock_service
    ):
        """New event is dispatched to handler and recorded in stripe_events."""
        from httpx import ASGITransport, AsyncClient
        from fastapi import FastAPI
        from app.routers.webhooks import router, EVENT_HANDLERS

        app = FastAPI()
        app.include_router(router)

        session_data = {"client_reference_id": str(uuid4()), "mode": "subscription"}
        mock_construct.return_value = _make_event(
            "checkout.session.completed", data_object=session_data
        )

        mock_db = _mock_db_session()
        # First execute: dedup check returns None (new event)
        mock_db.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        )

        mock_handler = AsyncMock()
        # Patch the handler in EVENT_HANDLERS dict
        original_handler = EVENT_HANDLERS.get("checkout.session.completed")
        EVENT_HANDLERS["checkout.session.completed"] = mock_handler

        async def fake_get_db():
            yield mock_db

        mock_get_db.side_effect = fake_get_db

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/webhooks/stripe",
                    content=b"{}",
                    headers={"stripe-signature": "t=123,v1=abc"},
                )

            assert response.status_code == 200
            mock_handler.assert_called_once()
            # Verify StripeEvent was added to session
            mock_db.add.assert_called()
        finally:
            # Restore original handler
            if original_handler:
                EVENT_HANDLERS["checkout.session.completed"] = original_handler


# ---------------------------------------------------------------------------
# TestCheckoutCompletedHandler (STRIPE-06)
# ---------------------------------------------------------------------------

class TestCheckoutCompletedHandler:
    """STRIPE-06: checkout.session.completed handler."""

    @pytest.mark.asyncio
    @patch("app.services.subscription.SubscriptionService._get_stripe_client")
    async def test_subscription_checkout_activates_subscription(self, mock_get_client):
        """Subscription checkout creates/updates Subscription and resets credits."""
        from app.services.subscription import SubscriptionService

        user_id = uuid4()
        db = _mock_db_session()

        # Mock Stripe client for subscriptions.retrieve
        mock_client = MagicMock()
        mock_stripe_sub = MagicMock()
        mock_stripe_sub.current_period_start = 1700000000
        mock_stripe_sub.current_period_end = 1702592000
        mock_client.subscriptions.retrieve.return_value = mock_stripe_sub
        mock_get_client.return_value = mock_client

        # Mock DB queries: no existing subscription, user found, credit found
        mock_sub_result = MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        mock_user = MagicMock()
        mock_user.user_class = "free_trial"
        mock_user_result = MagicMock(scalar_one_or_none=MagicMock(return_value=mock_user))
        mock_credit = MagicMock()
        mock_credit.balance = Decimal("0")
        mock_credit.user_id = user_id
        mock_credit.last_reset_at = None
        mock_credit_result = MagicMock(scalar_one_or_none=MagicMock(return_value=mock_credit))

        db.execute = AsyncMock(
            side_effect=[mock_sub_result, mock_user_result, mock_credit_result]
        )

        session_data = {
            "client_reference_id": str(user_id),
            "mode": "subscription",
            "subscription": "sub_123",
            "customer": "cus_123",
            "metadata": {"plan_tier": "standard"},
            "amount_total": 999,
            "currency": "usd",
            "payment_intent": "pi_123",
        }

        with patch("app.services.subscription.CreditService.execute_reset", new_callable=AsyncMock) as mock_reset, \
             patch("app.services.subscription.get_class_config") as mock_class_config:
            mock_class_config.return_value = {"credits": 100, "reset_policy": "monthly"}
            await SubscriptionService.handle_checkout_completed(db, session_data)

            # Verify Subscription was added (new subscription)
            db.add.assert_called()
            # Verify credit reset was called
            mock_reset.assert_called_once_with(
                db, mock_credit, 100, "subscription_activation"
            )
            # Verify user class updated
            assert mock_user.user_class == "standard"

    @pytest.mark.asyncio
    async def test_topup_checkout_adds_purchased_credits(self):
        """Top-up checkout adds to purchased_balance and records PaymentHistory."""
        from app.services.subscription import SubscriptionService

        user_id = uuid4()
        db = _mock_db_session()

        mock_credit = MagicMock()
        mock_credit.purchased_balance = Decimal("10")
        mock_credit.user_id = user_id
        mock_credit_result = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_credit)
        )

        db.execute = AsyncMock(return_value=mock_credit_result)

        session_data = {
            "client_reference_id": str(user_id),
            "mode": "payment",
            "metadata": {
                "user_id": str(user_id),
                "package_id": str(uuid4()),
                "credit_amount": "50",
                "payment_type": "topup",
            },
            "amount_total": 1999,
            "currency": "usd",
            "payment_intent": "pi_topup_123",
        }

        await SubscriptionService.handle_checkout_completed(db, session_data)

        # Verify purchased_balance increased by 50
        assert mock_credit.purchased_balance == Decimal("60")
        # Verify PaymentHistory and CreditTransaction were added
        assert db.add.call_count >= 2  # CreditTransaction + PaymentHistory


# ---------------------------------------------------------------------------
# TestInvoicePaidHandler (STRIPE-07)
# ---------------------------------------------------------------------------

class TestInvoicePaidHandler:
    """STRIPE-07: invoice.paid handler."""

    @pytest.mark.asyncio
    @patch("app.services.subscription.SubscriptionService._get_stripe_client")
    async def test_renewal_resets_subscription_credits(self, mock_get_client):
        """Renewal invoice resets subscription credits to tier allocation."""
        from app.services.subscription import SubscriptionService

        user_id = uuid4()
        db = _mock_db_session()

        # Mock existing subscription
        mock_sub = MagicMock()
        mock_sub.user_id = user_id
        mock_sub.plan_tier = "standard"
        mock_sub.stripe_subscription_id = "sub_renew_123"

        mock_sub_result = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_sub)
        )

        # Mock credit row
        mock_credit = MagicMock()
        mock_credit.balance = Decimal("5")
        mock_credit.user_id = user_id
        mock_credit.last_reset_at = None
        mock_credit_result = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_credit)
        )

        db.execute = AsyncMock(side_effect=[mock_sub_result, mock_credit_result])

        # Mock Stripe client
        mock_client = MagicMock()
        mock_stripe_sub = MagicMock()
        mock_stripe_sub.current_period_start = 1700000000
        mock_stripe_sub.current_period_end = 1702592000
        mock_client.subscriptions.retrieve.return_value = mock_stripe_sub
        mock_get_client.return_value = mock_client

        invoice_data = {
            "subscription": "sub_renew_123",
            "billing_reason": "subscription_cycle",
            "amount_paid": 999,
            "currency": "usd",
            "payment_intent": "pi_renew_123",
        }

        with patch("app.services.subscription.CreditService.execute_reset", new_callable=AsyncMock) as mock_reset, \
             patch("app.services.subscription.get_class_config") as mock_class_config:
            mock_class_config.return_value = {"credits": 100, "reset_policy": "monthly"}
            await SubscriptionService.handle_invoice_paid(db, invoice_data)

            mock_reset.assert_called_once_with(
                db, mock_credit, 100, "billing_cycle_reset"
            )

    @pytest.mark.asyncio
    @patch("app.services.subscription.SubscriptionService._get_stripe_client")
    async def test_purchased_credits_untouched_on_renewal(self, mock_get_client):
        """Renewal does not modify purchased_balance."""
        from app.services.subscription import SubscriptionService

        user_id = uuid4()
        db = _mock_db_session()

        mock_sub = MagicMock()
        mock_sub.user_id = user_id
        mock_sub.plan_tier = "standard"
        mock_sub_result = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_sub)
        )

        mock_credit = MagicMock()
        mock_credit.balance = Decimal("5")
        mock_credit.purchased_balance = Decimal("25")
        mock_credit.user_id = user_id
        mock_credit.last_reset_at = None
        mock_credit_result = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_credit)
        )

        db.execute = AsyncMock(side_effect=[mock_sub_result, mock_credit_result])

        mock_client = MagicMock()
        mock_stripe_sub = MagicMock()
        mock_stripe_sub.current_period_start = 1700000000
        mock_stripe_sub.current_period_end = 1702592000
        mock_client.subscriptions.retrieve.return_value = mock_stripe_sub
        mock_get_client.return_value = mock_client

        invoice_data = {
            "subscription": "sub_renew_456",
            "billing_reason": "subscription_cycle",
            "amount_paid": 999,
            "currency": "usd",
            "payment_intent": "pi_renew_456",
        }

        with patch("app.services.subscription.CreditService.execute_reset", new_callable=AsyncMock), \
             patch("app.services.subscription.get_class_config") as mock_class_config:
            mock_class_config.return_value = {"credits": 100, "reset_policy": "monthly"}
            await SubscriptionService.handle_invoice_paid(db, invoice_data)

            # purchased_balance should be unchanged
            assert mock_credit.purchased_balance == Decimal("25")


# ---------------------------------------------------------------------------
# TestInvoicePaymentFailedHandler (STRIPE-08)
# ---------------------------------------------------------------------------

class TestInvoicePaymentFailedHandler:
    """STRIPE-08: invoice.payment_failed handler."""

    @pytest.mark.asyncio
    async def test_marks_subscription_past_due(self):
        """Payment failure marks subscription as past_due."""
        from app.services.subscription import SubscriptionService

        user_id = uuid4()
        db = _mock_db_session()

        mock_sub = MagicMock()
        mock_sub.user_id = user_id
        mock_sub.status = "active"
        mock_sub_result = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_sub)
        )

        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.first_name = "Test"
        mock_user_result = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_user)
        )

        db.execute = AsyncMock(side_effect=[mock_sub_result, mock_user_result])

        invoice_data = {
            "subscription": "sub_fail_123",
            "amount_due": 999,
            "currency": "usd",
            "payment_intent": "pi_fail_123",
        }

        with patch("app.services.subscription.send_payment_failed_email", new_callable=AsyncMock):
            await SubscriptionService.handle_invoice_payment_failed(db, invoice_data)

        assert mock_sub.status == "past_due"

    @pytest.mark.asyncio
    async def test_sends_payment_failed_email(self):
        """Payment failure sends email to user."""
        from app.services.subscription import SubscriptionService

        user_id = uuid4()
        db = _mock_db_session()

        mock_sub = MagicMock()
        mock_sub.user_id = user_id
        mock_sub_result = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_sub)
        )

        mock_user = MagicMock()
        mock_user.email = "jane@example.com"
        mock_user.first_name = "Jane"
        mock_user_result = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_user)
        )

        db.execute = AsyncMock(side_effect=[mock_sub_result, mock_user_result])

        invoice_data = {
            "subscription": "sub_fail_456",
            "amount_due": 999,
            "currency": "usd",
            "payment_intent": "pi_fail_456",
        }

        with patch(
            "app.services.subscription.send_payment_failed_email",
            new_callable=AsyncMock,
        ) as mock_email:
            await SubscriptionService.handle_invoice_payment_failed(db, invoice_data)
            mock_email.assert_called_once()
            call_args = mock_email.call_args
            assert call_args[0][0] == "jane@example.com"
            assert call_args[0][1] == "Jane"


# ---------------------------------------------------------------------------
# TestSubscriptionUpdatedHandler (STRIPE-09)
# ---------------------------------------------------------------------------

class TestSubscriptionUpdatedHandler:
    """STRIPE-09: customer.subscription.updated handler."""

    @pytest.mark.asyncio
    async def test_plan_upgrade_updates_tier(self):
        """Plan tier change updates both Subscription and User.user_class."""
        from app.services.subscription import SubscriptionService

        user_id = uuid4()
        db = _mock_db_session()

        mock_sub = MagicMock()
        mock_sub.user_id = user_id
        mock_sub.plan_tier = "standard"
        mock_sub.status = "active"
        mock_sub.cancel_at_period_end = False
        mock_sub_result = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_sub)
        )

        mock_user = MagicMock()
        mock_user.user_class = "standard"
        mock_user_result = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_user)
        )

        db.execute = AsyncMock(side_effect=[mock_sub_result, mock_user_result])

        sub_data = {
            "id": "sub_upgrade_123",
            "status": "active",
            "cancel_at_period_end": False,
            "metadata": {"plan_tier": "premium"},
            "current_period_start": 1700000000,
            "current_period_end": 1702592000,
        }

        await SubscriptionService.handle_subscription_updated(db, sub_data)

        assert mock_sub.plan_tier == "premium"
        assert mock_user.user_class == "premium"

    @pytest.mark.asyncio
    async def test_cancel_at_period_end_sets_flag(self):
        """cancel_at_period_end=True sets flag on Subscription."""
        from app.services.subscription import SubscriptionService

        user_id = uuid4()
        db = _mock_db_session()

        mock_sub = MagicMock()
        mock_sub.user_id = user_id
        mock_sub.plan_tier = "standard"
        mock_sub.status = "active"
        mock_sub.cancel_at_period_end = False
        mock_sub_result = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_sub)
        )

        db.execute = AsyncMock(return_value=mock_sub_result)

        sub_data = {
            "id": "sub_cancel_123",
            "status": "active",
            "cancel_at_period_end": True,
            "metadata": {"plan_tier": "standard"},
            "current_period_start": 1700000000,
            "current_period_end": 1702592000,
        }

        await SubscriptionService.handle_subscription_updated(db, sub_data)

        assert mock_sub.cancel_at_period_end is True


# ---------------------------------------------------------------------------
# TestSubscriptionDeletedHandler (STRIPE-10)
# ---------------------------------------------------------------------------

class TestSubscriptionDeletedHandler:
    """STRIPE-10: customer.subscription.deleted handler."""

    @pytest.mark.asyncio
    async def test_downgrades_to_on_demand(self):
        """Subscription deletion sets User.user_class to on_demand."""
        from app.services.subscription import SubscriptionService

        user_id = uuid4()
        db = _mock_db_session()

        mock_sub = MagicMock()
        mock_sub.user_id = user_id
        mock_sub.status = "active"
        mock_sub_result = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_sub)
        )

        mock_user = MagicMock()
        mock_user.user_class = "standard"
        mock_user_result = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_user)
        )

        mock_credit = MagicMock()
        mock_credit.balance = Decimal("50")
        mock_credit.purchased_balance = Decimal("10")
        mock_credit.user_id = user_id
        mock_credit_result = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_credit)
        )

        db.execute = AsyncMock(
            side_effect=[mock_sub_result, mock_user_result, mock_credit_result]
        )

        sub_data = {"id": "sub_del_123"}

        await SubscriptionService.handle_subscription_deleted(db, sub_data)

        assert mock_user.user_class == "on_demand"
        assert mock_sub.status == "canceled"

    @pytest.mark.asyncio
    async def test_zeros_subscription_credits(self):
        """Subscription deletion zeros balance but preserves purchased_balance."""
        from app.services.subscription import SubscriptionService

        user_id = uuid4()
        db = _mock_db_session()

        mock_sub = MagicMock()
        mock_sub.user_id = user_id
        mock_sub.status = "active"
        mock_sub_result = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_sub)
        )

        mock_user = MagicMock()
        mock_user.user_class = "premium"
        mock_user_result = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_user)
        )

        mock_credit = MagicMock()
        mock_credit.balance = Decimal("200")
        mock_credit.purchased_balance = Decimal("30")
        mock_credit.user_id = user_id
        mock_credit_result = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_credit)
        )

        db.execute = AsyncMock(
            side_effect=[mock_sub_result, mock_user_result, mock_credit_result]
        )

        sub_data = {"id": "sub_del_456"}

        await SubscriptionService.handle_subscription_deleted(db, sub_data)

        assert mock_credit.balance == Decimal("0")
        assert mock_credit.purchased_balance == Decimal("30")
