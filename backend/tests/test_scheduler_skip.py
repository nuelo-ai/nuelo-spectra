"""Tests for APScheduler subscription-tier skip logic (TIER-08)."""

import pytest


class TestSchedulerSkip:
    """Verify APScheduler credit reset skips subscription-tier users."""

    def test_skip_subscription_tiers(self):
        """TIER-08: Scheduler skips standard/premium users (reset_policy=none -> is_reset_due() returns False)."""
        pytest.skip("Wave 0 stub")

    def test_internal_unlimited_skipped(self):
        """Internal users with reset_policy=unlimited are skipped."""
        pytest.skip("Wave 0 stub")

    def test_free_trial_none_skipped(self):
        """Free trial users with reset_policy=none are skipped."""
        pytest.skip("Wave 0 stub")
