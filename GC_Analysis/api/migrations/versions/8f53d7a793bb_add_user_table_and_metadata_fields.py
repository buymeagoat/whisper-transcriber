"""Add users table and extra metadata fields

Revision ID: 8f53d7a793bb
Revises: 600b2cda9baf
Create Date: 2025-06-26
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "8f53d7a793bb"
down_revision: Union[str, None] = "600b2cda9baf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create users table and new metadata fields."""
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.add_column("metadata", sa.Column("summary", sa.Text(), nullable=True))
    op.add_column("metadata", sa.Column("language", sa.String(), nullable=True))
    op.add_column("metadata", sa.Column("sentiment", sa.Float(), nullable=True))


def downgrade() -> None:
    """Drop users table and new metadata fields."""
    op.drop_column("metadata", "sentiment")
    op.drop_column("metadata", "language")
    op.drop_column("metadata", "summary")
    op.drop_table("users")
