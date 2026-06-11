"""farmer preferences and account archive

Revision ID: 0017_farmer_preferences_archive
Revises: 0016_audit_logs
Create Date: 2026-06-10
"""

from alembic import op
import sqlalchemy as sa

revision = "0017_farmer_preferences_archive"
down_revision = "0016_audit_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("accounts", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("accounts", sa.Column("archived_at", sa.String(length=80), nullable=True))
    op.create_table(
        "farmer_preferences",
        sa.Column("farmer_id", sa.String(length=80), primary_key=True),
        sa.Column("scan_result_notifications", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sync_notifications", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("area_risk_advisory_notifications", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("follow_up_status_notifications", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("quiet_hours_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("quiet_hours_start", sa.String(length=8), nullable=False, server_default="21:00"),
        sa.Column("quiet_hours_end", sa.String(length=8), nullable=False, server_default="06:00"),
    )


def downgrade() -> None:
    op.drop_table("farmer_preferences")
    op.drop_column("accounts", "archived_at")
    op.drop_column("accounts", "is_active")
