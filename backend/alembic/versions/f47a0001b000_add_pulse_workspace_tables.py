"""add pulse workspace tables

Revision ID: f47a0001b000
Revises: c1d2e3f4a5b6
Create Date: 2026-03-06
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f47a0001b000"
down_revision = "c1d2e3f4a5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. collections — depends on users
    op.create_table(
        "collections",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_collections_user_id", "collections", ["user_id"])

    # 2. collection_files — depends on collections, files
    op.create_table(
        "collection_files",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("collection_id", sa.UUID(), nullable=False),
        sa.Column("file_id", sa.UUID(), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["collection_id"], ["collections.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_collection_files_collection_id", "collection_files", ["collection_id"]
    )
    op.create_index("ix_collection_files_file_id", "collection_files", ["file_id"])

    # 3. pulse_runs — depends on collections
    op.create_table(
        "pulse_runs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("collection_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("credit_cost", sa.Numeric(10, 1), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["collection_id"], ["collections.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pulse_runs_collection_id", "pulse_runs", ["collection_id"])

    # 4. pulse_run_files — depends on pulse_runs, files (association table)
    op.create_table(
        "pulse_run_files",
        sa.Column("pulse_run_id", sa.UUID(), nullable=False),
        sa.Column("file_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["pulse_run_id"], ["pulse_runs.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("pulse_run_id", "file_id"),
    )

    # 5. signals — depends on collections, pulse_runs
    op.create_table(
        "signals",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("collection_id", sa.UUID(), nullable=False),
        sa.Column("pulse_run_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("analysis", sa.Text(), nullable=True),
        sa.Column("evidence", sa.JSON(), nullable=True),
        sa.Column("chart_data", sa.JSON(), nullable=True),
        sa.Column("chart_type", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["collection_id"], ["collections.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["pulse_run_id"], ["pulse_runs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_signals_collection_id", "signals", ["collection_id"])
    op.create_index("ix_signals_pulse_run_id", "signals", ["pulse_run_id"])

    # 6. reports — depends on collections, pulse_runs
    op.create_table(
        "reports",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("collection_id", sa.UUID(), nullable=False),
        sa.Column("pulse_run_id", sa.UUID(), nullable=True),
        sa.Column("report_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["collection_id"], ["collections.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["pulse_run_id"], ["pulse_runs.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reports_collection_id", "reports", ["collection_id"])
    op.create_index("ix_reports_pulse_run_id", "reports", ["pulse_run_id"])


def downgrade() -> None:
    # Drop in reverse FK-dependency order
    op.drop_table("reports")
    op.drop_table("signals")
    op.drop_table("pulse_run_files")
    op.drop_table("pulse_runs")
    op.drop_table("collection_files")
    op.drop_table("collections")
