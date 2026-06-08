"""detection events

Revision ID: 0003_detection_events
Revises: 0002_cattle_profiles
Create Date: 2026-06-08
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0003_detection_events"
down_revision = "0002_cattle_profiles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "detection_events",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("farmer_id", sa.String(length=80), nullable=False),
        sa.Column("cattle_id", sa.String(length=80), nullable=True),
        sa.Column("result_label", sa.String(length=80), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
    )
    op.create_index("ix_detection_events_farmer_id", "detection_events", ["farmer_id"])
    op.create_index("ix_detection_events_cattle_id", "detection_events", ["cattle_id"])


def downgrade() -> None:
    op.drop_index("ix_detection_events_cattle_id", table_name="detection_events")
    op.drop_index("ix_detection_events_farmer_id", table_name="detection_events")
    op.drop_table("detection_events")
