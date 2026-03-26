"""Tests for tier configuration (TIER-01, TIER-02)."""

import pytest


class TestTierConfig:
    """Verify user_classes.yaml defines the correct 5-tier structure."""

    def test_four_consumer_tiers(self):
        """TIER-01: Four consumer tiers exist: free_trial, on_demand, standard, premium."""
        pytest.skip("Wave 0 stub")

    def test_tier_keys(self):
        """TIER-02: Tier keys are free_trial, on_demand, standard, premium, internal (no 'free')."""
        pytest.skip("Wave 0 stub")

    def test_standard_reset_policy_none(self):
        """TIER-08 (partial): standard tier has reset_policy=none."""
        pytest.skip("Wave 0 stub")

    def test_premium_reset_policy_none(self):
        """TIER-08 (partial): premium tier has reset_policy=none."""
        pytest.skip("Wave 0 stub")
