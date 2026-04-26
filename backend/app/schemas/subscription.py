"""Pydantic schemas for subscription and checkout operations."""
from pydantic import BaseModel
from uuid import UUID


class SubscriptionCheckoutRequest(BaseModel):
    """Request body for creating a subscription checkout session."""
    plan_tier: str  # "standard" or "premium"


class TopupCheckoutRequest(BaseModel):
    """Request body for creating a credit top-up checkout session."""
    package_id: UUID


class CheckoutResponse(BaseModel):
    """Response containing the Stripe Checkout Session URL."""
    checkout_url: str


class SubscriptionStatusResponse(BaseModel):
    """Response showing current subscription state."""
    has_subscription: bool
    plan_tier: str | None = None
    status: str | None = None
    cancel_at_period_end: bool = False
    current_period_end: str | None = None


class PlanInfo(BaseModel):
    """Single plan tier info for pricing display."""
    tier_key: str           # "on_demand", "standard", "premium"
    display_name: str       # "On Demand", "Basic", "Premium"
    price_cents: int        # 0 for on_demand, e.g. 2900 for standard
    price_display: str      # "Pay as you go" or "$29.00/month"
    credit_allocation: int  # 0 for on_demand, 100 for standard, 500 for premium
    features: list[str]
    is_popular: bool        # True only for standard/Basic


class PlanPricingResponse(BaseModel):
    """Response for GET /subscriptions/plans."""
    plans: list[PlanInfo]
    current_tier: str       # user's current user_class


class PlanChangeRequest(BaseModel):
    """Request body for POST /subscriptions/change."""
    plan_tier: str          # "standard" or "premium"


class PlanChangeResponse(BaseModel):
    """Response for POST /subscriptions/change."""
    change_type: str        # "upgrade" or "downgrade"
    new_plan: str           # display name
    effective_at: str       # "immediately" or ISO date string


class PlanChangePreviewResponse(BaseModel):
    """Response for GET /subscriptions/preview-change."""
    proration_amount_cents: int   # Amount to charge now (prorated)
    proration_display: str        # "$19.35"
    new_plan_display: str         # "Premium"
    new_credit_allocation: int    # 500
    change_type: str              # "upgrade" or "downgrade"
    effective_at: str             # "immediately" or ISO date


class CancelResponse(BaseModel):
    """Response for POST /subscriptions/cancel."""
    cancel_at: str          # ISO date when subscription ends


class BillingHistoryItem(BaseModel):
    """Single billing history entry."""
    id: str
    date: str               # ISO date string
    payment_type: str       # "subscription", "topup", "refund"
    type_display: str       # "Subscription", "Credit Top-up", "Refund"
    amount_cents: int
    amount_display: str     # "$29.00"
    credit_amount: float | None
    status: str             # "succeeded", "failed", "refunded"


class BillingHistoryResponse(BaseModel):
    """Response for GET /subscriptions/billing-history."""
    items: list[BillingHistoryItem]


class CreditPackageResponse(BaseModel):
    """Single credit package for display."""
    id: str
    name: str
    credit_amount: int
    price_cents: int
    price_display: str      # "$4.99"
