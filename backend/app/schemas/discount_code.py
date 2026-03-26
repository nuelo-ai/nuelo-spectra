"""Discount code request/response schemas for admin CRUD endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class CreateDiscountCodeRequest(BaseModel):
    """Request schema for creating a discount code."""

    code: str = Field(..., min_length=1, max_length=50, pattern="^[A-Z0-9_-]+$")
    discount_type: str = Field(..., pattern="^(percent_off|amount_off)$")
    discount_value: int = Field(..., gt=0)
    max_redemptions: int | None = Field(None, ge=1)
    expires_at: datetime | None = None


class UpdateDiscountCodeRequest(BaseModel):
    """Request schema for updating a discount code."""

    max_redemptions: int | None = Field(None, ge=1)
    expires_at: datetime | None = None


class DiscountCodeResponse(BaseModel):
    """Response schema for a single discount code."""

    id: str
    code: str
    discount_type: str
    discount_value: int
    currency: str
    stripe_coupon_id: str | None
    stripe_promotion_code_id: str | None
    max_redemptions: int | None
    times_redeemed: int
    expires_at: datetime | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class DiscountCodeListResponse(BaseModel):
    """Response schema for listing discount codes."""

    items: list[DiscountCodeResponse]
    total: int
