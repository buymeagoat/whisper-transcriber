"""Add role column to users

Revision ID: e0c45e6cf3db
Revises: 8f53d7a793bb
Create Date: 2025-06-26
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e0c45e6cf3db"
down_revision: Union[str, None] = "8f53d7a793bb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add role column with default 'user'."""
    op.add_column(
        "users", sa.Column("role", sa.String(), nullable=False, server_default="user")
    )
    op.alter_column("users", "role", server_default=None)


def downgrade() -> None:
    """Remove role column."""
    op.drop_column("users", "role")
