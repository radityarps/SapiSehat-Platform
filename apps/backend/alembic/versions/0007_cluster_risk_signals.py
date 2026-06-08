"""cluster risk signals

Revision ID: 0007_cluster_risk_signals
Revises: 0006_follow_ups
Create Date: 2026-06-08
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0007_cluster_risk_signals"
down_revision = "0006_follow_ups"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cluster_risk_signals",
        sa.Column("id", sa.String(length=120), primary_key=True),
        sa.Column("jurisdiction_id", sa.String(length=120), nullable=False),
        sa.Column("disease_class", sa.String(length=80), nullable=False),
        sa.Column("signal_count", sa.Integer(), nullable=False),
        sa.Column("window_days", sa.Integer(), nullable=False),
        sa.Column("risk_level", sa.String(length=80), nullable=False),
        sa.Column("priority", sa.String(length=80), nullable=False),
        sa.Column("summary_label", sa.String(length=160), nullable=False),
        sa.Column("source_result_ids", sa.JSON(), nullable=False),
    )
    op.create_index("ix_cluster_risk_signals_jurisdiction_id", "cluster_risk_signals", ["jurisdiction_id"])
    op.create_index("ix_cluster_risk_signals_disease_class", "cluster_risk_signals", ["disease_class"])
    op.create_index("ix_cluster_risk_signals_risk_level", "cluster_risk_signals", ["risk_level"])


def downgrade() -> None:
    op.drop_index("ix_cluster_risk_signals_risk_level", table_name="cluster_risk_signals")
    op.drop_index("ix_cluster_risk_signals_disease_class", table_name="cluster_risk_signals")
    op.drop_index("ix_cluster_risk_signals_jurisdiction_id", table_name="cluster_risk_signals")
    op.drop_table("cluster_risk_signals")
