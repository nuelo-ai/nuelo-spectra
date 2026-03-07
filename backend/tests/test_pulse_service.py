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


def _mock_db_for_run_detection(db, active_run=None, files=None, credit_balance=Decimal("100")):
    """Configure mock db.execute for run_detection calls.

    Call 1: UserCredit pre-fetch for 402 body
    Call 2: active run check (returns active_run or None)
    Call 3: file query (returns files list)
    """
    # Call 1: UserCredit query
    mock_user_credit = MagicMock()
    mock_user_credit.balance = credit_balance
    mock_uc_scalars = MagicMock()
    mock_uc_scalars.first.return_value = mock_user_credit
    mock_result_uc = MagicMock()
    mock_result_uc.scalars.return_value = mock_uc_scalars

    # Call 2: active run check
    mock_scalars_run = MagicMock()
    mock_scalars_run.first.return_value = active_run
    mock_result_run = MagicMock()
    mock_result_run.scalars.return_value = mock_scalars_run

    # Call 3: file query
    mock_file_scalars = MagicMock()
    mock_file_scalars.all.return_value = files or []
    mock_result_files = MagicMock()
    mock_result_files.scalars.return_value = mock_file_scalars

    call_count = 0
    async def mock_execute(stmt):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return mock_result_uc
        elif call_count == 2:
            return mock_result_run
        else:
            return mock_result_files

    db.execute = AsyncMock(side_effect=mock_execute)


def _mock_db_for_pipeline(db, pulse_run, files):
    """Configure mock db.execute for _run_pipeline calls.

    Call 1: PulseRun load (returns pulse_run)
    Call 2: file query (returns files)
    """
    mock_scalars_run = MagicMock()
    mock_scalars_run.first.return_value = pulse_run
    mock_result_run = MagicMock()
    mock_result_run.scalars.return_value = mock_scalars_run

    mock_file_scalars = MagicMock()
    mock_file_scalars.all.return_value = files
    mock_result_files = MagicMock()
    mock_result_files.scalars.return_value = mock_file_scalars

    call_count = 0
    async def mock_execute(stmt):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return mock_result_run
        else:
            return mock_result_files

    db.execute = AsyncMock(side_effect=mock_execute)


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

        # Configure db.execute to return a mock UserCredit for the pre-fetch
        _mock_db_for_run_detection(db, active_run=None, files=[], credit_balance=Decimal("2"))

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

        mock_file = MagicMock()
        _mock_db_for_run_detection(db, active_run=None, files=[mock_file])

        with patch("app.services.pulse.platform_settings") as mock_ps, \
             patch("app.services.pulse.CreditService") as mock_cs, \
             patch("app.services.pulse.asyncio") as mock_asyncio, \
             patch("app.services.pulse.select") as mock_select:
            mock_ps.get = AsyncMock(return_value="5.0")
            mock_cs.deduct_credit = AsyncMock(return_value=credit_result)
            mock_asyncio.create_task = MagicMock()
            # select() returns a mock that chains .where() etc
            mock_select.return_value = MagicMock()

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

        mock_file = MagicMock()
        _mock_db_for_run_detection(db, active_run=None, files=[mock_file])

        with patch("app.services.pulse.platform_settings") as mock_ps, \
             patch("app.services.pulse.CreditService") as mock_cs, \
             patch("app.services.pulse.asyncio") as mock_asyncio, \
             patch("app.services.pulse.select") as mock_select:
            mock_ps.get = AsyncMock(return_value="5.0")
            mock_cs.deduct_credit = AsyncMock(return_value=credit_result)
            mock_asyncio.create_task = MagicMock()
            mock_select.return_value = MagicMock()

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

        existing_run = MagicMock()
        existing_run.status = "analyzing"
        _mock_db_for_run_detection(db, active_run=existing_run, files=[])

        with patch("app.services.pulse.platform_settings") as mock_ps, \
             patch("app.services.pulse.CreditService") as mock_cs, \
             patch("app.services.pulse.select") as mock_select:
            mock_ps.get = AsyncMock(return_value="5.0")
            mock_cs.deduct_credit = AsyncMock(return_value=credit_result)
            mock_cs.refund = AsyncMock()
            mock_select.return_value = MagicMock()

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

        mock_db = _make_mock_db()

        mock_pulse_run = MagicMock()
        mock_pulse_run.status = "pending"

        mock_file = MagicMock()
        mock_file.id = file_ids[0]
        mock_file.file_path = "/tmp/test.csv"
        mock_file.original_filename = "test.csv"
        mock_file.file_type = "csv"
        mock_file.data_summary = "test data"
        mock_file.deep_profile = None

        _mock_db_for_pipeline(mock_db, mock_pulse_run, [mock_file])

        # Mock build_pulse_graph to raise an error
        mock_graph = MagicMock()
        mock_graph.ainvoke = AsyncMock(side_effect=RuntimeError("Pipeline crashed"))

        with patch("app.services.pulse.async_session_maker") as mock_session_maker, \
             patch("app.services.pulse.CreditService") as mock_cs, \
             patch("app.services.pulse.build_pulse_graph", return_value=mock_graph), \
             patch("app.services.pulse.select") as mock_select, \
             patch("builtins.open", MagicMock(return_value=MagicMock(
                 __enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value=b"data"))),
                 __exit__=MagicMock(return_value=False),
             ))):
            mock_cs.refund = AsyncMock()
            mock_select.return_value = MagicMock()

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

        mock_pulse_run = MagicMock()
        mock_pulse_run.status = "pending"
        mock_pulse_run.collection = MagicMock()
        mock_pulse_run.collection.name = "Test Collection"

        mock_file = MagicMock()
        mock_file.id = file_ids[0]
        mock_file.file_path = "/tmp/test.csv"
        mock_file.original_filename = "test.csv"
        mock_file.file_type = "csv"
        mock_file.data_summary = "test data"
        mock_file.deep_profile = None

        _mock_db_for_pipeline(mock_db, mock_pulse_run, [mock_file])

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
             patch("app.services.pulse.select") as mock_select, \
             patch("builtins.open", MagicMock(return_value=MagicMock(
                 __enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value=b"data"))),
                 __exit__=MagicMock(return_value=False),
             ))):
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_select.return_value = MagicMock()

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

        mock_file = MagicMock()
        mock_file.id = file_ids[0]
        mock_file.file_path = "/tmp/test.csv"
        mock_file.original_filename = "test.csv"
        mock_file.file_type = "csv"
        mock_file.data_summary = "data"
        mock_file.deep_profile = None

        _mock_db_for_pipeline(mock_db, mock_pulse_run, [mock_file])

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
             patch("app.services.pulse.select") as mock_select, \
             patch("builtins.open", MagicMock(return_value=MagicMock(
                 __enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value=b"data"))),
                 __exit__=MagicMock(return_value=False),
             ))):
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_select.return_value = MagicMock()

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

        # Use a simple class to track status transitions
        class StatusTracker:
            def __init__(self):
                self.log = []
                self._status = "pending"

            @property
            def status(self):
                return self._status

            @status.setter
            def status(self, val):
                self.log.append(val)
                self._status = val

        tracker = StatusTracker()

        # Build a MagicMock that delegates status to tracker
        mock_pulse_run = MagicMock()
        mock_pulse_run.collection = MagicMock()
        mock_pulse_run.collection.name = "Test Collection"
        # Wire up status property
        type(mock_pulse_run).status = property(
            lambda self: tracker.status,
            lambda self, val: setattr(tracker, 'status', val),
        )

        mock_file = MagicMock()
        mock_file.id = file_ids[0]
        mock_file.file_path = "/tmp/test.csv"
        mock_file.original_filename = "test.csv"
        mock_file.file_type = "csv"
        mock_file.data_summary = "data"
        mock_file.deep_profile = None

        _mock_db_for_pipeline(mock_db, mock_pulse_run, [mock_file])

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
             patch("app.services.pulse.select") as mock_select, \
             patch("builtins.open", MagicMock(return_value=MagicMock(
                 __enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value=b"data"))),
                 __exit__=MagicMock(return_value=False),
             ))):
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_select.return_value = MagicMock()

            asyncio.get_event_loop().run_until_complete(
                PulseService._run_pipeline(
                    pulse_run_id, collection_id, user_id, cost, file_ids, None
                )
            )

        # Verify transitions: profiling -> analyzing -> completed
        assert "profiling" in tracker.log
        assert "analyzing" in tracker.log
        assert "completed" in tracker.log
        # profiling must come before analyzing, analyzing before completed
        assert tracker.log.index("profiling") < tracker.log.index("analyzing")
        assert tracker.log.index("analyzing") < tracker.log.index("completed")
