"""TDD tests for Wave 1: pulse schemas, service error bodies, and config.

RED phase: these tests document the expected behavior before implementation.
They FAIL until backend/app/schemas/pulse.py, services/pulse.py, and config.py
are updated.
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest


class TestSignalDetailResponse:
    """SignalDetailResponse must serialize Signal ORM objects."""

    def test_signal_detail_response_importable(self):
        from app.schemas.pulse import SignalDetailResponse
        assert SignalDetailResponse is not None

    def test_signal_detail_response_fields(self):
        from app.schemas.pulse import SignalDetailResponse
        now = datetime.now(timezone.utc)
        obj = SignalDetailResponse(
            id=uuid4(),
            title="Outlier Detected",
            severity="critical",
            category="statistical",
            analysis="High z-score",
            evidence={"metric": "z-score"},
            chart_data={"x": [1, 2]},
            chart_type="bar",
            created_at=now,
        )
        assert obj.title == "Outlier Detected"
        assert obj.severity == "critical"

    def test_signal_detail_response_optional_fields(self):
        from app.schemas.pulse import SignalDetailResponse
        now = datetime.now(timezone.utc)
        obj = SignalDetailResponse(
            id=uuid4(),
            title="T",
            severity="info",
            category="general",
            analysis=None,
            evidence=None,
            chart_data=None,
            chart_type=None,
            created_at=now,
        )
        assert obj.analysis is None
        assert obj.chart_data is None

    def test_signal_detail_response_from_attributes(self):
        from app.schemas.pulse import SignalDetailResponse
        from pydantic import ConfigDict
        assert SignalDetailResponse.model_config.get("from_attributes") is True


class TestPulseRunTriggerResponse:
    """PulseRunTriggerResponse is the 202 payload for the trigger endpoint."""

    def test_trigger_response_importable(self):
        from app.schemas.pulse import PulseRunTriggerResponse
        assert PulseRunTriggerResponse is not None

    def test_trigger_response_fields(self):
        from app.schemas.pulse import PulseRunTriggerResponse
        obj = PulseRunTriggerResponse(
            pulse_run_id=uuid4(),
            status="pending",
            credit_cost=5.0,
        )
        assert obj.status == "pending"
        assert obj.credit_cost == 5.0

    def test_trigger_response_from_attributes(self):
        from app.schemas.pulse import PulseRunTriggerResponse
        assert PulseRunTriggerResponse.model_config.get("from_attributes") is True


class TestPulseRunDetailResponseSignals:
    """PulseRunDetailResponse must expose signals: list[SignalDetailResponse]."""

    def test_detail_response_has_signals_field(self):
        from app.schemas.pulse import PulseRunDetailResponse
        fields = PulseRunDetailResponse.model_fields
        assert "signals" in fields

    def test_detail_response_signals_defaults_empty(self):
        from app.schemas.pulse import PulseRunDetailResponse
        now = datetime.now(timezone.utc)
        obj = PulseRunDetailResponse(
            id=uuid4(),
            collection_id=uuid4(),
            status="completed",
            credit_cost=5.0,
            error_message=None,
            started_at=now,
            completed_at=now,
            created_at=now,
            signal_count=0,
        )
        assert obj.signals == []


class TestSettingsPulseOrphanTimeout:
    """Settings must read PULSE_ORPHAN_TIMEOUT_MINUTES from env."""

    def test_pulse_orphan_timeout_minutes_exists(self):
        from app.config import get_settings
        s = get_settings()
        assert hasattr(s, "pulse_orphan_timeout_minutes")

    def test_pulse_orphan_timeout_minutes_default(self):
        from app.config import get_settings
        s = get_settings()
        assert s.pulse_orphan_timeout_minutes == 10


class TestPulseService402Body:
    """run_detection() 402 detail must be a dict with 'required' and 'available'."""

    @pytest.mark.asyncio
    async def test_402_detail_is_dict_with_required_available(self):
        from unittest.mock import AsyncMock, MagicMock, patch
        from decimal import Decimal
        from fastapi import HTTPException
        from app.services.pulse import PulseService

        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()

        # Mock UserCredit with balance
        mock_user_credit = MagicMock()
        mock_user_credit.balance = Decimal("2.0")
        scalars_result = MagicMock()
        scalars_result.first.return_value = mock_user_credit
        execute_result = MagicMock()
        execute_result.scalars.return_value = scalars_result
        db.execute = AsyncMock(return_value=execute_result)

        # Mock deduction fails
        deduct_result = MagicMock()
        deduct_result.success = False
        deduct_result.error_message = "Insufficient credits"

        with (
            patch("app.services.pulse.platform_settings.get", AsyncMock(return_value="5.0")),
            patch("app.services.pulse.CreditService.deduct_credit", AsyncMock(return_value=deduct_result)),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await PulseService.run_detection(
                    db=db,
                    collection_id=uuid4(),
                    user_id=uuid4(),
                    file_ids=[],
                )

        assert exc_info.value.status_code == 402
        detail = exc_info.value.detail
        assert isinstance(detail, dict)
        assert "required" in detail
        assert "available" in detail
        assert detail["required"] == 5.0
        assert detail["available"] == 2.0


class TestPulseService409Body:
    """run_detection() 409 detail must be a dict with 'active_run_id'."""

    @pytest.mark.asyncio
    async def test_409_detail_is_dict_with_active_run_id(self):
        from unittest.mock import AsyncMock, MagicMock, patch
        from decimal import Decimal
        from fastapi import HTTPException
        from uuid import UUID
        from app.services.pulse import PulseService

        run_id = uuid4()
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()

        # First execute call: UserCredit balance query
        mock_user_credit = MagicMock()
        mock_user_credit.balance = Decimal("10.0")
        uc_scalars = MagicMock()
        uc_scalars.first.return_value = mock_user_credit
        uc_result = MagicMock()
        uc_result.scalars.return_value = uc_scalars

        # Second execute call: existing active run query
        mock_run = MagicMock()
        mock_run.id = run_id
        run_scalars = MagicMock()
        run_scalars.first.return_value = mock_run
        run_result = MagicMock()
        run_result.scalars.return_value = run_scalars

        db.execute = AsyncMock(side_effect=[uc_result, run_result])

        deduct_result = MagicMock()
        deduct_result.success = True

        with (
            patch("app.services.pulse.platform_settings.get", AsyncMock(return_value="5.0")),
            patch("app.services.pulse.CreditService.deduct_credit", AsyncMock(return_value=deduct_result)),
            patch("app.services.pulse.CreditService.refund", AsyncMock()),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await PulseService.run_detection(
                    db=db,
                    collection_id=uuid4(),
                    user_id=uuid4(),
                    file_ids=[],
                )

        assert exc_info.value.status_code == 409
        detail = exc_info.value.detail
        assert isinstance(detail, dict)
        assert "active_run_id" in detail
        assert detail["active_run_id"] == str(run_id)
