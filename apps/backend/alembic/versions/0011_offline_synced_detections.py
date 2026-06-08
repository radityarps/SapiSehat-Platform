"""offline synced detections

Revision ID: 0011_offline_synced_detections
Revises: 0010_agency_reference
Create Date: 2026-06-08
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0011_offline_synced_detections"
down_revision = "0010_agency_reference"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "offline_synced_detections",
        sa.Column("local_detection_id", sa.String(length=160), primary_key=True),
        sa.Column("sync_status", sa.String(length=40), nullable=False),
        sa.Column("fusion_result_id", sa.String(length=80), nullable=False),
        sa.Column("local_created_at", sa.String(length=80), nullable=False),
        sa.Column("synced_at", sa.String(length=80), nullable=False),
    )
    op.create_index("ix_offline_synced_detections_sync_status", "offline_synced_detections", ["sync_status"])
    op.create_index("ix_offline_synced_detections_fusion_result_id", "offline_synced_detections", ["fusion_result_id"])


def downgrade() -> None:
    op.drop_index("ix_offline_synced_detections_fusion_result_id", table_name="offline_synced_detections")
    op.drop_index("ix_offline_synced_detections_sync_status", table_name="offline_synced_detections")
    op.drop_table("offline_synced_detections")
