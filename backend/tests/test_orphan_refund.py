"""Unit tests for the orphan-refund scheduler job.

Tests process_orphan_refunds() in isolation using AsyncMock.
No database or scheduler required.
"""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch, call
from uuid import uuid4


# ============================================================================
# Helpers
# ============================================================================


def _make_mock_pulse_run(collection_id=None, status="analyzing", credit_cost=5.0):
    """Create a mock PulseRun ORM object that is 'stuck'."""
    run = MagicMock()
    run.id = uuid4()
    run.collection_id = collection_id or uuid4()
    run.status = status
    run.credit_cost = credit_cost
    run.error_message = None
    run.completed_at = None
    # created_at far in the past
    run.created_at = datetime.now(timezone.utc) - timedelta(hours=2)
    return run


# ============================================================================
# Test Group: Orphan Refund Job
# ============================================================================


class TestOrphanRefundJob:
    """Tests for process_orphan_refunds() scheduler job."""

    @pytest.mark.asyncio
    async def test_orphan_refund_job(self):
        """Orphan job marks stuck runs failed and refunds credits when no signals exist."""
        from app.scheduler import process_orphan_refunds

        user_id = uuid4()
        mock_run = _make_mock_pulse_run(status="analyzing", credit_cost=5.0)

        # Build a mock DB session
        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)

        # First execute() call returns the stuck pulse runs
        pulse_run_result = MagicMock()
        pulse_run_result.all.return_value = [(mock_run, user_id)]

        # Second execute() call returns signal_count = 0
        signal_count_result = MagicMock()
        signal_count_result.scalar_one.return_value = 0

        mock_db.execute = AsyncMock(side_effect=[pulse_run_result, signal_count_result])

        mock_session_maker = MagicMock()
        mock_session_maker.return_value = mock_db

        mock_settings = MagicMock()
        mock_settings.pulse_orphan_timeout_minutes = 30

        with patch("app.scheduler.async_session_maker", mock_session_maker), patch(
            "app.config.get_settings", return_value=mock_settings
        ), patch(
            "app.scheduler.CreditService.refund", new_callable=AsyncMock
        ) as mock_refund:
            await process_orphan_refunds()

        # CreditService.refund called with correct user_id and amount
        mock_refund.assert_called_once()
        call_args = mock_refund.call_args
        assert call_args[0][1] == user_id  # user_id positional arg
        assert call_args[0][2] == mock_run.credit_cost  # amount positional arg

        # Run marked failed
        assert mock_run.status == "failed"
        assert mock_run.error_message is not None
        assert "timed out" in mock_run.error_message.lower()

        # DB committed
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_orphan_refund_skips_runs_with_signals(self):
        """Orphan job does NOT refund credits when signals already exist."""
        from app.scheduler import process_orphan_refunds

        user_id = uuid4()
        mock_run = _make_mock_pulse_run(status="analyzing", credit_cost=5.0)

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)

        pulse_run_result = MagicMock()
        pulse_run_result.all.return_value = [(mock_run, user_id)]

        # Signal count = 3 (partial run — should not refund)
        signal_count_result = MagicMock()
        signal_count_result.scalar_one.return_value = 3

        mock_db.execute = AsyncMock(side_effect=[pulse_run_result, signal_count_result])

        mock_session_maker = MagicMock()
        mock_session_maker.return_value = mock_db

        mock_settings = MagicMock()
        mock_settings.pulse_orphan_timeout_minutes = 30

        with patch("app.scheduler.async_session_maker", mock_session_maker), patch(
            "app.config.get_settings", return_value=mock_settings
        ), patch(
            "app.scheduler.CreditService.refund", new_callable=AsyncMock
        ) as mock_refund:
            await process_orphan_refunds()

        # refund should NOT be called when signals exist
        mock_refund.assert_not_called()

        # Run still marked failed
        assert mock_run.status == "failed"

        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_orphan_refund_rollback_on_error(self):
        """Orphan job rolls back on unexpected exception."""
        from app.scheduler import process_orphan_refunds

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)
        mock_db.execute = AsyncMock(side_effect=Exception("DB connection lost"))

        mock_session_maker = MagicMock()
        mock_session_maker.return_value = mock_db

        mock_settings = MagicMock()
        mock_settings.pulse_orphan_timeout_minutes = 30

        with patch("app.scheduler.async_session_maker", mock_session_maker), patch(
            "app.config.get_settings", return_value=mock_settings
        ):
            # Should not raise — job catches all exceptions
            await process_orphan_refunds()

        mock_db.rollback.assert_called_once()
        mock_db.commit.assert_not_called()
