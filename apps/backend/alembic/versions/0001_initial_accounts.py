"""initial accounts

Revision ID: 0001_initial_accounts
Revises:
Create Date: 2026-06-08
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_accounts"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("account_type", sa.String(length=32), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("jurisdiction_id", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=128), nullable=False),
        sa.UniqueConstraint("account_type", "email", name="uq_accounts_type_email"),
    )
    op.create_index("ix_accounts_account_type", "accounts", ["account_type"])
    op.create_index("ix_accounts_email", "accounts", ["email"])
    op.create_index("ix_accounts_jurisdiction_id", "accounts", ["jurisdiction_id"])


def downgrade() -> None:
    op.drop_index("ix_accounts_jurisdiction_id", table_name="accounts")
    op.drop_index("ix_accounts_email", table_name="accounts")
    op.drop_index("ix_accounts_account_type", table_name="accounts")
    op.drop_table("accounts")
