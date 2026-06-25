"""fusion results

Revision ID: 0005_fusion_results
Revises: 0004_stored_media
Create Date: 2026-06-08
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0005_fusion_results"
down_revision = "0004_stored_media"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fusion_results",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("fusion_version", sa.String(length=80), nullable=False),
        sa.Column("inference_mode", sa.String(length=20), nullable=False),
        sa.Column("farmer_id", sa.String(length=80), nullable=False),
        sa.Column("cattle_id", sa.String(length=80), nullable=True),
        sa.Column("disease_class", sa.String(length=80), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("confidence_level", sa.String(length=20), nullable=False),
        sa.Column("reliability", sa.String(length=40), nullable=False),
        sa.Column("handling_advice_key", sa.String(length=160), nullable=False),
        sa.Column("evidence_breakdown", sa.JSON(), nullable=False),
        sa.Column("conflict_status", sa.String(length=80), nullable=False),
        sa.Column("model_versions", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.String(length=80), nullable=False),
    )
    op.create_index("ix_fusion_results_farmer_id", "fusion_results", ["farmer_id"])
    op.create_index("ix_fusion_results_cattle_id", "fusion_results", ["cattle_id"])
    op.create_index("ix_fusion_results_disease_class", "fusion_results", ["disease_class"])
    op.create_index("ix_fusion_results_reliability", "fusion_results", ["reliability"])


def downgrade() -> None:
    op.drop_index("ix_fusion_results_reliability", table_name="fusion_results")
    op.drop_index("ix_fusion_results_disease_class", table_name="fusion_results")
    op.drop_index("ix_fusion_results_cattle_id", table_name="fusion_results")
    op.drop_index("ix_fusion_results_farmer_id", table_name="fusion_results")
    op.drop_table("fusion_results")
