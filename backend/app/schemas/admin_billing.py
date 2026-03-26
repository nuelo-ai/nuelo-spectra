"""Request/response schemas for admin billing endpoints."""

from pydantic import BaseModel, Field
from datetime import datetime


# --- User Billing Detail ---


class SubscriptionStatusResponse(BaseModel):
    has_subscription: bool
    plan_tier: str | None = None
    status: str | None = None
    stripe_customer_id: str | None = None
    stripe_subscription_id: str | None = None
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    cancel_at_period_end: bool = False


class PaymentHistoryItem(BaseModel):
    id: str
    created_at: datetime
    payment_type: str
    amount_cents: int
    currency: str
    credit_amount: float | None = None
    status: str
    stripe_payment_intent_id: str | None = None


class StripeEventItem(BaseModel):
    id: str
    stripe_event_id: str
    event_type: str
    processed_at: datetime


class UserBillingDetailResponse(BaseModel):
    subscription: SubscriptionStatusResponse
    payments: list[PaymentHistoryItem]
    stripe_events: list[StripeEventItem]


# --- Force Set Tier ---


class ForceSetTierRequest(BaseModel):
    new_tier: str = Field(..., pattern="^(free_trial|on_demand|standard|premium)$")
    reason: str = Field(..., min_length=1, max_length=500)


class ForceSetTierResponse(BaseModel):
    previous_tier: str
    new_tier: str
    stripe_synced: bool
    stripe_action: str | None = None  # "subscription_cancelled", "subscription_created", etc.


# --- Admin Cancel ---


class AdminCancelResponse(BaseModel):
    cancel_at: str | None = None


# --- Refund ---


class RefundRequest(BaseModel):
    payment_id: str
    amount_cents: int | None = None  # None = full refund


class RefundResponse(BaseModel):
    refund_amount_cents: int
    credits_deducted: float
    stripe_refund_id: str


# --- Billing Settings ---


class BillingSettingsResponse(BaseModel):
    monetization_enabled: bool
    price_standard_monthly_cents: int
    price_premium_monthly_cents: int
    stripe_price_standard_monthly: str
    stripe_price_premium_monthly: str


class BillingSettingsUpdateRequest(BaseModel):
    monetization_enabled: bool | None = None
    price_standard_monthly_cents: int | None = Field(None, ge=0)
    price_premium_monthly_cents: int | None = Field(None, ge=0)
