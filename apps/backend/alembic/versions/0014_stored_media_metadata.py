"""stored media metadata

Revision ID: 0014_stored_media_metadata
Revises: 0013_scan_image_storage_notice
Create Date: 2026-06-09
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0014_stored_media_metadata"
down_revision = "0013_scan_image_storage_notice"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("stored_media", sa.Column("content_type", sa.String(length=80), nullable=False, server_default="image/jpeg"))
    op.add_column("stored_media", sa.Column("byte_size", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("stored_media", sa.Column("retention_policy", sa.String(length=80), nullable=False, server_default="first_release_monitoring"))
    op.add_column("stored_media", sa.Column("created_at", sa.String(length=80), nullable=False, server_default=""))


def downgrade() -> None:
    op.drop_column("stored_media", "created_at")
    op.drop_column("stored_media", "retention_policy")
    op.drop_column("stored_media", "byte_size")
    op.drop_column("stored_media", "content_type")
