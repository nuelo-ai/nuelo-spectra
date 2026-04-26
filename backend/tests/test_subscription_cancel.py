"""Tests for subscription cancellation.

Covers: SUB-04 (cancel subscription at period end).
"""
import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.asyncio
async def test_cancel_subscription_sets_cancel_at_period_end(client, auth_headers, db_session):
    """SUB-04: Cancel calls stripe.subscriptions.update with cancel_at_period_end=True."""
    pytest.skip("Stub — implement after cancel_subscription service method exists")


@pytest.mark.asyncio
async def test_cancel_subscription_no_active_subscription_rejected(client, auth_headers, db_session):
    """Cancel without active subscription returns 400."""
    pytest.skip("Stub — implement after cancel_subscription service method exists")


@pytest.mark.asyncio
async def test_cancel_subscription_returns_cancel_date(client, auth_headers, db_session):
    """SUB-04: Cancel response includes cancel_at ISO date."""
    pytest.skip("Stub — implement after cancel_subscription service method exists")
