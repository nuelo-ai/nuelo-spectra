"""Tests for subscription plan change (upgrade/downgrade) and on-demand selection.

Covers: SUB-02 (upgrade), SUB-03 (downgrade), SUB-05 (select on-demand).
"""
import pytest
from unittest.mock import patch, MagicMock

# Stub tests — implementation follows in Task 1b after service methods exist


@pytest.mark.asyncio
async def test_change_plan_upgrade_uses_proration(client, auth_headers, db_session):
    """SUB-02: Upgrade from standard to premium uses create_prorations."""
    pytest.skip("Stub — implement after change_plan service method exists")


@pytest.mark.asyncio
async def test_change_plan_downgrade_no_proration(client, auth_headers, db_session):
    """SUB-03: Downgrade from premium to standard uses proration_behavior=none."""
    pytest.skip("Stub — implement after change_plan service method exists")


@pytest.mark.asyncio
async def test_change_plan_same_tier_rejected(client, auth_headers, db_session):
    """Changing to the same plan tier returns 400."""
    pytest.skip("Stub — implement after change_plan service method exists")


@pytest.mark.asyncio
async def test_change_plan_no_subscription_rejected(client, auth_headers, db_session):
    """Changing plan without active subscription returns 400."""
    pytest.skip("Stub — implement after change_plan service method exists")


@pytest.mark.asyncio
async def test_select_on_demand_sets_user_class(client, auth_headers, db_session):
    """SUB-05: Selecting On Demand updates user_class to on_demand."""
    pytest.skip("Stub — implement after select-on-demand endpoint exists")


@pytest.mark.asyncio
async def test_select_on_demand_cancels_existing_subscription(client, auth_headers, db_session):
    """SUB-05: Selecting On Demand with active subscription sets cancel_at_period_end."""
    pytest.skip("Stub — implement after select-on-demand endpoint exists")


@pytest.mark.asyncio
async def test_select_on_demand_already_on_demand_rejected(client, auth_headers, db_session):
    """Selecting On Demand when already on_demand returns 400."""
    pytest.skip("Stub — implement after select-on-demand endpoint exists")
