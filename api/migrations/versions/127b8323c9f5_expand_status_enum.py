"""Expand status_enum values

Revision ID: 127b8323c9f5
Revises: e9a7d25a7408
Create Date: 2025-06-24 15:48:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "127b8323c9f5"
down_revision: Union[str, None] = "e9a7d25a7408"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

old_statuses = (
    "queued",
    "processing",
    "completed",
    "failed",
    "stalled",
)

new_statuses = (
    "queued",
    "processing",
    "enriching",
    "completed",
    "failed",
    "stalled",
    "failed_timeout",
    "failed_launch_error",
    "failed_whisper_error",
    "failed_thread_exception",
    "failed_unknown",
)


def upgrade() -> None:
    """Upgrade schema by expanding status_enum."""
    conn = op.get_bind()
    enum_name = "status_enum"
    if conn.dialect.name == "postgresql":
        op.execute(sa.text(f"ALTER TYPE {enum_name} RENAME TO {enum_name}_old"))
        new_enum = postgresql.ENUM(*new_statuses, name=enum_name)
        new_enum.create(bind=conn)
        op.execute(
            sa.text(
                f"ALTER TABLE jobs ALTER COLUMN status TYPE {enum_name} USING status::text::{enum_name}"
            )
        )
        op.execute(sa.text(f"DROP TYPE {enum_name}_old"))
    else:
        with op.batch_alter_table("jobs") as batch:
            batch.alter_column(
                "status",
                type_=sa.Enum(*new_statuses, name=enum_name),
            )


def downgrade() -> None:
    """Downgrade schema by restoring original status_enum."""
    conn = op.get_bind()
    enum_name = "status_enum"
    if conn.dialect.name == "postgresql":
        op.execute(sa.text(f"ALTER TYPE {enum_name} RENAME TO {enum_name}_old"))
        old_enum = postgresql.ENUM(*old_statuses, name=enum_name)
        old_enum.create(bind=conn)
        op.execute(
            sa.text(
                f"ALTER TABLE jobs ALTER COLUMN status TYPE {enum_name} USING status::text::{enum_name}"
            )
        )
        op.execute(sa.text(f"DROP TYPE {enum_name}_old"))
    else:
        with op.batch_alter_table("jobs") as batch:
            batch.alter_column(
                "status",
                type_=sa.Enum(*old_statuses, name=enum_name),
            )
