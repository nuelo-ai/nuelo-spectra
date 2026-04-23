"""UserClassService for loading and caching tier configuration from user_classes.yaml."""

import time
from pathlib import Path

import yaml


# Module-level cache (same TTL pattern as platform_settings: 30s)
_yaml_cache: dict | None = None
_cache_loaded_at: float = 0.0
_CACHE_TTL_SECONDS: float = 30.0

_CONFIG_PATH = Path(__file__).parent.parent / "config" / "user_classes.yaml"


def _load_yaml() -> dict:
    """Load and cache the full YAML config with 30s TTL."""
    global _yaml_cache, _cache_loaded_at

    now = time.time()
    if _yaml_cache is not None and (now - _cache_loaded_at) < _CACHE_TTL_SECONDS:
        return _yaml_cache

    if not _CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"user_classes.yaml not found at {_CONFIG_PATH}. "
            "Ensure the config file is present in backend/app/config/."
        )
    try:
        with open(_CONFIG_PATH, "r") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in user_classes.yaml: {e}") from e

    if not isinstance(data, dict) or "user_classes" not in data:
        raise ValueError("user_classes.yaml must contain a 'user_classes' key")

    _yaml_cache = data
    _cache_loaded_at = now
    return _yaml_cache


def get_user_classes() -> dict:
    """Load and cache the full user_classes dict from YAML.

    Returns the ``user_classes`` key from user_classes.yaml.
    Uses a 30-second TTL cache to avoid repeated disk reads.
    """
    return _load_yaml()["user_classes"]


def get_credit_packages() -> list[dict]:
    """Load and cache credit packages from user_classes.yaml.

    Returns the ``credit_packages`` key from user_classes.yaml.
    Uses the same 30-second TTL cache as get_user_classes().
    """
    data = _load_yaml()
    return data.get("credit_packages", [])


def get_class_config(class_name: str) -> dict | None:
    """Return config for a specific user class, or None if not found."""
    classes = get_user_classes()
    return classes.get(class_name)


def get_default_class() -> str:
    """Return the default user class name for new registrations."""
    return "free_trial"


def invalidate_cache() -> None:
    """Clear the YAML config cache. Useful for testing."""
    global _yaml_cache, _cache_loaded_at
    _yaml_cache = None
    _cache_loaded_at = 0.0
