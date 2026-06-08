"""agency reference data

Revision ID: 0010_agency_reference
Revises: 0009_farmer_accounts
Create Date: 2026-06-08
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0010_agency_reference"
down_revision = "0009_farmer_accounts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agency_jurisdictions",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("parent_id", sa.String(length=80), nullable=True),
        sa.Column("level", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
    )
    op.create_index("ix_agency_jurisdictions_parent_id", "agency_jurisdictions", ["parent_id"])
    op.create_index("ix_agency_jurisdictions_level", "agency_jurisdictions", ["level"])
    op.create_table(
        "agency_users",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("role", sa.String(length=40), nullable=False),
        sa.Column("jurisdiction_id", sa.String(length=80), nullable=False),
    )
    op.create_index("ix_agency_users_role", "agency_users", ["role"])
    op.create_index("ix_agency_users_jurisdiction_id", "agency_users", ["jurisdiction_id"])


def downgrade() -> None:
    op.drop_index("ix_agency_users_jurisdiction_id", table_name="agency_users")
    op.drop_index("ix_agency_users_role", table_name="agency_users")
    op.drop_table("agency_users")
    op.drop_index("ix_agency_jurisdictions_level", table_name="agency_jurisdictions")
    op.drop_index("ix_agency_jurisdictions_parent_id", table_name="agency_jurisdictions")
    op.drop_table("agency_jurisdictions")
