"""Add config table

Revision ID: f9f3e87495ad
Revises: a664c766e9de
Create Date: 2025-07-05 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f9f3e87495ad"
down_revision: Union[str, None] = "a664c766e9de"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "config",
        sa.Column("key", sa.String(), primary_key=True),
        sa.Column("value", sa.String(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("config")
