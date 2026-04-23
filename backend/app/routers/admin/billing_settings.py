"""Admin billing settings endpoints.

Provides endpoints for reading and updating billing platform settings
(monetization toggle, trial duration, pricing, credit allocations).
"""

import json
import logging

from fastapi import APIRouter, HTTPException

from app.dependencies import CurrentAdmin, DbSession
from app.schemas.admin_billing import (
    BillingSettingsResponse,
    BillingSettingsUpdateRequest,
)
from app.services.platform_settings import (
    get_all as get_platform_settings,
    invalidate_cache,
    upsert,
    validate_setting,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing-settings", tags=["admin-billing-settings"])

# Mapping from BillingSettingsUpdateRequest fields to platform_settings keys
_FIELD_TO_KEY = {
    "monetization_enabled": "monetization_enabled",
    "price_standard_monthly_cents": "price_standard_monthly_cents",
    "price_premium_monthly_cents": "price_premium_monthly_cents",
}


@router.get("", response_model=BillingSettingsResponse)
async def get_billing_settings(
    admin: CurrentAdmin,
    db: DbSession,
):
    """Read all billing-related platform settings."""
    settings = await get_platform_settings(db)

    return BillingSettingsResponse(
        monetization_enabled=json.loads(settings.get("monetization_enabled", "false")),
        price_standard_monthly_cents=json.loads(
            settings.get("price_standard_monthly_cents", "2900")
        ),
        price_premium_monthly_cents=json.loads(
            settings.get("price_premium_monthly_cents", "7900")
        ),
        stripe_price_standard_monthly=json.loads(
            settings.get("stripe_price_standard_monthly", '""')
        ),
        stripe_price_premium_monthly=json.loads(
            settings.get("stripe_price_premium_monthly", '""')
        ),
    )


@router.put("", response_model=BillingSettingsResponse)
async def update_billing_settings(
    body: BillingSettingsUpdateRequest,
    admin: CurrentAdmin,
    db: DbSession,
):
    """Update billing platform settings.

    For price changes (price_standard_monthly_cents, price_premium_monthly_cents):
    if the value changed, creates a new Stripe Price via API, deactivates old price,
    and stores the new price ID.
    """
    updates = body.model_dump(exclude_none=True)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Validate each setting
    for field_name, value in updates.items():
        key = _FIELD_TO_KEY.get(field_name)
        if not key:
            continue
        error = validate_setting(key, value)
        if error:
            raise HTTPException(status_code=422, detail=error)

    # Guard: block monetization_enabled=true if Stripe not fully ready (D-07)
    if updates.get("monetization_enabled") is True:
        from app.services.pricing_sync import check_stripe_readiness
        readiness = await check_stripe_readiness(db)
        if not readiness["ready"]:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "Cannot enable monetization — Stripe is not fully configured",
                    "missing": readiness["missing"],
                },
            )

    # Get current settings for price change detection
    current_settings = await get_platform_settings(db)

    # Handle price changes with Stripe Price creation
    for price_field in ("price_standard_monthly_cents", "price_premium_monthly_cents"):
        if price_field not in updates:
            continue

        new_price_cents = updates[price_field]
        current_price_cents = json.loads(
            current_settings.get(price_field, "0")
        )

        if new_price_cents != current_price_cents and new_price_cents > 0:
            # Determine which tier
            tier = "standard" if "standard" in price_field else "premium"
            stripe_price_key = f"stripe_price_{tier}_monthly"
            old_stripe_price_id = json.loads(
                current_settings.get(stripe_price_key, '""')
            )

            try:
                from app.services.subscription import SubscriptionService

                client = SubscriptionService._get_stripe_client()

                # Create new Stripe Price
                new_price = client.v1.prices.create(
                    params={
                        "unit_amount": new_price_cents,
                        "currency": "usd",
                        "recurring": {"interval": "month"},
                        "product_data": {
                            "name": f"Spectra {tier.title()} Plan",
                        },
                        "lookup_key": f"{tier}_monthly",
                        "transfer_lookup_key": True,
                    }
                )

                # Deactivate old price
                if old_stripe_price_id:
                    try:
                        client.v1.prices.update(
                            old_stripe_price_id, params={"active": False}
                        )
                    except Exception:
                        logger.warning(
                            "Failed to deactivate old Stripe price: %s",
                            old_stripe_price_id,
                        )

                # Store new price ID
                await upsert(db, stripe_price_key, new_price.id, admin.id)
                logger.info(
                    "Created new Stripe price for %s: %s",
                    tier,
                    new_price.id,
                )
            except Exception as e:
                logger.error(
                    "Failed to create Stripe price for %s: %s", tier, str(e)
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to create Stripe price for {tier} plan: {str(e)}",
                )

    # Upsert all non-None fields
    for field_name, value in updates.items():
        key = _FIELD_TO_KEY.get(field_name)
        if key:
            await upsert(db, key, value, admin.id)

    invalidate_cache()
    await db.commit()

    # Return updated settings
    return await get_billing_settings(admin, db)
