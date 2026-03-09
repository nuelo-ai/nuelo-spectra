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
from app.schemas.collection import CollectionCreate


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

    async def test_free_tier_blocked(self):
        """Free tier user is blocked from workspace access with 403."""
        user = _make_mock_user(user_class="free")
        with patch(
            "app.dependencies.get_class_config",
            return_value={"workspace_access": False, "max_active_collections": 0},
        ):
            with pytest.raises(HTTPException) as exc_info:
                await require_workspace_access(user)
            assert exc_info.value.status_code == 403
            assert "workspace access" in exc_info.value.detail.lower()

    async def test_free_trial_workspace_allowed(self):
        """Free trial user has workspace_access=True — no exception raised."""
        user = _make_mock_user(user_class="free_trial")
        with patch(
            "app.dependencies.get_class_config",
            return_value={"workspace_access": True, "max_active_collections": 1},
        ):
            result = await require_workspace_access(user)
            assert result is user


@pytest.mark.asyncio
class TestCollectionLimit:
    """ADMIN-01: max_active_collections enforcement (free_trial capped at 1)."""

    async def test_free_trial_first_collection_allowed(self):
        """Free trial user can create their first collection (count=0, limit=1)."""
        from app.routers.collections import create_collection

        user = _make_mock_user(user_class="free_trial")
        body = CollectionCreate(name="My First Collection")
        mock_db = AsyncMock()

        mock_collection = MagicMock()
        mock_collection.id = uuid4()
        mock_collection.name = "My First Collection"
        mock_collection.description = None
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        mock_collection.created_at = now
        mock_collection.updated_at = now

        with patch(
            "app.routers.collections.get_class_config",
            return_value={"workspace_access": True, "max_active_collections": 1},
        ):
            with patch(
                "app.routers.collections.CollectionService.count_user_collections",
                new_callable=AsyncMock,
                return_value=0,  # below limit
            ):
                with patch(
                    "app.routers.collections.CollectionService.create_collection",
                    new_callable=AsyncMock,
                    return_value=mock_collection,
                ):
                    # Should not raise — first collection is allowed
                    result = await create_collection(body, user, mock_db)
                    assert result.name == "My First Collection"

    async def test_free_trial_second_collection_blocked(self):
        """Free trial user is blocked creating a second collection (count=1, limit=1) with 403."""
        from app.routers.collections import create_collection

        user = _make_mock_user(user_class="free_trial")
        body = CollectionCreate(name="Second Collection")
        mock_db = AsyncMock()

        with patch(
            "app.routers.collections.get_class_config",
            return_value={"workspace_access": True, "max_active_collections": 1},
        ):
            with patch(
                "app.routers.collections.CollectionService.count_user_collections",
                new_callable=AsyncMock,
                return_value=1,  # already at limit
            ):
                with pytest.raises(HTTPException) as exc_info:
                    await create_collection(body, user, mock_db)
                assert exc_info.value.status_code == 403
                assert "Collection limit reached" in exc_info.value.detail


@pytest.mark.asyncio
class TestUnlimitedTiers:
    """ADMIN-01: standard/premium/internal tiers are not blocked by collection limits."""

    async def test_standard_not_blocked(self):
        """Standard tier (limit=5) user with 4 collections can create another."""
        from app.routers.collections import create_collection

        user = _make_mock_user(user_class="standard")
        body = CollectionCreate(name="Standard Collection")
        mock_db = AsyncMock()

        mock_collection = MagicMock()
        mock_collection.id = uuid4()
        mock_collection.name = "Standard Collection"
        mock_collection.description = None
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        mock_collection.created_at = now
        mock_collection.updated_at = now

        with patch(
            "app.routers.collections.get_class_config",
            return_value={"workspace_access": True, "max_active_collections": 5},
        ):
            with patch(
                "app.routers.collections.CollectionService.count_user_collections",
                new_callable=AsyncMock,
                return_value=4,  # below limit of 5
            ):
                with patch(
                    "app.routers.collections.CollectionService.create_collection",
                    new_callable=AsyncMock,
                    return_value=mock_collection,
                ):
                    result = await create_collection(body, user, mock_db)
                    assert result.name == "Standard Collection"

    async def test_premium_not_blocked(self):
        """Premium tier (limit=-1 unlimited) user with 10 collections can create another."""
        from app.routers.collections import create_collection

        user = _make_mock_user(user_class="premium")
        body = CollectionCreate(name="Premium Collection")
        mock_db = AsyncMock()

        mock_collection = MagicMock()
        mock_collection.id = uuid4()
        mock_collection.name = "Premium Collection"
        mock_collection.description = None
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        mock_collection.created_at = now
        mock_collection.updated_at = now

        with patch(
            "app.routers.collections.get_class_config",
            return_value={"workspace_access": True, "max_active_collections": -1},
        ):
            # count_user_collections should NOT be called for unlimited tier
            # (router skips the check when max_collections == -1)
            with patch(
                "app.routers.collections.CollectionService.create_collection",
                new_callable=AsyncMock,
                return_value=mock_collection,
            ):
                result = await create_collection(body, user, mock_db)
                assert result.name == "Premium Collection"

    async def test_internal_not_blocked(self):
        """Internal tier (limit=-1 unlimited) user with 10 collections can create another."""
        from app.routers.collections import create_collection

        user = _make_mock_user(user_class="internal")
        body = CollectionCreate(name="Internal Collection")
        mock_db = AsyncMock()

        mock_collection = MagicMock()
        mock_collection.id = uuid4()
        mock_collection.name = "Internal Collection"
        mock_collection.description = None
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        mock_collection.created_at = now
        mock_collection.updated_at = now

        with patch(
            "app.routers.collections.get_class_config",
            return_value={"workspace_access": True, "max_active_collections": -1},
        ):
            with patch(
                "app.routers.collections.CollectionService.create_collection",
                new_callable=AsyncMock,
                return_value=mock_collection,
            ):
                result = await create_collection(body, user, mock_db)
                assert result.name == "Internal Collection"
