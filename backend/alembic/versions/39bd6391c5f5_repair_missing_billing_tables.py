"""repair missing billing tables

Repair for a1b2c3d4e5f6 which was stamped but partially applied.
Creates tables and columns that are missing, skipping anything already present.

Revision ID: 39bd6391c5f5
Revises: a1b2c3d4e5f6
Create Date: 2026-03-23 08:54:35.614660

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '39bd6391c5f5'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    insp = inspect(bind)
    return table_name in insp.get_table_names()


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    insp = inspect(bind)
    columns = [c["name"] for c in insp.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    # 1. subscriptions table
    if not _table_exists("subscriptions"):
        op.create_table(
            "subscriptions",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("user_id", sa.UUID(), nullable=False),
            sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
            sa.Column("stripe_customer_id", sa.String(255), nullable=True),
            sa.Column("plan_tier", sa.String(20), nullable=False),
            sa.Column("status", sa.String(30), nullable=False),
            sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
            sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
            sa.Column("cancel_at_period_end", sa.Boolean(), server_default="false", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("stripe_subscription_id"),
            sa.UniqueConstraint("user_id"),
        )
        op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])
        op.create_index("ix_subscriptions_stripe_customer_id", "subscriptions", ["stripe_customer_id"])

    # 2. payment_history table
    if not _table_exists("payment_history"):
        op.create_table(
            "payment_history",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("user_id", sa.UUID(), nullable=False),
            sa.Column("stripe_payment_intent_id", sa.String(255), nullable=True),
            sa.Column("amount_cents", sa.Integer(), nullable=False),
            sa.Column("currency", sa.String(3), server_default="usd", nullable=False),
            sa.Column("payment_type", sa.String(30), nullable=False),
            sa.Column("credit_amount", sa.Numeric(10, 1), nullable=True),
            sa.Column("status", sa.String(30), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("stripe_payment_intent_id"),
        )
        op.create_index("ix_payment_history_user_id", "payment_history", ["user_id"])

    # 3. credit_packages table
    if not _table_exists("credit_packages"):
        op.create_table(
            "credit_packages",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("credit_amount", sa.Integer(), nullable=False),
            sa.Column("price_cents", sa.Integer(), nullable=False),
            sa.Column("stripe_price_id", sa.String(255), nullable=True),
            sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
            sa.Column("display_order", sa.Integer(), server_default="0", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    # 4. stripe_events table
    if not _table_exists("stripe_events"):
        op.create_table(
            "stripe_events",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("stripe_event_id", sa.String(255), nullable=False),
            sa.Column("event_type", sa.String(100), nullable=False),
            sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("stripe_event_id"),
        )
        op.create_index("ix_stripe_events_stripe_event_id", "stripe_events", ["stripe_event_id"])

    # 5. Add balance_pool to credit_transactions (if missing)
    if not _column_exists("credit_transactions", "balance_pool"):
        op.add_column("credit_transactions", sa.Column("balance_pool", sa.String(20), nullable=True))


def downgrade() -> None:
    if _column_exists("credit_transactions", "balance_pool"):
        op.drop_column("credit_transactions", "balance_pool")
    if _table_exists("stripe_events"):
        op.drop_index("ix_stripe_events_stripe_event_id", table_name="stripe_events")
        op.drop_table("stripe_events")
    if _table_exists("credit_packages"):
        op.drop_table("credit_packages")
    if _table_exists("payment_history"):
        op.drop_index("ix_payment_history_user_id", table_name="payment_history")
        op.drop_table("payment_history")
    if _table_exists("subscriptions"):
        op.drop_index("ix_subscriptions_stripe_customer_id", table_name="subscriptions")
        op.drop_index("ix_subscriptions_user_id", table_name="subscriptions")
        op.drop_table("subscriptions")
