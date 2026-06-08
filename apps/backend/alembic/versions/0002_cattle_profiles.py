"""cattle profiles

Revision ID: 0002_cattle_profiles
Revises: 0001_initial_accounts
Create Date: 2026-06-08
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_cattle_profiles"
down_revision = "0001_initial_accounts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cattle_profiles",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("farmer_id", sa.String(length=80), nullable=False),
        sa.Column("tag", sa.String(length=80), nullable=False),
        sa.Column("sex", sa.String(length=20), nullable=False),
        sa.Column("breed", sa.String(length=120), nullable=False),
        sa.Column("age_months", sa.Integer(), nullable=True),
        sa.Column("birth_year_estimate", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("jurisdiction_id", sa.String(length=120), nullable=False),
    )
    op.create_index("ix_cattle_profiles_farmer_id", "cattle_profiles", ["farmer_id"])
    op.create_index("ix_cattle_profiles_jurisdiction_id", "cattle_profiles", ["jurisdiction_id"])


def downgrade() -> None:
    op.drop_index("ix_cattle_profiles_jurisdiction_id", table_name="cattle_profiles")
    op.drop_index("ix_cattle_profiles_farmer_id", table_name="cattle_profiles")
    op.drop_table("cattle_profiles")
