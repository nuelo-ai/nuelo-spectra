"""CreditService for atomic credit deduction, balance queries, and reset execution."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.credit_transaction import CreditTransaction
from app.models.user import User
from app.models.user_credit import UserCredit
from app.schemas.credit import CreditBalanceResponse, CreditDeductionResult
from app.services.user_class import get_class_config


class CreditService:
    """Service for credit operations: deduction, balance, resets, admin adjustments."""

    @staticmethod
    async def deduct_credit(
        db: AsyncSession, user_id: UUID, cost: Decimal
    ) -> CreditDeductionResult:
        """Atomically deduct credits from a user's balance.

        Uses SELECT FOR UPDATE to lock the credit row during the transaction.
        Unlimited users have transactions logged but no balance deduction.
        Returns failure (not negative balance) when balance < cost.
        """
        # Check if user has unlimited plan
        user_result = await db.execute(
            select(User.user_class).where(User.id == user_id)
        )
        user_class = user_result.scalar_one_or_none()
        if user_class is None:
            return CreditDeductionResult(
                success=False, balance=Decimal("0"), error_message="User not found."
            )

        class_config = get_class_config(user_class)
        if class_config and class_config.get("reset_policy") == "unlimited":
            # Log transaction but don't deduct balance
            transaction = CreditTransaction(
                user_id=user_id,
                amount=-cost,
                balance_after=Decimal("-1"),  # sentinel for unlimited
                transaction_type="usage",
            )
            db.add(transaction)
            await db.flush()
            return CreditDeductionResult(
                success=True, balance=Decimal("-1")
            )

        # Lock the credit row for atomic update
        result = await db.execute(
            select(UserCredit)
            .where(UserCredit.user_id == user_id)
            .with_for_update()
        )
        credit = result.scalar_one_or_none()

        if credit is None:
            return CreditDeductionResult(
                success=False,
                balance=Decimal("0"),
                error_message="No credit record found for user.",
            )

        current_balance = Decimal(str(credit.balance))
        if current_balance < cost:
            # Get user signup date for next reset calculation
            user_row = await db.execute(
                select(User.created_at).where(User.id == user_id)
            )
            signup_date = user_row.scalar_one_or_none()
            reset_policy = class_config["reset_policy"] if class_config else "none"
            next_reset = CreditService._get_next_reset_date(
                signup_date, credit.last_reset_at, reset_policy
            )
            reset_msg = "You're out of credits. Please contact your administrator."
            return CreditDeductionResult(
                success=False,
                balance=current_balance,
                error_message=reset_msg,
                next_reset=next_reset,
            )

        # Deduct and record
        credit.balance = current_balance - cost
        transaction = CreditTransaction(
            user_id=user_id,
            amount=-cost,
            balance_after=credit.balance,
            transaction_type="usage",
        )
        db.add(transaction)
        await db.flush()

        return CreditDeductionResult(
            success=True, balance=Decimal(str(credit.balance))
        )

    @staticmethod
    async def get_balance(
        db: AsyncSession, user_id: UUID, user_class: str
    ) -> CreditBalanceResponse:
        """Get credit balance with tier info and reset date."""
        result = await db.execute(
            select(UserCredit).where(UserCredit.user_id == user_id)
        )
        credit = result.scalar_one_or_none()

        class_config = get_class_config(user_class) or {}
        tier_allocation = class_config.get("credits", 0)
        reset_policy = class_config.get("reset_policy", "none")
        display_name = class_config.get("display_name", user_class)
        is_unlimited = reset_policy == "unlimited"

        if credit is None:
            return CreditBalanceResponse(
                balance=Decimal("-1") if is_unlimited else Decimal("0"),
                tier_allocation=tier_allocation,
                reset_policy=reset_policy,
                next_reset_at=None,
                is_low=False if is_unlimited else True,
                is_unlimited=is_unlimited,
                display_class=display_name,
            )

        balance = Decimal(str(credit.balance))

        # Get signup date for next_reset calculation
        user_result = await db.execute(
            select(User.created_at).where(User.id == user_id)
        )
        signup_date = user_result.scalar_one_or_none()

        next_reset_at = CreditService._get_next_reset_date(
            signup_date, credit.last_reset_at, reset_policy
        )

        # Low credit: balance < 20% of allocation OR balance < 3, whichever triggers first
        if is_unlimited:
            is_low = False
        elif tier_allocation > 0:
            threshold_pct = Decimal(str(tier_allocation)) * Decimal("0.2")
            is_low = balance < threshold_pct or balance < Decimal("3")
        else:
            is_low = balance < Decimal("3")

        return CreditBalanceResponse(
            balance=balance,
            tier_allocation=tier_allocation,
            reset_policy=reset_policy,
            next_reset_at=next_reset_at,
            is_low=is_low,
            is_unlimited=is_unlimited,
            display_class=display_name,
        )

    @staticmethod
    async def admin_adjust(
        db: AsyncSession,
        user_id: UUID,
        amount: Decimal,
        reason: str,
        admin_id: UUID,
    ) -> CreditBalanceResponse:
        """Adjust a user's credit balance (admin operation).

        Locks the credit row, applies adjustment, prevents negative balance.
        """
        result = await db.execute(
            select(UserCredit)
            .where(UserCredit.user_id == user_id)
            .with_for_update()
        )
        credit = result.scalar_one_or_none()
        if credit is None:
            raise ValueError(f"No credit record found for user {user_id}")

        old_balance = Decimal(str(credit.balance))
        new_balance = old_balance + amount
        if new_balance < Decimal("0"):
            new_balance = Decimal("0")

        credit.balance = new_balance

        transaction = CreditTransaction(
            user_id=user_id,
            amount=amount,
            balance_after=new_balance,
            transaction_type="admin_adjustment",
            reason=reason,
            admin_id=admin_id,
        )
        db.add(transaction)
        await db.flush()

        # Return updated balance info
        user_result = await db.execute(
            select(User.user_class).where(User.id == user_id)
        )
        user_class = user_result.scalar_one()
        return await CreditService.get_balance(db, user_id, user_class)

    @staticmethod
    async def refund(
        db: AsyncSession,
        user_id: UUID,
        amount: Decimal,
        reason: str = "API query refund",
    ) -> None:
        """Refund credits to a user (e.g., after failed API analysis).

        Uses SELECT FOR UPDATE for atomicity, same pattern as deduct_credit.
        Creates a CreditTransaction with transaction_type='api_refund'.
        """
        result = await db.execute(
            select(UserCredit).where(UserCredit.user_id == user_id).with_for_update()
        )
        user_credit = result.scalar_one_or_none()
        if user_credit is None:
            return  # No credit record = unlimited user, nothing to refund

        user_credit.balance += amount

        txn = CreditTransaction(
            user_id=user_id,
            amount=amount,
            transaction_type="api_refund",
            reason=reason,
        )
        db.add(txn)
        await db.flush()

    @staticmethod
    async def execute_reset(
        db: AsyncSession,
        credit: UserCredit,
        allocation: int,
        transaction_type: str = "auto_reset",
    ) -> None:
        """Execute a credit reset: set balance to tier allocation and record transaction.

        Always resets to tier allocation, ignoring admin bonuses (per locked decision).
        """
        old_balance = Decimal(str(credit.balance))
        new_balance = Decimal(str(allocation))

        credit.balance = new_balance
        credit.last_reset_at = datetime.now(timezone.utc)

        transaction = CreditTransaction(
            user_id=credit.user_id,
            amount=new_balance - old_balance,
            balance_after=new_balance,
            transaction_type=transaction_type,
        )
        db.add(transaction)
        await db.flush()

    @staticmethod
    async def manual_reset(
        db: AsyncSession, user_id: UUID, admin_id: UUID
    ) -> CreditBalanceResponse:
        """Manually reset a user's credits (admin operation).

        Restarts the user's credit cycle from today.
        """
        result = await db.execute(
            select(UserCredit)
            .where(UserCredit.user_id == user_id)
            .with_for_update()
        )
        credit = result.scalar_one_or_none()
        if credit is None:
            raise ValueError(f"No credit record found for user {user_id}")

        # Get user class and tier config
        user_result = await db.execute(
            select(User.user_class).where(User.id == user_id)
        )
        user_class = user_result.scalar_one()
        class_config = get_class_config(user_class) or {}
        allocation = class_config.get("credits", 0)

        await CreditService.execute_reset(
            db, credit, allocation, transaction_type="manual_reset"
        )

        # Record admin_id on the transaction (execute_reset doesn't set it)
        # Get the most recent transaction we just created
        tx_result = await db.execute(
            select(CreditTransaction)
            .where(CreditTransaction.user_id == user_id)
            .where(CreditTransaction.transaction_type == "manual_reset")
            .order_by(CreditTransaction.created_at.desc())
            .limit(1)
        )
        tx = tx_result.scalar_one_or_none()
        if tx:
            tx.admin_id = admin_id
            await db.flush()

        return await CreditService.get_balance(db, user_id, user_class)

    @staticmethod
    async def get_transaction_history(
        db: AsyncSession, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[CreditTransaction]:
        """Get credit transaction history for a user, newest first."""
        result = await db.execute(
            select(CreditTransaction)
            .where(CreditTransaction.user_id == user_id)
            .order_by(CreditTransaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_credit_distribution(db: AsyncSession) -> list[dict]:
        """Aggregate credit stats grouped by user class.

        Returns count and average balance per class (powers admin dashboard widget).
        """
        result = await db.execute(
            select(
                User.user_class,
                func.count(UserCredit.id).label("user_count"),
                func.avg(UserCredit.balance).label("avg_balance"),
            )
            .join(UserCredit, UserCredit.user_id == User.id)
            .group_by(User.user_class)
        )
        return [
            {
                "user_class": row.user_class,
                "user_count": row.user_count,
                "avg_balance": float(row.avg_balance) if row.avg_balance else 0.0,
            }
            for row in result.all()
        ]

    @staticmethod
    async def get_low_credit_users(
        db: AsyncSession, threshold_pct: float = 0.1
    ) -> list[dict]:
        """Get users whose balance is below threshold percentage of their tier allocation.

        Returns user details with balance info for admin monitoring.
        """
        result = await db.execute(
            select(
                User.id,
                User.email,
                User.user_class,
                UserCredit.balance,
            )
            .join(UserCredit, UserCredit.user_id == User.id)
        )
        rows = result.all()

        low_credit_users = []
        for row in rows:
            class_config = get_class_config(row.user_class)
            if not class_config:
                continue
            if class_config.get("reset_policy") == "unlimited":
                continue
            tier_allocation = class_config.get("credits", 0)
            if tier_allocation <= 0:
                continue
            balance = float(row.balance)
            threshold = tier_allocation * threshold_pct
            if balance < threshold:
                low_credit_users.append(
                    {
                        "user_id": str(row.id),
                        "email": row.email,
                        "balance": balance,
                        "tier_allocation": tier_allocation,
                        "user_class": row.user_class,
                    }
                )

        return low_credit_users

    @staticmethod
    def _get_next_reset_date(
        signup_date: datetime | None,
        last_reset_at: datetime | None,
        reset_policy: str,
    ) -> datetime | None:
        """Calculate the next reset date based on policy and anchor date.

        Rolling reset anchored to signup date or last_reset_at.
        """
        if reset_policy in ("none", "unlimited"):
            return None

        if signup_date is None:
            return None

        anchor = last_reset_at or signup_date
        now = datetime.now(timezone.utc)

        if reset_policy == "weekly":
            period = timedelta(weeks=1)
        elif reset_policy == "monthly":
            period = timedelta(days=30)
        else:
            return None

        next_reset = anchor + period
        # Roll forward until next_reset is in the future
        while next_reset <= now:
            next_reset += period
        return next_reset

    @staticmethod
    def is_reset_due(
        signup_date: datetime | None,
        last_reset_at: datetime | None,
        reset_policy: str,
    ) -> bool:
        """Check if a credit reset is due for a user (used by scheduler).

        Rolling reset: weekly = 7 days, monthly = 30 days from anchor.
        """
        if reset_policy in ("none", "unlimited"):
            return False

        if signup_date is None:
            return False

        now = datetime.now(timezone.utc)
        anchor = last_reset_at or signup_date

        if reset_policy == "weekly":
            return (now - anchor) >= timedelta(weeks=1)
        elif reset_policy == "monthly":
            return (now - anchor) >= timedelta(days=30)

        return False
