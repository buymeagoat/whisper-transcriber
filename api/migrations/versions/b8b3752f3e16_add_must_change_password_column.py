"""add must_change_password column to users

Revision ID: b8b3752f3e16
Revises: f9f3e87495ad
Create Date: 2025-07-05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b8b3752f3e16"
down_revision: Union[str, None] = "f9f3e87495ad"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "must_change_password",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.alter_column("users", "must_change_password", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "must_change_password")
