"""scan image storage notice

Revision ID: 0013_scan_image_storage_notice
Revises: 0012_rate_limit_requests
Create Date: 2026-06-09
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0013_scan_image_storage_notice"
down_revision = "0012_rate_limit_requests"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "farmer_accounts",
        sa.Column("scan_image_storage_notice_accepted", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("farmer_accounts", "scan_image_storage_notice_accepted")
