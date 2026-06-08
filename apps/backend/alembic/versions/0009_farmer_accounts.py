"""farmer accounts

Revision ID: 0009_farmer_accounts
Revises: 0008_cattle_timeline_events
Create Date: 2026-06-08
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0009_farmer_accounts"
down_revision = "0008_cattle_timeline_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "farmer_accounts",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("phone_number", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("jurisdiction_id", sa.String(length=120), nullable=False),
        sa.Column("consent_state", sa.String(length=80), nullable=False),
        sa.UniqueConstraint("phone_number", name="uq_farmer_accounts_phone_number"),
    )
    op.create_index("ix_farmer_accounts_phone_number", "farmer_accounts", ["phone_number"])
    op.create_index("ix_farmer_accounts_jurisdiction_id", "farmer_accounts", ["jurisdiction_id"])
    op.create_index("ix_farmer_accounts_consent_state", "farmer_accounts", ["consent_state"])


def downgrade() -> None:
    op.drop_index("ix_farmer_accounts_consent_state", table_name="farmer_accounts")
    op.drop_index("ix_farmer_accounts_jurisdiction_id", table_name="farmer_accounts")
    op.drop_index("ix_farmer_accounts_phone_number", table_name="farmer_accounts")
    op.drop_table("farmer_accounts")
