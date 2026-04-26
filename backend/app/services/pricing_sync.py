"""Pricing sync service: config seeding, Stripe provisioning, readiness checks.

Reads pricing config from user_classes.yaml and ensures the database
and Stripe are in sync on every startup.
"""

import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.credit_package import CreditPackage
from app.models.platform_setting import PlatformSetting
from app.services.platform_settings import upsert, invalidate_cache as invalidate_platform_cache
from app.services.user_class import get_user_classes, get_credit_packages

logger = logging.getLogger("spectra.pricing")


async def seed_pricing_from_config(db: AsyncSession) -> None:
    """Seed pricing defaults from config and sync Stripe Products/Prices.

    Called on every startup. Idempotent: fills gaps only, never overwrites.
    DB failures are fail-fast (propagate). Stripe failures are graceful (log + continue).
    """
    tiers = get_user_classes()
    packages = get_credit_packages()

    # Step 1: Seed subscription pricing to platform_settings (all modes)
    await _seed_subscription_pricing(db, tiers)

    # Step 2: Seed credit packages to credit_packages table (all modes)
    await _seed_credit_packages(db, packages)

    await db.flush()  # Ensure all DB writes are visible
    invalidate_platform_cache()

    # Step 3: Sync Stripe Products/Prices (dev/public only, per D-09)
    settings = get_settings()
    if settings.spectra_mode in ("dev", "public") and settings.stripe_secret_key:
        await _sync_stripe_prices(db, tiers)
        await _sync_stripe_packages(db)
        await db.flush()
        invalidate_platform_cache()
    else:
        logger.info("Stripe sync skipped (mode=%s)", settings.spectra_mode)


async def check_stripe_readiness(db: AsyncSession) -> dict:
    """Check whether all Stripe Price IDs are configured for monetization.

    Validates that all subscription tiers with has_plan=true have non-empty
    stripe_price_id in platform_settings, all active credit packages have
    non-empty stripe_price_id, and STRIPE_SECRET_KEY is configured.

    Returns:
        dict with 'ready' (bool) and 'missing' (list of description strings).
    """
    missing = []
    settings = get_settings()

    if not settings.stripe_secret_key:
        missing.append("STRIPE_SECRET_KEY not configured")

    # Check subscription tiers
    tiers = get_user_classes()
    for tier_name, tier_config in tiers.items():
        if not tier_config.get("has_plan"):
            continue
        stripe_key = f"stripe_price_{tier_name}_monthly"
        result = await db.execute(
            select(PlatformSetting).where(PlatformSetting.key == stripe_key)
        )
        row = result.scalar_one_or_none()
        stripe_id = json.loads(row.value) if row else ""
        if not stripe_id:
            missing.append(f"Missing Stripe Price for {tier_name} subscription")

    # Check credit packages
    result = await db.execute(
        select(CreditPackage).where(CreditPackage.is_active == True)  # noqa: E712
    )
    packages = result.scalars().all()
    for pkg in packages:
        if not pkg.stripe_price_id:
            missing.append(f"Missing Stripe Price for credit package '{pkg.name}'")

    return {"ready": len(missing) == 0, "missing": missing}


async def reset_subscription_pricing(db: AsyncSession) -> None:
    """Reset subscription pricing in DB to match config values.

    Overwrites existing DB values with config defaults. Deactivates old
    Stripe Prices and creates new ones (in dev/public mode).
    """
    tiers = get_user_classes()
    settings = get_settings()

    for tier_name, tier_config in tiers.items():
        if not tier_config.get("has_plan"):
            continue

        price_key = f"price_{tier_name}_monthly_cents"
        stripe_key = f"stripe_price_{tier_name}_monthly"

        # Get old stripe price ID before overwriting
        result = await db.execute(
            select(PlatformSetting).where(PlatformSetting.key == stripe_key)
        )
        row = result.scalar_one_or_none()
        old_stripe_id = json.loads(row.value) if row and row.value else ""

        # Overwrite DB with config values
        await upsert(db, price_key, tier_config["price_cents"], admin_id=None)

        # Create new Stripe Price if possible
        if settings.spectra_mode in ("dev", "public") and settings.stripe_secret_key:
            try:
                from app.services.subscription import SubscriptionService

                client = SubscriptionService._get_stripe_client()
                # Deactivate old price
                if old_stripe_id:
                    try:
                        client.v1.prices.update(old_stripe_id, params={"active": False})
                    except Exception:
                        logger.warning("Failed to deactivate old Stripe price: %s", old_stripe_id)

                # Create new price
                product = client.v1.products.create(params={
                    "name": f"Spectra {tier_name.title()} Plan",
                    "metadata": {"tier": tier_name, "type": "subscription"},
                })
                price = client.v1.prices.create(params={
                    "product": product.id,
                    "unit_amount": tier_config["price_cents"],
                    "currency": "usd",
                    "recurring": {"interval": "month"},
                    "lookup_key": f"{tier_name}_monthly",
                    "transfer_lookup_key": True,
                })
                await upsert(db, stripe_key, price.id, admin_id=None)
            except Exception as e:
                logger.warning("Stripe reset failed for %s: %s", tier_name, str(e))
                await upsert(db, stripe_key, "", admin_id=None)
        else:
            await upsert(db, stripe_key, "", admin_id=None)

    invalidate_platform_cache()


async def reset_credit_packages(db: AsyncSession) -> None:
    """Reset credit packages in DB to match config values.

    Overwrites existing DB rows to match config. Packages not in config are
    deactivated (is_active=False), never deleted. Creates new Stripe Prices
    for packages missing them (in dev/public mode).
    """
    config_packages = get_credit_packages()
    config_names = {p["name"] for p in config_packages}
    settings = get_settings()

    # Deactivate packages not in config
    result = await db.execute(select(CreditPackage))
    all_packages = result.scalars().all()
    for pkg in all_packages:
        if pkg.name not in config_names:
            pkg.is_active = False
            logger.info("Deactivated non-config package: %s", pkg.name)

    # Upsert config packages
    for pkg_config in config_packages:
        result = await db.execute(
            select(CreditPackage).where(CreditPackage.name == pkg_config["name"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            old_stripe_id = existing.stripe_price_id
            existing.price_cents = pkg_config["price_cents"]
            existing.credit_amount = pkg_config["credit_amount"]
            existing.display_order = pkg_config["display_order"]
            existing.is_active = True
            existing.stripe_price_id = None  # Will be re-created

            # Deactivate old Stripe Price
            if old_stripe_id and settings.spectra_mode in ("dev", "public") and settings.stripe_secret_key:
                try:
                    from app.services.subscription import SubscriptionService

                    client = SubscriptionService._get_stripe_client()
                    client.v1.prices.update(old_stripe_id, params={"active": False})
                except Exception:
                    logger.warning("Failed to deactivate old Stripe price: %s", old_stripe_id)
        else:
            new_pkg = CreditPackage(
                name=pkg_config["name"],
                price_cents=pkg_config["price_cents"],
                credit_amount=pkg_config["credit_amount"],
                display_order=pkg_config["display_order"],
            )
            db.add(new_pkg)

    # Sync new Stripe prices for all active packages missing stripe_price_id
    if settings.spectra_mode in ("dev", "public") and settings.stripe_secret_key:
        await db.flush()
        await _sync_stripe_packages(db)

    invalidate_platform_cache()


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


async def _seed_subscription_pricing(db: AsyncSession, tiers: dict) -> None:
    """Seed subscription pricing keys to platform_settings if not present.

    Uses direct DB queries (not cached get/get_all) to avoid stale cache
    during startup. Only inserts missing keys -- never overwrites existing.
    """
    for tier_name, tier_config in tiers.items():
        if not tier_config.get("has_plan"):
            continue

        price_key = f"price_{tier_name}_monthly_cents"
        stripe_key = f"stripe_price_{tier_name}_monthly"

        # Check price_cents key
        result = await db.execute(
            select(PlatformSetting).where(PlatformSetting.key == price_key)
        )
        existing = result.scalar_one_or_none()
        if existing is None:
            await upsert(db, price_key, tier_config["price_cents"], admin_id=None)
            logger.info("Seeded %s = %d", price_key, tier_config["price_cents"])

        # Check stripe_price key
        result = await db.execute(
            select(PlatformSetting).where(PlatformSetting.key == stripe_key)
        )
        existing = result.scalar_one_or_none()
        if existing is None:
            await upsert(db, stripe_key, "", admin_id=None)
            logger.info("Seeded %s (empty placeholder)", stripe_key)


async def _seed_credit_packages(db: AsyncSession, packages: list[dict]) -> None:
    """Seed credit packages to credit_packages table if not present.

    Matches by name. Only inserts missing packages -- never overwrites existing.
    """
    for pkg_config in packages:
        result = await db.execute(
            select(CreditPackage).where(CreditPackage.name == pkg_config["name"])
        )
        existing = result.scalar_one_or_none()
        if existing is None:
            new_pkg = CreditPackage(
                name=pkg_config["name"],
                price_cents=pkg_config["price_cents"],
                credit_amount=pkg_config["credit_amount"],
                display_order=pkg_config["display_order"],
            )
            db.add(new_pkg)
            logger.info("Seeded credit package: %s", pkg_config["name"])


async def _sync_stripe_prices(db: AsyncSession, tiers: dict) -> None:
    """Create Stripe Products/Prices for subscription tiers missing stripe_price_id.

    Only runs in dev/public mode. Failures are graceful (logged, not raised).
    """
    for tier_name, tier_config in tiers.items():
        if not tier_config.get("has_plan"):
            continue

        stripe_key = f"stripe_price_{tier_name}_monthly"

        # Check if already has a Stripe price ID
        result = await db.execute(
            select(PlatformSetting).where(PlatformSetting.key == stripe_key)
        )
        row = result.scalar_one_or_none()
        stripe_id = json.loads(row.value) if row and row.value else ""

        if stripe_id:
            continue  # Already has a Stripe price, skip

        try:
            from app.services.subscription import SubscriptionService

            client = SubscriptionService._get_stripe_client()
            product = client.v1.products.create(params={
                "name": f"Spectra {tier_name.title()} Plan",
                "metadata": {"tier": tier_name, "type": "subscription"},
            })
            price = client.v1.prices.create(params={
                "product": product.id,
                "unit_amount": tier_config["price_cents"],
                "currency": "usd",
                "recurring": {"interval": "month"},
                "lookup_key": f"{tier_name}_monthly",
                "transfer_lookup_key": True,
            })
            await upsert(db, stripe_key, price.id, admin_id=None)
            logger.info("Created Stripe price for %s: %s", tier_name, price.id)
        except Exception as e:
            logger.warning("Stripe sync failed for tier '%s': %s", tier_name, str(e))


async def _sync_stripe_packages(db: AsyncSession) -> None:
    """Create Stripe Products/Prices for credit packages missing stripe_price_id.

    Only runs in dev/public mode. Failures are graceful (logged, not raised).
    """
    result = await db.execute(
        select(CreditPackage).where(CreditPackage.stripe_price_id.is_(None))
    )
    packages = result.scalars().all()
    for pkg in packages:
        try:
            from app.services.subscription import SubscriptionService

            client = SubscriptionService._get_stripe_client()
            product = client.v1.products.create(params={
                "name": f"Spectra {pkg.name}",
                "metadata": {"type": "credit_package", "credit_amount": str(pkg.credit_amount)},
            })
            price = client.v1.prices.create(params={
                "product": product.id,
                "unit_amount": pkg.price_cents,
                "currency": "usd",
            })
            pkg.stripe_price_id = price.id
            logger.info("Created Stripe price for package '%s': %s", pkg.name, price.id)
        except Exception as e:
            logger.warning("Stripe sync failed for package '%s': %s", pkg.name, str(e))
