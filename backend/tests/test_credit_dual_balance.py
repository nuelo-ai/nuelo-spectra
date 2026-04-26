"""Tests for dual-balance CreditService: subscription-first deduction, LIFO refund, sub-only reset.

Covers the dual-balance credit system where:
- Deduction: subscription credits first, then purchased credits
- Refund: LIFO -- refunds to purchased_balance first
- Reset: only resets balance (subscription), purchased_balance untouched
- Balance query: returns purchased_balance and total_balance
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.credit import CreditService
from app.schemas.credit import CreditBalanceResponse


def _make_credit(balance: float = 10.0, purchased_balance: float = 0.0):
    """Create a mock UserCredit with dual balance."""
    credit = MagicMock()
    credit.balance = balance
    credit.purchased_balance = purchased_balance
    credit.last_reset_at = None
    credit.user_id = uuid4()
    return credit


def _make_db_with_credit(credit, user_class="standard"):
    """Create a mock async DB session that returns the given credit on SELECT FOR UPDATE."""
    db = AsyncMock()
    # First call: select User.user_class
    user_class_result = MagicMock()
    user_class_result.scalar_one_or_none.return_value = user_class
    # Second call: select UserCredit with_for_update
    credit_result = MagicMock()
    credit_result.scalar_one_or_none.return_value = credit

    db.execute = AsyncMock(side_effect=[user_class_result, credit_result])
    return db


@pytest.mark.asyncio
class TestDeductCredit:
    """Dual-balance deduction: subscription first, purchased second."""

    async def test_deduct_from_subscription_only(self):
        """cost=5, sub=10, purchased=0: deduct from subscription only, pool=subscription."""
        credit = _make_credit(balance=10.0, purchased_balance=0.0)
        db = _make_db_with_credit(credit, user_class="standard")

        with patch("app.services.credit.get_class_config", return_value={"reset_policy": "none", "credits": 100}):
            result = await CreditService.deduct_credit(db, uuid4(), Decimal("5"))

        assert result.success is True
        assert float(credit.balance) == 5.0
        assert float(credit.purchased_balance) == 0.0

    async def test_deduct_split_across_both_pools(self):
        """cost=15, sub=10, purchased=20: splits deduction, pool=split."""
        credit = _make_credit(balance=10.0, purchased_balance=20.0)
        db = _make_db_with_credit(credit, user_class="standard")

        with patch("app.services.credit.get_class_config", return_value={"reset_policy": "none", "credits": 100}):
            result = await CreditService.deduct_credit(db, uuid4(), Decimal("15"))

        assert result.success is True
        assert float(credit.balance) == 0.0
        assert float(credit.purchased_balance) == 15.0  # 20 - 5

    async def test_deduct_from_purchased_only(self):
        """cost=5, sub=0, purchased=10: deduct from purchased only, pool=purchased."""
        credit = _make_credit(balance=0.0, purchased_balance=10.0)
        db = _make_db_with_credit(credit, user_class="standard")

        with patch("app.services.credit.get_class_config", return_value={"reset_policy": "none", "credits": 100}):
            result = await CreditService.deduct_credit(db, uuid4(), Decimal("5"))

        assert result.success is True
        assert float(credit.balance) == 0.0
        assert float(credit.purchased_balance) == 5.0  # 10 - 5

    async def test_insufficient_total_balance(self):
        """cost=50, sub=10, purchased=20: insufficient, returns failure."""
        credit = _make_credit(balance=10.0, purchased_balance=20.0)
        # For insufficient case, need extra query for User.created_at
        db = AsyncMock()
        user_class_result = MagicMock()
        user_class_result.scalar_one_or_none.return_value = "standard"
        credit_result = MagicMock()
        credit_result.scalar_one_or_none.return_value = credit
        signup_result = MagicMock()
        signup_result.scalar_one_or_none.return_value = None

        db.execute = AsyncMock(side_effect=[user_class_result, credit_result, signup_result])

        with patch("app.services.credit.get_class_config", return_value={"reset_policy": "none", "credits": 100}):
            result = await CreditService.deduct_credit(db, uuid4(), Decimal("50"))

        assert result.success is False


@pytest.mark.asyncio
class TestRefund:
    """LIFO refund: adds to purchased_balance first."""

    async def test_refund_to_purchased_balance(self):
        """Refund amount=5: adds to purchased_balance, pool=purchased."""
        credit = _make_credit(balance=5.0, purchased_balance=0.0)
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = credit
        db.execute = AsyncMock(return_value=result_mock)

        with patch("app.services.credit.get_class_config"):
            await CreditService.refund(db, uuid4(), Decimal("5"))

        # Refund should go to purchased_balance (LIFO)
        assert float(credit.purchased_balance) == 5.0


@pytest.mark.asyncio
class TestExecuteReset:
    """Reset only resets subscription balance; purchased_balance untouched."""

    async def test_reset_only_subscription(self):
        """execute_reset with allocation=100: balance=100, purchased unchanged."""
        credit = _make_credit(balance=20.0, purchased_balance=50.0)
        db = AsyncMock()

        await CreditService.execute_reset(db, credit, allocation=100)

        assert float(credit.balance) == 100.0
        assert float(credit.purchased_balance) == 50.0  # untouched


@pytest.mark.asyncio
class TestGetBalance:
    """Balance query returns purchased_balance and total_balance."""

    async def test_balance_includes_purchased_and_total(self):
        """get_balance returns purchased_balance and total_balance fields."""
        credit = _make_credit(balance=50.0, purchased_balance=25.0)
        db = AsyncMock()
        credit_result = MagicMock()
        credit_result.scalar_one_or_none.return_value = credit
        user_result = MagicMock()
        user_result.scalar_one_or_none.return_value = None  # signup_date

        db.execute = AsyncMock(side_effect=[credit_result, user_result])

        with patch("app.services.credit.get_class_config", return_value={
            "credits": 100, "reset_policy": "none", "display_name": "Standard"
        }), patch("app.services.credit.get_platform_setting", return_value=True):
            result = await CreditService.get_balance(db, uuid4(), "standard")

        assert result.purchased_balance == Decimal("25")
        assert result.total_balance == Decimal("75")
        assert result.monetization_enabled is True


@pytest.mark.asyncio
class TestSchema:
    """CreditBalanceResponse schema includes new fields."""

    async def test_schema_has_purchased_and_total(self):
        """CreditBalanceResponse has purchased_balance and total_balance fields."""
        resp = CreditBalanceResponse(
            balance=Decimal("50"),
            purchased_balance=Decimal("25"),
            total_balance=Decimal("75"),
            tier_allocation=100,
            reset_policy="none",
            next_reset_at=None,
            is_low=False,
            is_unlimited=False,
            display_class="Standard",
        )
        assert resp.purchased_balance == Decimal("25")
        assert resp.total_balance == Decimal("75")
