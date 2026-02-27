"""Pydantic schemas for credit operations."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class CreditBalanceResponse(BaseModel):
    """Response schema for credit balance queries."""

    balance: Decimal
    tier_allocation: int
    reset_policy: str
    next_reset_at: datetime | None
    is_low: bool
    is_unlimited: bool
    display_class: str

    model_config = {"from_attributes": True}


class CreditDeductionResult(BaseModel):
    """Result of a credit deduction attempt."""

    success: bool
    balance: Decimal
    error_message: str | None = None
    next_reset: datetime | None = None


class CreditTransactionResponse(BaseModel):
    """Response schema for a credit transaction record."""

    id: UUID
    user_id: UUID
    amount: Decimal
    balance_after: Decimal
    transaction_type: str
    reason: str | None
    admin_id: UUID | None
    api_key_id: UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CreditAdjustmentRequest(BaseModel):
    """Request schema for admin credit adjustment."""

    amount: Decimal = Field(description="Positive to add, negative to deduct")
    reason: str = Field(min_length=1, max_length=500)
    password: str = Field(min_length=1)


class CreditManualResetRequest(BaseModel):
    """Request schema for admin manual credit reset."""

    password: str = Field(min_length=1)
