"""create review run persistence"""

import sqlalchemy as sa
from alembic import op

revision = "0001_review_runs"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "review_runs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("scenario", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_review_runs_status", "review_runs", ["status"])
    op.create_table(
        "review_steps",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("run_id", sa.String(length=36), sa.ForeignKey("review_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_key", sa.String(length=120), nullable=False),
        sa.Column("product", sa.String(length=30), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("resource_id", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("error_code", sa.String(length=100)),
        sa.Column("error_detail", sa.Text()),
    )
    op.create_index("ix_review_steps_run_id", "review_steps", ["run_id"])
    op.create_table(
        "review_event_ledger",
        sa.Column("event_key", sa.String(length=255), primary_key=True),
        sa.Column("state", sa.String(length=20), nullable=False),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_review_event_ledger_state", "review_event_ledger", ["state"])


def downgrade() -> None:
    op.drop_index("ix_review_event_ledger_state", table_name="review_event_ledger")
    op.drop_table("review_event_ledger")
    op.drop_index("ix_review_steps_run_id", table_name="review_steps")
    op.drop_table("review_steps")
    op.drop_index("ix_review_runs_status", table_name="review_runs")
    op.drop_table("review_runs")
