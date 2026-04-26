"""add user_id to stripe_events and create discount_codes table

Revision ID: 059_01_admin
Revises: 39bd6391c5f5
Create Date: 2026-03-24 19:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "059_01_admin"
down_revision = "39bd6391c5f5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add user_id column to stripe_events
    op.add_column(
        "stripe_events",
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_stripe_events_user_id", "stripe_events", ["user_id"])

    # Create discount_codes table
    op.create_table(
        "discount_codes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("code", sa.String(50), unique=True, index=True, nullable=False),
        sa.Column("discount_type", sa.String(20), nullable=False),
        sa.Column("discount_value", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), server_default="usd", nullable=False),
        sa.Column("stripe_coupon_id", sa.String(255), nullable=True),
        sa.Column("stripe_promotion_code_id", sa.String(255), nullable=True),
        sa.Column("max_redemptions", sa.Integer(), nullable=True),
        sa.Column("times_redeemed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_by",
            sa.Uuid(),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("discount_codes")
    op.drop_index("ix_stripe_events_user_id", table_name="stripe_events")
    op.drop_column("stripe_events", "user_id")
