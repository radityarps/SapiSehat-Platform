"""remove google login support

Revision ID: 0019_remove_google_login
Revises: 0018_postgresql_hardening
Create Date: 2026-06-20
"""

from __future__ import annotations

revision = "0019_remove_google_login"
down_revision = "0018_postgresql_hardening"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Google login used no dedicated database tables or columns."""
    # Endpoint, token verification, and mobile entry point removed in application code.
    # Existing accounts remain normal email/password accounts because provider origin
    # was never stored separately in schema.
    pass


def downgrade() -> None:
    """No schema change to restore."""
    pass
