"""Test configuration and fixtures for Spectra backend tests."""

import pytest


@pytest.fixture(autouse=True)
def clear_config_caches():
    """Clear LRU caches between tests to prevent state leakage.

    This fixture automatically runs before each test to ensure configuration
    caches (load_prompts, load_provider_registry) are cleared, preventing
    test state from leaking between tests.
    """
    from app.agents.config import load_prompts, load_provider_registry

    # Clear caches before test
    load_prompts.cache_clear()
    load_provider_registry.cache_clear()

    yield

    # Clear caches after test
    load_prompts.cache_clear()
    load_provider_registry.cache_clear()
