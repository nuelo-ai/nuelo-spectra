"""PlatformSettingsService for runtime platform configuration.

Provides a module-level TTL cache for reading platform settings from the
platform_settings table, with validation and upsert support.
"""

import json
import time
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform_setting import PlatformSetting
from app.services.user_class import get_user_classes


# Module-level TTL cache (same pattern as user_class.py)
_settings_cache: dict[str, str] | None = None
_cache_loaded_at: float = 0.0
_CACHE_TTL_SECONDS: float = 30.0

# Defaults for all known setting keys (values are JSON-encoded strings)
DEFAULTS: dict[str, str] = {
    "allow_public_signup": json.dumps(True),
    "default_user_class": json.dumps("free_trial"),
    "invite_expiry_days": json.dumps(7),
    "default_credit_cost": json.dumps("1.0"),
    "max_pending_invites": json.dumps(50),
    "workspace_credit_cost_pulse": json.dumps("5.0"),
    "stripe_price_standard_monthly": json.dumps(""),
    "stripe_price_premium_monthly": json.dumps(""),
    "price_standard_monthly_cents": json.dumps(2900),   # $29.00
    "price_premium_monthly_cents": json.dumps(7900),     # $79.00
    "monetization_enabled": json.dumps(False),
}

VALID_KEYS = set(DEFAULTS.keys())


async def get_all(db: AsyncSession) -> dict[str, str]:
    """Load all settings with 30s TTL cache.

    Queries the platform_settings table and merges with DEFAULTS for any
    missing keys. Returns raw JSON-encoded string values.
    """
    global _settings_cache, _cache_loaded_at

    now = time.time()
    if _settings_cache is not None and (now - _cache_loaded_at) < _CACHE_TTL_SECONDS:
        return _settings_cache

    result = await db.execute(select(PlatformSetting))
    rows = result.scalars().all()

    settings = dict(DEFAULTS)  # Start with defaults
    for row in rows:
        settings[row.key] = row.value

    _settings_cache = settings
    _cache_loaded_at = now
    return _settings_cache


async def get(db: AsyncSession, key: str) -> Any:
    """Get a single parsed setting value.

    Args:
        db: Database session.
        key: Setting key name.

    Returns:
        Parsed Python value (bool, str, int, etc.)
    """
    all_settings = await get_all(db)
    raw = all_settings.get(key)
    if raw is None:
        return None
    return json.loads(raw)


async def upsert(db: AsyncSession, key: str, value: Any, admin_id: Optional[UUID] = None) -> None:
    """Upsert a single setting key.

    Args:
        db: Database session.
        key: Setting key name.
        value: Python value to store (will be JSON-encoded).
        admin_id: UUID of the admin performing the change, or None for system operations.
    """
    result = await db.execute(
        select(PlatformSetting).where(PlatformSetting.key == key)
    )
    existing = result.scalar_one_or_none()

    json_value = json.dumps(value)

    if existing:
        existing.value = json_value
        if admin_id is not None:
            existing.updated_by = admin_id
    else:
        setting = PlatformSetting(
            key=key,
            value=json_value,
            updated_by=admin_id,
        )
        db.add(setting)


def invalidate_cache() -> None:
    """Reset the settings cache immediately."""
    global _settings_cache, _cache_loaded_at
    _settings_cache = None
    _cache_loaded_at = 0.0


def validate_setting(key: str, value: Any) -> str | None:
    """Validate a setting key/value pair.

    Returns:
        Error message string if invalid, None if valid.
    """
    if key not in VALID_KEYS:
        return f"Unknown setting key: {key}"

    if key == "allow_public_signup":
        if not isinstance(value, bool):
            return "allow_public_signup must be a boolean"

    elif key == "default_user_class":
        if not isinstance(value, str):
            return "default_user_class must be a string"
        valid_classes = get_user_classes().keys()
        if value not in valid_classes:
            return f"default_user_class must be one of: {', '.join(valid_classes)}"

    elif key == "invite_expiry_days":
        if not isinstance(value, int) or isinstance(value, bool):
            return "invite_expiry_days must be an integer"
        if value < 1 or value > 365:
            return "invite_expiry_days must be between 1 and 365"

    elif key == "default_credit_cost":
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return "default_credit_cost must be a number"
        if value <= 0:
            return "default_credit_cost must be greater than 0"

    elif key == "max_pending_invites":
        if not isinstance(value, int) or isinstance(value, bool):
            return "max_pending_invites must be an integer"
        if value < 1 or value > 1000:
            return "max_pending_invites must be between 1 and 1000"

    elif key == "workspace_credit_cost_pulse":
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return "workspace_credit_cost_pulse must be a number"
        if value <= 0:
            return "workspace_credit_cost_pulse must be greater than 0"

    elif key == "monetization_enabled":
        if not isinstance(value, bool):
            return "monetization_enabled must be a boolean"

    elif key in ("price_standard_monthly_cents", "price_premium_monthly_cents"):
        if not isinstance(value, int) or isinstance(value, bool):
            return f"{key} must be an integer"
        if value <= 0:
            return f"{key} must be > 0"

    elif key in ("stripe_price_standard_monthly", "stripe_price_premium_monthly"):
        if not isinstance(value, str):
            return f"{key} must be a string"

    return None
