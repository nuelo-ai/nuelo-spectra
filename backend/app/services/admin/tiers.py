"""Admin tier change service.

Handles user tier changes with atomic credit reset.
"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.user_credit import UserCredit
from app.services.credit import CreditService
from app.services.user_class import get_class_config


async def change_user_tier(
    db: AsyncSession, user_id: UUID, new_class: str, admin_id: UUID
) -> dict:
    """Change a user's tier and atomically reset their credit balance.

    Args:
        db: Database session (caller manages transaction/commit).
        user_id: UUID of the user to change.
        new_class: New user class name (must exist in user_classes.yaml).
        admin_id: UUID of the admin performing the change.

    Returns:
        Dict with old_class, new_class, and new_balance.

    Raises:
        ValueError: If new_class is unknown or user not found.
    """
    # Validate new class exists
    class_config = get_class_config(new_class)
    if class_config is None:
        raise ValueError(f"Unknown user class: {new_class}")

    # Lock user row for atomic update
    result = await db.execute(
        select(User).where(User.id == user_id).with_for_update()
    )
    user_row = result.scalar_one_or_none()
    if user_row is None:
        raise ValueError("User not found")

    old_class = user_row.user_class
    user_row.user_class = new_class

    # Determine new allocation
    if class_config.get("reset_policy") == "unlimited":
        new_allocation = -1  # sentinel
        new_balance = Decimal("-1")
    else:
        new_allocation = class_config.get("credits", 0)
        new_balance = Decimal(str(new_allocation))

    # Lock and update credit row
    credit_result = await db.execute(
        select(UserCredit).where(UserCredit.user_id == user_id).with_for_update()
    )
    credit = credit_result.scalar_one_or_none()

    if credit is not None:
        if new_allocation == -1:
            # Unlimited tier: set sentinel balance directly
            credit.balance = Decimal("-1")
        else:
            await CreditService.execute_reset(
                db, credit, new_allocation, transaction_type="tier_change"
            )
    else:
        # No credit row exists -- create one
        credit = UserCredit(user_id=user_id, balance=new_balance)
        db.add(credit)
        await db.flush()

    return {
        "old_class": old_class,
        "new_class": new_class,
        "new_balance": float(new_balance),
    }
