"""Pydantic schemas for admin dashboard metrics and admin profile."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TrendPoint(BaseModel):
    """Single data point in a time-series trend."""

    date: str
    count: int


class CreditDistributionEntry(BaseModel):
    """Credit distribution grouped by user tier."""

    tier: str
    user_count: int
    total_credits: float


class LowCreditUser(BaseModel):
    """User with low credit balance."""

    user_id: str
    email: str
    name: str
    balance: float
    tier: str


class CreditSummary(BaseModel):
    """Aggregated credit totals."""

    total_used: float
    total_remaining: float


class DashboardMetricsResponse(BaseModel):
    """Full dashboard metrics response covering DASH-01 through DASH-07."""

    # DASH-01: User counts
    total_users: int
    active_users: int
    inactive_users: int
    active_today: int

    # DASH-02: Signup counts
    signups_today: int
    signups_this_week: int
    signups_this_month: int

    # DASH-03, DASH-04, DASH-05: Platform totals
    total_sessions: int
    total_files: int
    total_messages: int

    # DASH-06: Credit summary
    credit_summary: CreditSummary

    # DASH-07: Time-series trends
    signup_trend: list[TrendPoint]
    message_trend: list[TrendPoint]

    # Additional credit analytics
    credit_distribution: list[CreditDistributionEntry]
    low_credit_users: list[LowCreditUser]


class AdminMeResponse(BaseModel):
    """Admin user profile response."""

    id: UUID
    email: str
    first_name: str | None
    last_name: str | None
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}
