"""Tests for SubscriptionService (STRIPE-01, STRIPE-02, STRIPE-03)."""
import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import stripe

from app.config import Settings
from app.exceptions.stripe import CheckoutValidationError, StripeConfigError
from app.services.subscription import SubscriptionService


class TestStripeConfig:
    """STRIPE-01: Stripe SDK initialization and settings."""

    def test_stripe_settings_fields_exist(self):
        """Verify Settings model includes Stripe fields."""
        assert "stripe_secret_key" in Settings.model_fields
        assert "stripe_webhook_secret" in Settings.model_fields

    @patch("app.services.subscription.get_settings")
    def test_stripe_client_creation(self, mock_get_settings):
        """StripeClient is created when key is present."""
        mock_settings = MagicMock()
        mock_settings.stripe_secret_key = "sk_test_123"
        mock_get_settings.return_value = mock_settings

        client = SubscriptionService._get_stripe_client()
        assert isinstance(client, stripe.StripeClient)

    @patch("app.services.subscription.get_settings")
    def test_stripe_client_missing_key_raises(self, mock_get_settings):
        """StripeConfigError raised when key is empty."""
        mock_settings = MagicMock()
        mock_settings.stripe_secret_key = ""
        mock_get_settings.return_value = mock_settings

        with pytest.raises(StripeConfigError):
            SubscriptionService._get_stripe_client()


class TestSubscriptionCheckout:
    """STRIPE-02: Subscription checkout session creation."""

    @pytest.mark.asyncio
    @patch("app.services.subscription.SubscriptionService._get_stripe_client")
    @patch("app.services.subscription.get_platform_settings")
    @patch("app.services.subscription.SubscriptionService.get_or_create_customer")
    async def test_create_subscription_checkout_standard(
        self, mock_get_customer, mock_platform_settings, mock_get_client
    ):
        """Standard plan checkout creates session with correct price."""
        db = AsyncMock()
        # No existing subscription
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        mock_get_customer.return_value = "cus_test123"
        mock_platform_settings.return_value = {
            "stripe_price_standard_monthly": json.dumps("price_std_123"),
            "stripe_price_premium_monthly": json.dumps("price_prem_456"),
        }

        mock_session = MagicMock()
        mock_session.id = "cs_test_abc"
        mock_session.url = "https://checkout.stripe.com/test"
        mock_client = MagicMock()
        mock_client.checkout.sessions.create.return_value = mock_session
        mock_get_client.return_value = mock_client

        user_id = uuid4()
        url = await SubscriptionService.create_subscription_checkout(
            db=db,
            user_id=user_id,
            email="test@test.com",
            name="Test User",
            plan_tier="standard",
            success_url="http://ok",
            cancel_url="http://cancel",
        )

        assert url == "https://checkout.stripe.com/test"
        call_kwargs = mock_client.checkout.sessions.create.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params")
        assert params["mode"] == "subscription"
        assert params["line_items"][0]["price"] == "price_std_123"

    @pytest.mark.asyncio
    @patch("app.services.subscription.SubscriptionService._get_stripe_client")
    @patch("app.services.subscription.get_platform_settings")
    @patch("app.services.subscription.SubscriptionService.get_or_create_customer")
    async def test_create_subscription_checkout_premium(
        self, mock_get_customer, mock_platform_settings, mock_get_client
    ):
        """Premium plan checkout creates session with correct price."""
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        mock_get_customer.return_value = "cus_test123"
        mock_platform_settings.return_value = {
            "stripe_price_standard_monthly": json.dumps("price_std_123"),
            "stripe_price_premium_monthly": json.dumps("price_prem_456"),
        }

        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/premium"
        mock_client = MagicMock()
        mock_client.checkout.sessions.create.return_value = mock_session
        mock_get_client.return_value = mock_client

        url = await SubscriptionService.create_subscription_checkout(
            db=db,
            user_id=uuid4(),
            email="test@test.com",
            name="Test",
            plan_tier="premium",
            success_url="http://ok",
            cancel_url="http://cancel",
        )

        assert url == "https://checkout.stripe.com/premium"
        call_kwargs = mock_client.checkout.sessions.create.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params")
        assert params["line_items"][0]["price"] == "price_prem_456"

    @pytest.mark.asyncio
    async def test_already_subscribed_rejected(self):
        """User with active subscription on same tier is rejected."""
        db = AsyncMock()
        existing_sub = MagicMock()
        existing_sub.plan_tier = "standard"
        existing_sub.status = "active"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_sub
        db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(CheckoutValidationError) as exc_info:
            await SubscriptionService.create_subscription_checkout(
                db=db,
                user_id=uuid4(),
                email="test@test.com",
                name="Test",
                plan_tier="standard",
                success_url="http://ok",
                cancel_url="http://cancel",
            )
        assert exc_info.value.code == "already_subscribed"

    @pytest.mark.asyncio
    async def test_invalid_plan_tier_rejected(self):
        """Invalid plan tier raises CheckoutValidationError."""
        db = AsyncMock()

        with pytest.raises(CheckoutValidationError) as exc_info:
            await SubscriptionService.create_subscription_checkout(
                db=db,
                user_id=uuid4(),
                email="test@test.com",
                name="Test",
                plan_tier="gold",
                success_url="http://ok",
                cancel_url="http://cancel",
            )
        assert exc_info.value.code == "invalid_plan_tier"


class TestTopupCheckout:
    """STRIPE-03: Top-up checkout session creation."""

    @pytest.mark.asyncio
    @patch("app.services.subscription.SubscriptionService._get_stripe_client")
    @patch("app.services.subscription.SubscriptionService.get_or_create_customer")
    async def test_create_topup_checkout(self, mock_get_customer, mock_get_client):
        """Top-up checkout creates payment session with correct metadata."""
        db = AsyncMock()
        package = MagicMock()
        package.id = uuid4()
        package.stripe_price_id = "price_topup_123"
        package.is_active = True
        package.credit_amount = 50
        package.name = "50 Credits"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = package
        db.execute = AsyncMock(return_value=mock_result)

        mock_get_customer.return_value = "cus_test456"

        mock_session = MagicMock()
        mock_session.id = "cs_test_topup"
        mock_session.url = "https://checkout.stripe.com/topup"
        mock_client = MagicMock()
        mock_client.checkout.sessions.create.return_value = mock_session
        mock_get_client.return_value = mock_client

        user_id = uuid4()
        url = await SubscriptionService.create_topup_checkout(
            db=db,
            user_id=user_id,
            email="test@test.com",
            name="Test",
            user_class="standard",
            package_id=package.id,
            success_url="http://ok",
            cancel_url="http://cancel",
        )

        assert url == "https://checkout.stripe.com/topup"
        call_kwargs = mock_client.checkout.sessions.create.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params")
        assert params["mode"] == "payment"
        assert params["metadata"]["payment_type"] == "topup"

    @pytest.mark.asyncio
    async def test_trial_user_topup_rejected(self):
        """Trial users cannot purchase top-ups."""
        db = AsyncMock()

        with pytest.raises(CheckoutValidationError) as exc_info:
            await SubscriptionService.create_topup_checkout(
                db=db,
                user_id=uuid4(),
                email="test@test.com",
                name="Test",
                user_class="free_trial",
                package_id=uuid4(),
                success_url="http://ok",
                cancel_url="http://cancel",
            )
        assert exc_info.value.code == "trial_topup_blocked"

    @pytest.mark.asyncio
    async def test_inactive_package_rejected(self):
        """Inactive package raises CheckoutValidationError."""
        db = AsyncMock()
        package = MagicMock()
        package.is_active = False
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = package
        db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(CheckoutValidationError) as exc_info:
            await SubscriptionService.create_topup_checkout(
                db=db,
                user_id=uuid4(),
                email="test@test.com",
                name="Test",
                user_class="standard",
                package_id=uuid4(),
                success_url="http://ok",
                cancel_url="http://cancel",
            )
        assert exc_info.value.code == "invalid_package"
