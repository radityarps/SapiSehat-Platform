"""rate limit requests

Revision ID: 0012_rate_limit_requests
Revises: 0011_offline_synced_detections
Create Date: 2026-06-08
"""

from alembic import op
import sqlalchemy as sa

revision = "0012_rate_limit_requests"
down_revision = "0011_offline_synced_detections"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rate_limit_requests",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("client_key", sa.String(length=160), nullable=False),
        sa.Column("path", sa.String(length=160), nullable=False),
        sa.Column("requested_at", sa.Float(), nullable=False),
    )
    op.create_index("ix_rate_limit_requests_client_key", "rate_limit_requests", ["client_key"])
    op.create_index("ix_rate_limit_requests_path", "rate_limit_requests", ["path"])
    op.create_index("ix_rate_limit_requests_requested_at", "rate_limit_requests", ["requested_at"])


def downgrade() -> None:
    op.drop_index("ix_rate_limit_requests_requested_at", table_name="rate_limit_requests")
    op.drop_index("ix_rate_limit_requests_path", table_name="rate_limit_requests")
    op.drop_index("ix_rate_limit_requests_client_key", table_name="rate_limit_requests")
    op.drop_table("rate_limit_requests")
