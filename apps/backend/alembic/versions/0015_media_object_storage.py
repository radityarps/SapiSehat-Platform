"""media object storage

Revision ID: 0015_media_object_storage
Revises: 0014_stored_media_metadata
Create Date: 2026-06-09
"""

from alembic import op
import sqlalchemy as sa


revision = "0015_media_object_storage"
down_revision = "0014_stored_media_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("stored_media", sa.Column("storage_backend", sa.String(length=80), nullable=False, server_default="metadata-only"))
    op.add_column("stored_media", sa.Column("object_key", sa.String(length=500), nullable=False, server_default=""))


def downgrade() -> None:
    op.drop_column("stored_media", "object_key")
    op.drop_column("stored_media", "storage_backend")
