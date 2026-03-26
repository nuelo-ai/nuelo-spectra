"""Tests for dual-balance CreditService logic (TIER-04 through TIER-07)."""

import pytest


class TestDualBalance:
    """Verify dual-balance deduction, refund, and reset behavior."""

    def test_balance_split(self):
        """TIER-04: Deduction splits across subscription and purchased balance."""
        pytest.skip("Wave 0 stub")

    def test_deduction_order(self):
        """TIER-05: Subscription credits consumed before purchased credits."""
        pytest.skip("Wave 0 stub")

    def test_purchased_persists_on_reset(self):
        """TIER-06: Purchased balance untouched during subscription reset."""
        pytest.skip("Wave 0 stub")

    def test_subscription_reset(self):
        """TIER-07: Subscription balance resets to tier allocation."""
        pytest.skip("Wave 0 stub")
