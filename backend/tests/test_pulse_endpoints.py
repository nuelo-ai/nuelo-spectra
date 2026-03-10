"""Integration tests for Pulse HTTP endpoints.

Tests the POST trigger and GET polling endpoints added in Phase 50 Plan 02.
All tests use unittest.mock — no database or live API required.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import HTTPException


# ============================================================================
# Helpers
# ============================================================================


def _make_mock_user(user_class: str = "standard", user_id=None):
    """Create a mock WorkspaceUser object."""
    user = MagicMock()
    user.id = user_id or uuid4()
    user.user_class = user_class
    user.is_active = True
    return user


def _make_mock_collection(user_id=None, collection_id=None):
    """Create a mock Collection object."""
    coll = MagicMock()
    coll.id = collection_id or uuid4()
    coll.user_id = user_id or uuid4()
    coll.name = "Test Collection"
    coll.created_at = datetime.now(timezone.utc)
    coll.updated_at = datetime.now(timezone.utc)
    return coll


def _make_mock_pulse_run(collection_id=None, run_id=None, status="pending", credit_cost=5.0, signals=None):
    """Create a mock PulseRun ORM object with a fixed __dict__ for model_validate."""
    _id = run_id or uuid4()
    _collection_id = collection_id or uuid4()
    _signals = signals if signals is not None else []
    _now = datetime.now(timezone.utc)

    # Use a plain object so we can set attributes and __dict__ freely
    class FakePulseRun:
        pass

    run = FakePulseRun()
    run.id = _id
    run.collection_id = _collection_id
    run.status = status
    run.credit_cost = credit_cost
    run.error_message = None
    run.started_at = None
    run.completed_at = None
    run.created_at = _now
    run.signals = _signals
    # __dict__ is already set correctly on a plain object
    return run


def _make_mock_signal():
    """Create a mock Signal ORM object."""
    sig = MagicMock()
    sig.id = uuid4()
    sig.title = "Revenue Anomaly"
    sig.severity = "warning"
    sig.category = "trend"
    sig.analysis = "Revenue dipped 15% below 3-month average."
    sig.evidence = {"metric": "revenue", "context": "Q1 comparison"}
    sig.chart_data = {"labels": ["Jan", "Feb"], "values": [100, 85]}
    sig.chart_type = "bar"
    sig.created_at = datetime.now(timezone.utc)
    return sig


# ============================================================================
# Test Group: Pulse Trigger Endpoint (POST /{collection_id}/pulse)
# ============================================================================


class TestTriggerPulse:
    """Tests for POST /collections/{collection_id}/pulse."""

    @pytest.mark.asyncio
    async def test_trigger_pulse_202(self):
        """POST with valid request returns 202 with pulse_run_id, status, credit_cost."""
        from app.routers.collections import trigger_pulse
        from app.schemas.pulse import PulseRunCreate

        user = _make_mock_user()
        collection_id = uuid4()
        mock_collection = _make_mock_collection(user_id=user.id, collection_id=collection_id)
        mock_run = _make_mock_pulse_run(collection_id=collection_id, status="pending", credit_cost=5.0, signals=[])

        mock_db = AsyncMock()
        body = PulseRunCreate(file_ids=[uuid4()])

        with patch(
            "app.routers.collections.CollectionService.get_user_collection",
            new_callable=AsyncMock,
            return_value=mock_collection,
        ), patch(
            "app.routers.collections.PulseService.run_detection",
            new_callable=AsyncMock,
            return_value=mock_run,
        ):
            result = await trigger_pulse(collection_id, body, user, mock_db)

        assert result.pulse_run_id == mock_run.id
        assert result.status == "pending"
        assert result.credit_cost == 5.0

    @pytest.mark.asyncio
    async def test_trigger_pulse_402(self):
        """POST with insufficient credits raises 402 with required and available keys."""
        from app.routers.collections import trigger_pulse
        from app.schemas.pulse import PulseRunCreate

        user = _make_mock_user()
        collection_id = uuid4()
        mock_collection = _make_mock_collection(user_id=user.id, collection_id=collection_id)

        mock_db = AsyncMock()
        body = PulseRunCreate(file_ids=[uuid4()])

        with patch(
            "app.routers.collections.CollectionService.get_user_collection",
            new_callable=AsyncMock,
            return_value=mock_collection,
        ), patch(
            "app.routers.collections.PulseService.run_detection",
            new_callable=AsyncMock,
            side_effect=HTTPException(
                status_code=402,
                detail={"detail": "Insufficient credits", "required": 5.0, "available": 2.0},
            ),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await trigger_pulse(collection_id, body, user, mock_db)

        assert exc_info.value.status_code == 402
        assert exc_info.value.detail["required"] == 5.0
        assert exc_info.value.detail["available"] == 2.0

    @pytest.mark.asyncio
    async def test_trigger_pulse_409(self):
        """POST with active run raises 409 with active_run_id key."""
        from app.routers.collections import trigger_pulse
        from app.schemas.pulse import PulseRunCreate

        user = _make_mock_user()
        collection_id = uuid4()
        active_run_id = str(uuid4())
        mock_collection = _make_mock_collection(user_id=user.id, collection_id=collection_id)

        mock_db = AsyncMock()
        body = PulseRunCreate(file_ids=[uuid4()])

        with patch(
            "app.routers.collections.CollectionService.get_user_collection",
            new_callable=AsyncMock,
            return_value=mock_collection,
        ), patch(
            "app.routers.collections.PulseService.run_detection",
            new_callable=AsyncMock,
            side_effect=HTTPException(
                status_code=409,
                detail={
                    "detail": "A detection run is already in progress",
                    "active_run_id": active_run_id,
                },
            ),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await trigger_pulse(collection_id, body, user, mock_db)

        assert exc_info.value.status_code == 409
        assert "active_run_id" in exc_info.value.detail
        assert exc_info.value.detail["active_run_id"] == active_run_id

    @pytest.mark.asyncio
    async def test_trigger_pulse_404_collection_not_found(self):
        """POST with unknown collection_id raises 404."""
        from app.routers.collections import trigger_pulse
        from app.schemas.pulse import PulseRunCreate

        user = _make_mock_user()
        collection_id = uuid4()
        mock_db = AsyncMock()
        body = PulseRunCreate(file_ids=[uuid4()])

        with patch(
            "app.routers.collections.CollectionService.get_user_collection",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await trigger_pulse(collection_id, body, user, mock_db)

        assert exc_info.value.status_code == 404


# ============================================================================
# Test Group: Pulse Polling Endpoint (GET /{collection_id}/pulse-runs/{run_id})
# ============================================================================


class TestGetPulseRun:
    """Tests for GET /collections/{collection_id}/pulse-runs/{run_id}."""

    @pytest.mark.asyncio
    async def test_poll_pulse_run(self):
        """GET returns 200 with a status field when run is pending."""
        from app.routers.collections import get_pulse_run

        user = _make_mock_user()
        collection_id = uuid4()
        run_id = uuid4()
        mock_collection = _make_mock_collection(user_id=user.id, collection_id=collection_id)
        mock_run = _make_mock_pulse_run(collection_id=collection_id, run_id=run_id, status="pending", signals=[])

        mock_db = AsyncMock()

        with patch(
            "app.routers.collections.CollectionService.get_user_collection",
            new_callable=AsyncMock,
            return_value=mock_collection,
        ), patch(
            "app.routers.collections.PulseService.get_pulse_run",
            new_callable=AsyncMock,
            return_value=mock_run,
        ):
            result = await get_pulse_run(collection_id, run_id, user, mock_db)

        assert result.status == "pending"
        assert result.signals == []
        assert result.signal_count == 0

    @pytest.mark.asyncio
    async def test_poll_pulse_run_completed(self):
        """GET returns signals list with length >= 1 when status=completed."""
        from app.routers.collections import get_pulse_run

        user = _make_mock_user()
        collection_id = uuid4()
        run_id = uuid4()
        mock_collection = _make_mock_collection(user_id=user.id, collection_id=collection_id)
        mock_signal = _make_mock_signal()
        mock_run = _make_mock_pulse_run(
            collection_id=collection_id, run_id=run_id, status="completed", signals=[mock_signal]
        )

        mock_db = AsyncMock()

        with patch(
            "app.routers.collections.CollectionService.get_user_collection",
            new_callable=AsyncMock,
            return_value=mock_collection,
        ), patch(
            "app.routers.collections.PulseService.get_pulse_run",
            new_callable=AsyncMock,
            return_value=mock_run,
        ):
            result = await get_pulse_run(collection_id, run_id, user, mock_db)

        assert result.status == "completed"
        assert len(result.signals) >= 1

    @pytest.mark.asyncio
    async def test_poll_pulse_run_ownership_bypass_prevented(self):
        """GET raises 404 when pulse_run.collection_id != collection_id in request."""
        from app.routers.collections import get_pulse_run

        user = _make_mock_user()
        collection_id = uuid4()
        different_collection_id = uuid4()
        run_id = uuid4()
        mock_collection = _make_mock_collection(user_id=user.id, collection_id=collection_id)
        mock_run = _make_mock_pulse_run(
            collection_id=different_collection_id, run_id=run_id, status="completed", signals=[]
        )

        mock_db = AsyncMock()

        with patch(
            "app.routers.collections.CollectionService.get_user_collection",
            new_callable=AsyncMock,
            return_value=mock_collection,
        ), patch(
            "app.routers.collections.PulseService.get_pulse_run",
            new_callable=AsyncMock,
            return_value=mock_run,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_pulse_run(collection_id, run_id, user, mock_db)

        assert exc_info.value.status_code == 404
