"""Tests for billing history endpoint.

Covers: BILL-05 (billing history display).
"""
import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.asyncio
async def test_billing_history_returns_user_payments(client, auth_headers, db_session):
    """BILL-05: Billing history returns payments for the current user only."""
    pytest.skip("Stub — implement after billing-history endpoint exists")


@pytest.mark.asyncio
async def test_billing_history_sorted_by_date_descending(client, auth_headers, db_session):
    """BILL-05: Billing history items sorted newest first."""
    pytest.skip("Stub — implement after billing-history endpoint exists")


@pytest.mark.asyncio
async def test_billing_history_empty_for_new_user(client, auth_headers, db_session):
    """Billing history returns empty items list for user with no payments."""
    pytest.skip("Stub — implement after billing-history endpoint exists")


@pytest.mark.asyncio
async def test_billing_history_type_display_mapping(client, auth_headers, db_session):
    """Billing history maps payment_type to human-readable type_display."""
    pytest.skip("Stub — implement after billing-history endpoint exists")
