"""follow ups

Revision ID: 0006_follow_ups
Revises: 0005_fusion_results
Create Date: 2026-06-08
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0006_follow_ups"
down_revision = "0005_fusion_results"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "follow_ups",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("farmer_id", sa.String(length=80), nullable=False),
        sa.Column("cattle_id", sa.String(length=80), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("public_message", sa.String(length=500), nullable=False),
        sa.Column("internal_notes", sa.String(length=1000), nullable=False),
    )
    op.create_index("ix_follow_ups_farmer_id", "follow_ups", ["farmer_id"])
    op.create_index("ix_follow_ups_cattle_id", "follow_ups", ["cattle_id"])
    op.create_index("ix_follow_ups_status", "follow_ups", ["status"])


def downgrade() -> None:
    op.drop_index("ix_follow_ups_status", table_name="follow_ups")
    op.drop_index("ix_follow_ups_cattle_id", table_name="follow_ups")
    op.drop_index("ix_follow_ups_farmer_id", table_name="follow_ups")
    op.drop_table("follow_ups")
