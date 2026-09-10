"""enforce foreign key from agency_users.id to accounts.id

Revision ID: 0021_agency_users_account_fk
Revises: 0020_guide_cms
"""

from __future__ import annotations

from alembic import op


revision = "0021_agency_users_account_fk"
down_revision = "0020_guide_cms"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("agency_users") as batch_op:
        batch_op.create_foreign_key(
            "fk_agency_users_account",
            "accounts",
            ["id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    with op.batch_alter_table("agency_users") as batch_op:
        batch_op.drop_constraint("fk_agency_users_account", type_="foreignkey")
