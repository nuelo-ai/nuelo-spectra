"""UserClassService for loading and caching tier configuration from user_classes.yaml."""

import time
from pathlib import Path

import yaml


# Module-level cache (same TTL pattern as platform_settings: 30s)
_user_classes_cache: dict | None = None
_cache_loaded_at: float = 0.0
_CACHE_TTL_SECONDS: float = 30.0

_CONFIG_PATH = Path(__file__).parent.parent / "config" / "user_classes.yaml"


def get_user_classes() -> dict:
    """Load and cache the full user_classes dict from YAML.

    Returns the ``user_classes`` key from user_classes.yaml.
    Uses a 30-second TTL cache to avoid repeated disk reads.
    """
    global _user_classes_cache, _cache_loaded_at

    now = time.time()
    if _user_classes_cache is not None and (now - _cache_loaded_at) < _CACHE_TTL_SECONDS:
        return _user_classes_cache

    with open(_CONFIG_PATH, "r") as f:
        data = yaml.safe_load(f)

    _user_classes_cache = data["user_classes"]
    _cache_loaded_at = now
    return _user_classes_cache


def get_class_config(class_name: str) -> dict | None:
    """Return config for a specific user class, or None if not found."""
    classes = get_user_classes()
    return classes.get(class_name)


def get_default_class() -> str:
    """Return the default user class name for new registrations."""
    return "free_trial"


def invalidate_cache() -> None:
    """Clear the user classes cache. Useful for testing."""
    global _user_classes_cache, _cache_loaded_at
    _user_classes_cache = None
    _cache_loaded_at = 0.0
