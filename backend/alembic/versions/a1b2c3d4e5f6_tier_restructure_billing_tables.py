"""tier restructure and billing tables

Revision ID: a1b2c3d4e5f6
Revises: 357a798917d0
Create Date: 2026-03-18
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "357a798917d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. subscriptions table
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

    # 5. Add trial_expires_at to users
    op.add_column("users", sa.Column("trial_expires_at", sa.DateTime(timezone=True), nullable=True))

    # 6. Add purchased_balance to user_credits
    op.add_column("user_credits", sa.Column("purchased_balance", sa.Numeric(10, 1), server_default="0", nullable=False))

    # 7. Add balance_pool to credit_transactions
    op.add_column("credit_transactions", sa.Column("balance_pool", sa.String(20), nullable=True))


def downgrade() -> None:
    # Reverse column additions
    op.drop_column("credit_transactions", "balance_pool")
    op.drop_column("user_credits", "purchased_balance")
    op.drop_column("users", "trial_expires_at")

    # Drop tables in reverse order
    op.drop_index("ix_stripe_events_stripe_event_id", table_name="stripe_events")
    op.drop_table("stripe_events")
    op.drop_table("credit_packages")
    op.drop_index("ix_payment_history_user_id", table_name="payment_history")
    op.drop_table("payment_history")
    op.drop_index("ix_subscriptions_stripe_customer_id", table_name="subscriptions")
    op.drop_index("ix_subscriptions_user_id", table_name="subscriptions")
    op.drop_table("subscriptions")
