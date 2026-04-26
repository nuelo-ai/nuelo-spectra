"""Tests for billing model importability and field existence (DATA-01 through DATA-06)."""


class TestBillingModels:
    """Verify all billing models are importable and have required fields."""

    def test_subscription_model(self):
        """DATA-01: Subscription model importable with required fields."""
        from app.models.subscription import Subscription
        assert hasattr(Subscription, "__tablename__")
        assert Subscription.__tablename__ == "subscriptions"
        cols = {c.name for c in Subscription.__table__.columns}
        assert "user_id" in cols
        assert "stripe_subscription_id" in cols
        assert "stripe_customer_id" in cols
        assert "plan_tier" in cols
        assert "status" in cols
        assert "current_period_start" in cols
        assert "current_period_end" in cols
        assert "cancel_at_period_end" in cols

    def test_payment_history_model(self):
        """DATA-02: PaymentHistory model importable with required fields."""
        from app.models.payment_history import PaymentHistory
        assert PaymentHistory.__tablename__ == "payment_history"
        cols = {c.name for c in PaymentHistory.__table__.columns}
        assert "user_id" in cols
        assert "stripe_payment_intent_id" in cols
        assert "amount_cents" in cols
        assert "payment_type" in cols
        assert "credit_amount" in cols
        assert "status" in cols

    def test_credit_package_model(self):
        """DATA-03: CreditPackage model importable with required fields."""
        from app.models.credit_package import CreditPackage
        assert CreditPackage.__tablename__ == "credit_packages"
        cols = {c.name for c in CreditPackage.__table__.columns}
        assert "name" in cols
        assert "credit_amount" in cols
        assert "price_cents" in cols
        assert "stripe_price_id" in cols
        assert "is_active" in cols

    def test_stripe_event_model(self):
        """DATA-04: StripeEvent model importable with required fields."""
        from app.models.stripe_event import StripeEvent
        assert StripeEvent.__tablename__ == "stripe_events"
        cols = {c.name for c in StripeEvent.__table__.columns}
        assert "stripe_event_id" in cols
        assert "event_type" in cols
        assert "processed_at" in cols

    def test_user_trial_field(self):
        """DATA-05: User model has trial_expires_at field."""
        from app.models.user import User
        cols = {c.name for c in User.__table__.columns}
        assert "trial_expires_at" in cols

    def test_user_credit_purchased_balance(self):
        """DATA-06: UserCredit model has purchased_balance field."""
        from app.models.user_credit import UserCredit
        cols = {c.name for c in UserCredit.__table__.columns}
        assert "purchased_balance" in cols
