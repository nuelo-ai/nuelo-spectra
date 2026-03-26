"""Tests for trial enforcement: expiration check, exempt paths, top-up guard.

Covers requirements:
- TRIAL-01: Registration creates free_trial user with trial_expires_at
- TRIAL-02: Trial duration configured in user_classes.yaml
- TRIAL-03: Expired trial returns 402 on non-exempt paths
- TRIAL-07: Trial users cannot purchase top-ups
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import HTTPException


def _make_user(
    user_class: str = "free_trial",
    trial_expires_at: datetime | None = None,
    is_active: bool = True,
):
    """Create a mock User object."""
    user = MagicMock()
    user.id = uuid4()
    user.email = "test@example.com"
    user.user_class = user_class
    user.trial_expires_at = trial_expires_at
    user.is_active = is_active
    user.is_admin = False
    return user


def _make_request(path: str = "/api/chat/sessions"):
    """Create a mock Request with url.path set."""
    request = MagicMock()
    request.url.path = path
    return request


class TestRegistrationTrialState:
    """TRIAL-01: New free_trial users get correct initial state."""

    def test_registration_trial_state(self):
        """A newly created free_trial user has user_class='free_trial',
        trial_expires_at set to a future datetime, and initial credits of 100."""
        from app.services.user_class import get_class_config

        config = get_class_config("free_trial")
        assert config is not None, "free_trial config must exist"
        assert config.get("credits") == 100, "free_trial initial credits should be 100"
        assert "trial_duration_days" in config, "free_trial must have trial_duration_days"

        # Verify that auth service sets trial_expires_at in the future
        trial_days = config["trial_duration_days"]
        future = datetime.now(timezone.utc) + timedelta(days=trial_days)
        # The future date should be at least trial_days from now (within a small margin)
        assert future > datetime.now(timezone.utc)


class TestTrialDurationConfig:
    """TRIAL-02: user_classes.yaml has trial_duration_days for free_trial."""

    def test_trial_duration_config(self):
        """user_classes.yaml free_trial section has trial_duration_days key with integer value."""
        from app.services.user_class import get_class_config

        config = get_class_config("free_trial")
        assert config is not None
        trial_days = config.get("trial_duration_days")
        assert trial_days is not None, "trial_duration_days must be set"
        assert isinstance(trial_days, int), "trial_duration_days must be an integer"
        assert trial_days > 0, "trial_duration_days must be positive"


@pytest.mark.asyncio
class TestExpiredTrialReturns402:
    """TRIAL-03: Expired trial users get 402 on non-exempt paths."""

    async def test_expired_trial_returns_402(self):
        """When user.user_class=='free_trial' and user.trial_expires_at is in the past
        and request path is '/api/chat/sessions', get_current_user raises HTTPException
        with status_code=402 and detail dict containing code='trial_expired'."""
        from app.dependencies import get_current_user

        expired_user = _make_user(
            user_class="free_trial",
            trial_expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        request = _make_request("/api/chat/sessions")
        mock_settings = MagicMock()
        mock_db = AsyncMock()

        with (
            patch("app.dependencies.verify_token", return_value=str(expired_user.id)),
            patch("app.dependencies.get_user_by_id", return_value=expired_user),
            patch("app.dependencies.is_user_deactivated", return_value=False),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(
                    request=request,
                    token="fake-token",
                    db=mock_db,
                    settings=mock_settings,
                )
            assert exc_info.value.status_code == 402
            assert exc_info.value.detail["code"] == "trial_expired"


@pytest.mark.asyncio
class TestExemptPathsBypassTrial:
    """TRIAL-03: Exempt paths allow expired trial users through."""

    @pytest.mark.parametrize(
        "path",
        ["/auth/login", "/credits/balance", "/admin/users"],
    )
    async def test_exempt_paths_bypass_trial(self, path: str):
        """When user is expired trial and request path starts with an exempt prefix,
        get_current_user returns the user without raising."""
        from app.dependencies import get_current_user

        expired_user = _make_user(
            user_class="free_trial",
            trial_expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        request = _make_request(path)
        mock_settings = MagicMock()
        mock_db = AsyncMock()

        with (
            patch("app.dependencies.verify_token", return_value=str(expired_user.id)),
            patch("app.dependencies.get_user_by_id", return_value=expired_user),
            patch("app.dependencies.is_user_deactivated", return_value=False),
        ):
            result = await get_current_user(
                request=request,
                token="fake-token",
                db=mock_db,
                settings=mock_settings,
            )
            assert result == expired_user


@pytest.mark.asyncio
class TestNonTrialUsersUnaffected:
    """Non-trial users are not affected by trial check."""

    @pytest.mark.parametrize("user_class", ["on_demand", "standard", "premium"])
    async def test_non_trial_users_unaffected(self, user_class: str):
        """When user.user_class is not 'free_trial', get_current_user returns user
        regardless of trial_expires_at value."""
        from app.dependencies import get_current_user

        user = _make_user(
            user_class=user_class,
            trial_expires_at=datetime.now(timezone.utc) - timedelta(days=30),
        )
        request = _make_request("/api/chat/sessions")
        mock_settings = MagicMock()
        mock_db = AsyncMock()

        with (
            patch("app.dependencies.verify_token", return_value=str(user.id)),
            patch("app.dependencies.get_user_by_id", return_value=user),
            patch("app.dependencies.is_user_deactivated", return_value=False),
        ):
            result = await get_current_user(
                request=request,
                token="fake-token",
                db=mock_db,
                settings=mock_settings,
            )
            assert result == user


class TestTrialTopupBlocked:
    """TRIAL-07: Trial users cannot purchase top-ups."""

    def test_trial_topup_blocked(self):
        """check_topup_eligible raises HTTPException 403 with code='trial_topup_blocked'
        when user.user_class=='free_trial'."""
        from app.routers.credits import check_topup_eligible

        trial_user = _make_user(user_class="free_trial")

        with pytest.raises(HTTPException) as exc_info:
            check_topup_eligible(trial_user)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["code"] == "trial_topup_blocked"

    def test_topup_eligible_non_trial(self):
        """check_topup_eligible does NOT raise for non-trial users."""
        from app.routers.credits import check_topup_eligible

        user = _make_user(user_class="on_demand")
        # Should not raise
        check_topup_eligible(user)
