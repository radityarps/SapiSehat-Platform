"""stored media

Revision ID: 0004_stored_media
Revises: 0003_detection_events
Create Date: 2026-06-08
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0004_stored_media"
down_revision = "0003_detection_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stored_media",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("farmer_id", sa.String(length=80), nullable=False),
        sa.Column("cattle_id", sa.String(length=80), nullable=True),
        sa.Column("detection_id", sa.String(length=80), nullable=True),
        sa.Column("checksum", sa.String(length=160), nullable=False),
        sa.Column("consent_scope", sa.String(length=80), nullable=False),
        sa.Column("storage_reference", sa.String(length=500), nullable=False),
    )
    op.create_index("ix_stored_media_farmer_id", "stored_media", ["farmer_id"])
    op.create_index("ix_stored_media_cattle_id", "stored_media", ["cattle_id"])
    op.create_index("ix_stored_media_detection_id", "stored_media", ["detection_id"])


def downgrade() -> None:
    op.drop_index("ix_stored_media_detection_id", table_name="stored_media")
    op.drop_index("ix_stored_media_cattle_id", table_name="stored_media")
    op.drop_index("ix_stored_media_farmer_id", table_name="stored_media")
    op.drop_table("stored_media")
