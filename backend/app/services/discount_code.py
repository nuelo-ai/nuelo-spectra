"""Discount code service with Stripe Coupon + Promotion Code sync.

Handles CRUD operations for discount codes and synchronizes them with
Stripe Coupons and Promotion Codes.
"""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discount_code import DiscountCode
from app.services.subscription import SubscriptionService

logger = logging.getLogger(__name__)


class DiscountCodeService:
    """Handles discount code CRUD with Stripe Coupon/Promotion Code sync."""

    @staticmethod
    async def create(
        db: AsyncSession,
        code: str,
        discount_type: str,
        discount_value: int,
        max_redemptions: int | None,
        expires_at,
        admin_id: UUID,
    ) -> DiscountCode:
        """Create a discount code with Stripe Coupon + Promotion Code.

        Per D-21: BOTH Stripe Coupon and Promotion Code must be created.
        Per D-16: Only percent_off and amount_off types supported.

        Args:
            db: Database session (caller manages transaction).
            code: Discount code string (auto-uppercased).
            discount_type: "percent_off" or "amount_off".
            discount_value: Percent (1-100) or cents (> 0).
            max_redemptions: Optional usage limit.
            expires_at: Optional expiration datetime.
            admin_id: UUID of the admin creating the code.

        Returns:
            Created DiscountCode row.
        """
        code = code.upper()

        client = SubscriptionService._get_stripe_client()

        # Build Stripe Coupon params
        coupon_params: dict = {
            "metadata": {"source": "spectra_admin", "code": code},
        }
        if discount_type == "percent_off":
            coupon_params["percent_off"] = discount_value
            coupon_params["duration"] = "forever"
        else:
            coupon_params["amount_off"] = discount_value
            coupon_params["currency"] = "usd"
            coupon_params["duration"] = "once"

        if max_redemptions is not None:
            coupon_params["max_redemptions"] = max_redemptions
        if expires_at is not None:
            coupon_params["redeem_by"] = int(expires_at.timestamp())

        coupon = client.v1.coupons.create(params=coupon_params)

        # Build Stripe Promotion Code params
        # SDK v14: coupon is nested inside promotion object
        promo_params: dict = {
            "promotion": {
                "type": "coupon",
                "coupon": coupon.id,
            },
            "code": code,
            "active": True,
        }
        if max_redemptions is not None:
            promo_params["max_redemptions"] = max_redemptions
        if expires_at is not None:
            promo_params["expires_at"] = int(expires_at.timestamp())

        promo = client.v1.promotion_codes.create(params=promo_params)

        # Save to DB
        discount_code = DiscountCode(
            code=code,
            discount_type=discount_type,
            discount_value=discount_value,
            stripe_coupon_id=coupon.id,
            stripe_promotion_code_id=promo.id,
            max_redemptions=max_redemptions,
            expires_at=expires_at,
            created_by=admin_id,
        )
        db.add(discount_code)
        await db.flush()

        logger.info(
            "Created discount code",
            extra={
                "code": code,
                "discount_type": discount_type,
                "stripe_coupon_id": coupon.id,
                "stripe_promo_id": promo.id,
            },
        )
        return discount_code

    @staticmethod
    async def list_all(db: AsyncSession) -> tuple[list[DiscountCode], int]:
        """List all discount codes ordered by created_at desc.

        Returns:
            Tuple of (list of DiscountCode rows, total count).
        """
        result = await db.execute(
            select(DiscountCode).order_by(DiscountCode.created_at.desc())
        )
        codes = list(result.scalars().all())
        return codes, len(codes)

    @staticmethod
    async def update(
        db: AsyncSession,
        discount_code_id: UUID,
        max_redemptions: int | None,
        expires_at=None,
    ) -> DiscountCode:
        """Update local discount code fields.

        Note: Stripe coupons are largely immutable for amounts.
        Stripe promotion codes cannot update expires_at after creation.

        Args:
            db: Database session.
            discount_code_id: UUID of the discount code.
            max_redemptions: New max redemptions value.
            expires_at: New expiration datetime.

        Returns:
            Updated DiscountCode row.

        Raises:
            ValueError: If discount code not found.
        """
        result = await db.execute(
            select(DiscountCode).where(DiscountCode.id == discount_code_id)
        )
        discount_code = result.scalar_one_or_none()
        if not discount_code:
            raise ValueError("Discount code not found")

        if max_redemptions is not None:
            discount_code.max_redemptions = max_redemptions
        if expires_at is not None:
            if discount_code.stripe_promotion_code_id:
                logger.warning(
                    "Stripe promotion codes cannot update expires_at after creation. "
                    "Updated locally only.",
                    extra={"discount_code_id": str(discount_code_id)},
                )
            discount_code.expires_at = expires_at

        await db.flush()
        return discount_code

    @staticmethod
    async def deactivate(db: AsyncSession, discount_code_id: UUID) -> DiscountCode:
        """Deactivate a discount code locally and in Stripe.

        Per D-18: Set is_active=False locally.
        Per ADMIN-09: Deactivate Stripe Promotion Code.

        Args:
            db: Database session.
            discount_code_id: UUID of the discount code.

        Returns:
            Deactivated DiscountCode row.

        Raises:
            ValueError: If discount code not found.
        """
        result = await db.execute(
            select(DiscountCode).where(DiscountCode.id == discount_code_id)
        )
        discount_code = result.scalar_one_or_none()
        if not discount_code:
            raise ValueError("Discount code not found")

        discount_code.is_active = False

        if discount_code.stripe_promotion_code_id:
            client = SubscriptionService._get_stripe_client()
            client.v1.promotion_codes.update(
                discount_code.stripe_promotion_code_id,
                params={"active": False},
            )

        await db.flush()

        logger.info(
            "Deactivated discount code",
            extra={
                "code": discount_code.code,
                "stripe_promo_id": discount_code.stripe_promotion_code_id,
            },
        )
        return discount_code

    @staticmethod
    async def delete(db: AsyncSession, discount_code_id: UUID) -> None:
        """Delete a discount code from DB and Stripe.

        Deactivates Stripe Promotion Code first, then deletes Stripe Coupon,
        then removes the local DB row.

        Args:
            db: Database session.
            discount_code_id: UUID of the discount code.

        Raises:
            ValueError: If discount code not found.
        """
        result = await db.execute(
            select(DiscountCode).where(DiscountCode.id == discount_code_id)
        )
        discount_code = result.scalar_one_or_none()
        if not discount_code:
            raise ValueError("Discount code not found")

        client = SubscriptionService._get_stripe_client()

        # Deactivate Stripe Promotion Code
        if discount_code.stripe_promotion_code_id:
            client.v1.promotion_codes.update(
                discount_code.stripe_promotion_code_id,
                params={"active": False},
            )

        # Delete Stripe Coupon
        if discount_code.stripe_coupon_id:
            client.v1.coupons.delete(discount_code.stripe_coupon_id)

        # Delete local row
        await db.delete(discount_code)
        await db.flush()

        logger.info(
            "Deleted discount code",
            extra={
                "code": discount_code.code,
                "stripe_coupon_id": discount_code.stripe_coupon_id,
            },
        )
