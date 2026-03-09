"""Tests for ADMIN-01: tier gating — workspace access and collection limits.

Covers all five tiers: free, free_trial, standard, premium, internal.
All tests use unittest.mock — no database or live API required.

Resolution: free_trial has workspace_access=True (per user_classes.yaml).
TestWorkspaceAccess covers free tier only. TestCollectionLimit covers
free_trial (passes workspace, blocked on 2nd collection create).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from fastapi import HTTPException
from app.dependencies import require_workspace_access


def _make_mock_user(user_class: str = "standard", user_id=None):
    """Create a mock User object for tier gating tests."""
    user = MagicMock()
    user.id = user_id or uuid4()
    user.user_class = user_class
    user.is_active = True
    return user


@pytest.mark.asyncio
class TestWorkspaceAccess:
    """ADMIN-01: workspace_access boolean enforcement (free tier blocked)."""

    async def test_placeholder(self):
        pytest.fail("Wave 0 stub — implement in Task 3")


@pytest.mark.asyncio
class TestCollectionLimit:
    """ADMIN-01: max_active_collections enforcement (free_trial capped at 1)."""

    async def test_placeholder(self):
        pytest.fail("Wave 0 stub — implement in Task 3")


@pytest.mark.asyncio
class TestUnlimitedTiers:
    """ADMIN-01: standard/premium/internal tiers are not blocked by collection limits."""

    async def test_placeholder(self):
        pytest.fail("Wave 0 stub — implement in Task 3")
