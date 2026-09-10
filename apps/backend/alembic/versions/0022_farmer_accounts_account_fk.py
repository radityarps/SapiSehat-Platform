"""enforce foreign key from farmer_accounts.id to accounts.id and make phone_number nullable

Revision ID: 0022_farmer_accounts_account_fk
Revises: 0021_agency_users_account_fk
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0022_farmer_accounts_account_fk"
down_revision = "0021_agency_users_account_fk"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("farmer_accounts") as batch_op:
        batch_op.alter_column(
            "phone_number",
            existing_type=sa.String(length=40),
            nullable=True,
        )
        batch_op.create_foreign_key(
            "fk_farmer_accounts_account",
            "accounts",
            ["id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    with op.batch_alter_table("farmer_accounts") as batch_op:
        batch_op.drop_constraint("fk_farmer_accounts_account", type_="foreignkey")
        batch_op.alter_column(
            "phone_number",
            existing_type=sa.String(length=40),
            nullable=False,
        )
