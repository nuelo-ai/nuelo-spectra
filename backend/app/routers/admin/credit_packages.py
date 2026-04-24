"""Admin credit package management endpoints.

Provides endpoints for viewing, editing, and resetting credit packages
with password verification for all mutations (D-09).
"""

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.dependencies import CurrentAdmin, DbSession
from app.models.credit_package import CreditPackage
from app.schemas.admin_billing import (
    AdminCreditPackageConfigDefaults,
    AdminCreditPackageResponse,
    CreditPackageResetRequest,
    CreditPackageUpdateRequest,
)
from app.services.platform_settings import invalidate_cache
from app.services.pricing_sync import reset_credit_packages
from app.services.user_class import get_credit_packages as get_config_packages
from app.utils.security import verify_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/credit-packages", tags=["admin-credit-packages"])


@router.get("", response_model=list[AdminCreditPackageResponse])
async def get_admin_credit_packages(
    admin: CurrentAdmin,
    db: DbSession,
):
    """Return all credit packages with config defaults for admin display."""
    result = await db.execute(
        select(CreditPackage).order_by(CreditPackage.display_order.asc())
    )
    packages = result.scalars().all()
    config_packages = get_config_packages()
    config_by_name = {p["name"]: p for p in config_packages}

    return [
        AdminCreditPackageResponse(
            id=str(pkg.id),
            name=pkg.name,
            price_cents=pkg.price_cents,
            credit_amount=pkg.credit_amount,
            display_order=pkg.display_order,
            is_active=pkg.is_active,
            stripe_price_id=pkg.stripe_price_id or "",
            config_defaults=(
                AdminCreditPackageConfigDefaults(**config_by_name[pkg.name])
                if pkg.name in config_by_name
                else None
            ),
        )
        for pkg in packages
    ]


@router.put("/{package_id}", response_model=AdminCreditPackageResponse)
async def update_credit_package(
    package_id: UUID,
    body: CreditPackageUpdateRequest,
    admin: CurrentAdmin,
    db: DbSession,
):
    """Update a credit package. Creates new Stripe Price if price_cents changes."""
    # Verify admin password -- use 403 (not 401) per established pattern
    if not verify_password(body.password, admin.hashed_password):
        raise HTTPException(status_code=403, detail="Incorrect password")

    result = await db.execute(
        select(CreditPackage).where(CreditPackage.id == package_id)
    )
    pkg = result.scalar_one_or_none()
    if not pkg:
        raise HTTPException(status_code=404, detail="Credit package not found")

    price_changed = body.price_cents != pkg.price_cents

    # Update fields
    pkg.name = body.name
    pkg.credit_amount = body.credit_amount
    pkg.display_order = body.display_order
    pkg.is_active = body.is_active

    # Handle price change with Stripe Price recreation
    if price_changed and body.price_cents > 0:
        old_stripe_price_id = pkg.stripe_price_id
        pkg.price_cents = body.price_cents

        from app.config import get_settings

        settings = get_settings()

        if settings.spectra_mode in ("dev", "public") and settings.stripe_secret_key:
            try:
                from app.services.subscription import SubscriptionService

                client = SubscriptionService._get_stripe_client()

                # Create new Stripe Price
                product = client.v1.products.create(
                    params={
                        "name": f"Spectra {pkg.name}",
                        "metadata": {
                            "type": "credit_package",
                            "credit_amount": str(pkg.credit_amount),
                        },
                    }
                )
                price = client.v1.prices.create(
                    params={
                        "product": product.id,
                        "unit_amount": body.price_cents,
                        "currency": "usd",
                    }
                )
                pkg.stripe_price_id = price.id

                # Deactivate old Stripe Price
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

                logger.info(
                    "Created new Stripe price for package '%s': %s",
                    pkg.name,
                    price.id,
                )
            except Exception as e:
                logger.error(
                    "Failed to create Stripe price for package '%s': %s",
                    pkg.name,
                    str(e),
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to create Stripe price: {str(e)}",
                )
        else:
            # No Stripe in this mode -- clear stripe_price_id so it's re-synced later
            pkg.stripe_price_id = None
    elif price_changed:
        pkg.price_cents = body.price_cents

    await db.commit()
    invalidate_cache()

    # Return updated package with config defaults
    config_packages = get_config_packages()
    config_by_name = {p["name"]: p for p in config_packages}
    return AdminCreditPackageResponse(
        id=str(pkg.id),
        name=pkg.name,
        price_cents=pkg.price_cents,
        credit_amount=pkg.credit_amount,
        display_order=pkg.display_order,
        is_active=pkg.is_active,
        stripe_price_id=pkg.stripe_price_id or "",
        config_defaults=(
            AdminCreditPackageConfigDefaults(**config_by_name[pkg.name])
            if pkg.name in config_by_name
            else None
        ),
    )


@router.post("/reset", response_model=list[AdminCreditPackageResponse])
async def reset_admin_credit_packages(
    body: CreditPackageResetRequest,
    admin: CurrentAdmin,
    db: DbSession,
):
    """Reset all credit packages to config-file defaults."""
    # Verify admin password -- use 403 (not 401) per established pattern
    if not verify_password(body.password, admin.hashed_password):
        raise HTTPException(status_code=403, detail="Incorrect password")

    await reset_credit_packages(db)
    await db.commit()
    invalidate_cache()

    return await get_admin_credit_packages(admin, db)
