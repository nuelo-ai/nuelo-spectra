"""Tests for PulseService lifecycle: credit pre-check, deduction, refund, pipeline."""

import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from uuid import uuid4

import pytest


def _make_mock_db():
    """Create a mock async DB session."""
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


def _make_credit_result(success=True, balance=Decimal("100"), error_message=None):
    """Create a mock CreditDeductionResult."""
    result = MagicMock()
    result.success = success
    result.balance = balance
    result.error_message = error_message
    result.next_reset = None
    return result


class TestCreditPrecheck:
    """Verify credit pre-check blocks insufficient balance."""

    def test_credit_precheck_insufficient(self):
        """run_detection with insufficient credits raises HTTPException 402."""
        from fastapi import HTTPException
        from app.services.pulse import PulseService

        db = _make_mock_db()
        collection_id = uuid4()
        user_id = uuid4()
        file_ids = [uuid4()]

        credit_result = _make_credit_result(
            success=False, balance=Decimal("2"), error_message="Insufficient credits"
        )

        with patch("app.services.pulse.platform_settings") as mock_ps, \
             patch("app.services.pulse.CreditService") as mock_cs:
            mock_ps.get = AsyncMock(return_value="5.0")
            mock_cs.deduct_credit = AsyncMock(return_value=credit_result)

            with pytest.raises(HTTPException) as exc_info:
                asyncio.get_event_loop().run_until_complete(
                    PulseService.run_detection(db, collection_id, user_id, file_ids)
                )

            assert exc_info.value.status_code == 402

    def test_credit_precheck_sufficient(self):
        """run_detection with sufficient credits creates PulseRun with status='pending'."""
        from app.services.pulse import PulseService

        db = _make_mock_db()
        collection_id = uuid4()
        user_id = uuid4()
        file_ids = [uuid4()]

        credit_result = _make_credit_result(success=True, balance=Decimal("95"))

        # Mock the active run check (no existing runs)
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = None
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        db.execute.return_value = mock_result

        # Mock file query
        mock_file = MagicMock()
        mock_file_scalars = MagicMock()
        mock_file_scalars.all.return_value = [mock_file]

        # Different responses for different db.execute calls
        call_count = 0
        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Active run check
                return mock_result
            else:
                # File query
                r = MagicMock()
                r.scalars.return_value = mock_file_scalars
                return r

        db.execute = AsyncMock(side_effect=mock_execute)

        with patch("app.services.pulse.platform_settings") as mock_ps, \
             patch("app.services.pulse.CreditService") as mock_cs, \
             patch("app.services.pulse.PulseRun") as mock_pr_cls, \
             patch("app.services.pulse.asyncio") as mock_asyncio:
            mock_ps.get = AsyncMock(return_value="5.0")
            mock_cs.deduct_credit = AsyncMock(return_value=credit_result)

            mock_pulse_run = MagicMock()
            mock_pulse_run.id = uuid4()
            mock_pulse_run.status = "pending"
            mock_pulse_run.files = []
            mock_pr_cls.return_value = mock_pulse_run

            mock_asyncio.create_task = MagicMock()

            result = asyncio.get_event_loop().run_until_complete(
                PulseService.run_detection(db, collection_id, user_id, file_ids)
            )

            assert result.status == "pending"
            mock_cs.deduct_credit.assert_called_once()


class TestCreditDeduction:
    """Verify credit deduction with correct cost."""

    def test_credit_deduction_on_start(self):
        """CreditService.deduct_credit called with correct cost from platform_settings."""
        from app.services.pulse import PulseService

        db = _make_mock_db()
        collection_id = uuid4()
        user_id = uuid4()
        file_ids = [uuid4()]

        credit_result = _make_credit_result(success=True, balance=Decimal("95"))

        # Mock active run check
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = None
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        mock_file = MagicMock()
        mock_file_scalars = MagicMock()
        mock_file_scalars.all.return_value = [mock_file]

        call_count = 0
        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_result
            else:
                r = MagicMock()
                r.scalars.return_value = mock_file_scalars
                return r

        db.execute = AsyncMock(side_effect=mock_execute)

        with patch("app.services.pulse.platform_settings") as mock_ps, \
             patch("app.services.pulse.CreditService") as mock_cs, \
             patch("app.services.pulse.PulseRun") as mock_pr_cls, \
             patch("app.services.pulse.asyncio") as mock_asyncio:
            mock_ps.get = AsyncMock(return_value="5.0")
            mock_cs.deduct_credit = AsyncMock(return_value=credit_result)

            mock_pulse_run = MagicMock()
            mock_pulse_run.id = uuid4()
            mock_pulse_run.status = "pending"
            mock_pulse_run.files = []
            mock_pr_cls.return_value = mock_pulse_run
            mock_asyncio.create_task = MagicMock()

            asyncio.get_event_loop().run_until_complete(
                PulseService.run_detection(db, collection_id, user_id, file_ids)
            )

            # Verify deduct_credit called with Decimal("5.0")
            call_args = mock_cs.deduct_credit.call_args
            assert call_args[0][1] == user_id  # user_id
            assert call_args[0][2] == Decimal("5.0")  # cost


class TestActiveRunConflict:
    """Verify one active run per collection enforced."""

    def test_active_run_conflict(self):
        """Existing active PulseRun causes 409 Conflict and credits refunded."""
        from fastapi import HTTPException
        from app.services.pulse import PulseService

        db = _make_mock_db()
        collection_id = uuid4()
        user_id = uuid4()
        file_ids = [uuid4()]

        credit_result = _make_credit_result(success=True, balance=Decimal("95"))

        # Mock active run exists
        existing_run = MagicMock()
        existing_run.status = "analyzing"
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = existing_run
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        db.execute.return_value = mock_result

        with patch("app.services.pulse.platform_settings") as mock_ps, \
             patch("app.services.pulse.CreditService") as mock_cs:
            mock_ps.get = AsyncMock(return_value="5.0")
            mock_cs.deduct_credit = AsyncMock(return_value=credit_result)
            mock_cs.refund = AsyncMock()

            with pytest.raises(HTTPException) as exc_info:
                asyncio.get_event_loop().run_until_complete(
                    PulseService.run_detection(db, collection_id, user_id, file_ids)
                )

            assert exc_info.value.status_code == 409
            # Verify credits were refunded
            mock_cs.refund.assert_called_once()


class TestPipelineRefundOnFailure:
    """Verify credits refunded on pipeline failure."""

    def test_credit_refund_on_failure(self):
        """_run_pipeline exception triggers CreditService.refund."""
        from app.services.pulse import PulseService

        pulse_run_id = uuid4()
        collection_id = uuid4()
        user_id = uuid4()
        cost = Decimal("5.0")
        file_ids = [uuid4()]

        # Mock DB session
        mock_db = _make_mock_db()

        # Mock PulseRun load
        mock_pulse_run = MagicMock()
        mock_pulse_run.status = "pending"
        mock_pulse_run.files = []

        mock_scalars = MagicMock()
        mock_scalars.first.return_value = mock_pulse_run

        mock_file = MagicMock()
        mock_file.id = file_ids[0]
        mock_file.file_path = "/tmp/test.csv"
        mock_file.original_filename = "test.csv"
        mock_file.file_type = "csv"
        mock_file.data_summary = "test data"
        mock_file.deep_profile = None
        mock_file_scalars = MagicMock()
        mock_file_scalars.all.return_value = [mock_file]

        call_count = 0
        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            r = MagicMock()
            if call_count == 1:
                r.scalars.return_value = mock_scalars
            else:
                r.scalars.return_value = mock_file_scalars
            return r

        mock_db.execute = AsyncMock(side_effect=mock_execute)

        # Mock build_pulse_graph to raise an error
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(side_effect=RuntimeError("Pipeline crashed"))

        with patch("app.services.pulse.async_session_maker") as mock_session_maker, \
             patch("app.services.pulse.CreditService") as mock_cs, \
             patch("app.services.pulse.build_pulse_graph", return_value=mock_graph), \
             patch("builtins.open", MagicMock(return_value=MagicMock(
                 __enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value=b"data"))),
                 __exit__=MagicMock(return_value=False),
             ))):
            mock_cs.refund = AsyncMock()

            # Set up async context manager for session
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            asyncio.get_event_loop().run_until_complete(
                PulseService._run_pipeline(
                    pulse_run_id, collection_id, user_id, cost, file_ids, None
                )
            )

            # Verify refund was called
            mock_cs.refund.assert_called_once()
            refund_args = mock_cs.refund.call_args
            assert refund_args[0][1] == user_id
            assert refund_args[0][2] == cost


class TestPipelinePersistsSignals:
    """Verify pipeline persists Signal rows on success."""

    def test_pipeline_persists_signals(self):
        """Successful pipeline creates Signal rows in DB."""
        from app.services.pulse import PulseService

        pulse_run_id = uuid4()
        collection_id = uuid4()
        user_id = uuid4()
        cost = Decimal("5.0")
        file_ids = [uuid4()]

        mock_db = _make_mock_db()

        # Mock PulseRun
        mock_pulse_run = MagicMock()
        mock_pulse_run.status = "pending"
        mock_pulse_run.collection = MagicMock()
        mock_pulse_run.collection.name = "Test Collection"

        mock_scalars = MagicMock()
        mock_scalars.first.return_value = mock_pulse_run

        mock_file = MagicMock()
        mock_file.id = file_ids[0]
        mock_file.file_path = "/tmp/test.csv"
        mock_file.original_filename = "test.csv"
        mock_file.file_type = "csv"
        mock_file.data_summary = "test data"
        mock_file.deep_profile = None
        mock_file_scalars = MagicMock()
        mock_file_scalars.all.return_value = [mock_file]

        call_count = 0
        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            r = MagicMock()
            if call_count == 1:
                r.scalars.return_value = mock_scalars
            else:
                r.scalars.return_value = mock_file_scalars
            return r

        mock_db.execute = AsyncMock(side_effect=mock_execute)

        # Mock successful pipeline result
        pipeline_result = {
            "signals_output": [
                {
                    "id": "sig-001",
                    "title": "Revenue Spike",
                    "severity": "critical",
                    "category": "anomaly",
                    "chartType": "bar",
                    "analysis_text": "Z-score 4.2",
                    "statistical_evidence": {
                        "metric": "z=4.2", "context": "Q4",
                        "benchmark": "$1M", "impact": "12%"
                    },
                    "chart_data": None,
                }
            ],
            "report_content": "# Report\nOne signal found.",
            "file_profiles": [{"row_count": 100}],
            "error": "",
        }

        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(return_value=pipeline_result)

        with patch("app.services.pulse.async_session_maker") as mock_session_maker, \
             patch("app.services.pulse.CreditService"), \
             patch("app.services.pulse.build_pulse_graph", return_value=mock_graph), \
             patch("app.services.pulse.Signal") as mock_signal_cls, \
             patch("app.services.pulse.Report") as mock_report_cls, \
             patch("builtins.open", MagicMock(return_value=MagicMock(
                 __enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value=b"data"))),
                 __exit__=MagicMock(return_value=False),
             ))):
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            asyncio.get_event_loop().run_until_complete(
                PulseService._run_pipeline(
                    pulse_run_id, collection_id, user_id, cost, file_ids, None
                )
            )

            # Verify Signal created
            mock_signal_cls.assert_called_once()
            signal_kwargs = mock_signal_cls.call_args[1]
            assert signal_kwargs["title"] == "Revenue Spike"
            assert signal_kwargs["severity"] == "critical"

            # Verify Report created
            mock_report_cls.assert_called_once()
            report_kwargs = mock_report_cls.call_args[1]
            assert report_kwargs["report_type"] == "pulse_detection"


class TestPipelinePersistsReport:
    """Verify report auto-generated with correct type."""

    def test_pipeline_persists_report(self):
        """Successful pipeline creates Report row with report_type='pulse_detection'."""
        from app.services.pulse import PulseService

        pulse_run_id = uuid4()
        collection_id = uuid4()
        user_id = uuid4()
        cost = Decimal("5.0")
        file_ids = [uuid4()]

        mock_db = _make_mock_db()

        mock_pulse_run = MagicMock()
        mock_pulse_run.status = "pending"
        mock_pulse_run.collection = MagicMock()
        mock_pulse_run.collection.name = "Test Collection"

        mock_scalars = MagicMock()
        mock_scalars.first.return_value = mock_pulse_run

        mock_file = MagicMock()
        mock_file.id = file_ids[0]
        mock_file.file_path = "/tmp/test.csv"
        mock_file.original_filename = "test.csv"
        mock_file.file_type = "csv"
        mock_file.data_summary = "data"
        mock_file.deep_profile = None
        mock_file_scalars = MagicMock()
        mock_file_scalars.all.return_value = [mock_file]

        call_count = 0
        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            r = MagicMock()
            if call_count == 1:
                r.scalars.return_value = mock_scalars
            else:
                r.scalars.return_value = mock_file_scalars
            return r

        mock_db.execute = AsyncMock(side_effect=mock_execute)

        pipeline_result = {
            "signals_output": [{
                "id": "sig-001", "title": "Test Signal", "severity": "info",
                "category": "trend", "chartType": "line",
                "analysis_text": "Trend found",
                "statistical_evidence": {"metric": "r=0.9", "context": "x", "benchmark": "y", "impact": "z"},
                "chart_data": None,
            }],
            "report_content": "# Detection Report\n\nTest report content.",
            "file_profiles": [{"row_count": 50}],
            "error": "",
        }

        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(return_value=pipeline_result)

        with patch("app.services.pulse.async_session_maker") as mock_session_maker, \
             patch("app.services.pulse.CreditService"), \
             patch("app.services.pulse.build_pulse_graph", return_value=mock_graph), \
             patch("app.services.pulse.Signal"), \
             patch("app.services.pulse.Report") as mock_report_cls, \
             patch("builtins.open", MagicMock(return_value=MagicMock(
                 __enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value=b"data"))),
                 __exit__=MagicMock(return_value=False),
             ))):
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            asyncio.get_event_loop().run_until_complete(
                PulseService._run_pipeline(
                    pulse_run_id, collection_id, user_id, cost, file_ids, None
                )
            )

            mock_report_cls.assert_called_once()
            report_kwargs = mock_report_cls.call_args[1]
            assert report_kwargs["report_type"] == "pulse_detection"
            assert "Detection Report" in report_kwargs["title"]
            assert report_kwargs["content"] == "# Detection Report\n\nTest report content."


class TestPipelineStatusTransitions:
    """Verify PulseRun status transitions through all states."""

    def test_pipeline_status_transitions(self):
        """Status goes pending -> profiling -> analyzing -> completed."""
        from app.services.pulse import PulseService

        pulse_run_id = uuid4()
        collection_id = uuid4()
        user_id = uuid4()
        cost = Decimal("5.0")
        file_ids = [uuid4()]

        mock_db = _make_mock_db()

        mock_pulse_run = MagicMock()
        mock_pulse_run.status = "pending"
        mock_pulse_run.collection = MagicMock()
        mock_pulse_run.collection.name = "Test Collection"

        # Track status transitions
        status_log = []
        original_status = mock_pulse_run.status

        def track_status(val):
            status_log.append(val)

        type(mock_pulse_run).status = PropertyMock(
            side_effect=lambda *a: status_log[-1] if status_log else "pending",
            fset=lambda self, val: track_status(val),
        )

        mock_scalars = MagicMock()
        mock_scalars.first.return_value = mock_pulse_run

        mock_file = MagicMock()
        mock_file.id = file_ids[0]
        mock_file.file_path = "/tmp/test.csv"
        mock_file.original_filename = "test.csv"
        mock_file.file_type = "csv"
        mock_file.data_summary = "data"
        mock_file.deep_profile = None
        mock_file_scalars = MagicMock()
        mock_file_scalars.all.return_value = [mock_file]

        call_count = 0
        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            r = MagicMock()
            if call_count == 1:
                r.scalars.return_value = mock_scalars
            else:
                r.scalars.return_value = mock_file_scalars
            return r

        mock_db.execute = AsyncMock(side_effect=mock_execute)

        pipeline_result = {
            "signals_output": [{
                "id": "sig-001", "title": "Test", "severity": "info",
                "category": "trend", "chartType": "bar",
                "analysis_text": "Test", "statistical_evidence": {
                    "metric": "x", "context": "y", "benchmark": "z", "impact": "w"
                }, "chart_data": None,
            }],
            "report_content": "# Report",
            "file_profiles": [{"row_count": 50}],
            "error": "",
        }

        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(return_value=pipeline_result)

        with patch("app.services.pulse.async_session_maker") as mock_session_maker, \
             patch("app.services.pulse.CreditService"), \
             patch("app.services.pulse.build_pulse_graph", return_value=mock_graph), \
             patch("app.services.pulse.Signal"), \
             patch("app.services.pulse.Report"), \
             patch("builtins.open", MagicMock(return_value=MagicMock(
                 __enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value=b"data"))),
                 __exit__=MagicMock(return_value=False),
             ))):
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            asyncio.get_event_loop().run_until_complete(
                PulseService._run_pipeline(
                    pulse_run_id, collection_id, user_id, cost, file_ids, None
                )
            )

        # Verify transitions: profiling -> analyzing -> completed
        assert "profiling" in status_log
        assert "analyzing" in status_log
        assert "completed" in status_log
        # profiling must come before analyzing, analyzing before completed
        assert status_log.index("profiling") < status_log.index("analyzing")
        assert status_log.index("analyzing") < status_log.index("completed")
