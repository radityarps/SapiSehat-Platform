"""cattle timeline events

Revision ID: 0008_cattle_timeline_events
Revises: 0007_cluster_risk_signals
Create Date: 2026-06-08
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0008_cattle_timeline_events"
down_revision = "0007_cluster_risk_signals"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cattle_timeline_events",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("cattle_id", sa.String(length=80), nullable=False),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("event_date", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("creator_id", sa.String(length=80), nullable=False),
    )
    op.create_index("ix_cattle_timeline_events_cattle_id", "cattle_timeline_events", ["cattle_id"])
    op.create_index("ix_cattle_timeline_events_event_type", "cattle_timeline_events", ["event_type"])
    op.create_index("ix_cattle_timeline_events_event_date", "cattle_timeline_events", ["event_date"])


def downgrade() -> None:
    op.drop_index("ix_cattle_timeline_events_event_date", table_name="cattle_timeline_events")
    op.drop_index("ix_cattle_timeline_events_event_type", table_name="cattle_timeline_events")
    op.drop_index("ix_cattle_timeline_events_cattle_id", table_name="cattle_timeline_events")
    op.drop_table("cattle_timeline_events")
