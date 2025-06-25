"""Add started_at and finished_at columns to jobs

Revision ID: 600b2cda9baf
Revises: 127b8323c9f5
Create Date: 2025-06-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "600b2cda9baf"
down_revision: Union[str, None] = "127b8323c9f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add started_at and finished_at columns."""
    op.add_column("jobs", sa.Column("started_at", sa.DateTime(), nullable=True))
    op.add_column("jobs", sa.Column("finished_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Remove started_at and finished_at columns."""
    op.drop_column("jobs", "finished_at")
    op.drop_column("jobs", "started_at")
