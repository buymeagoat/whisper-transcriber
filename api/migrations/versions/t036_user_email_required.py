"""T036 Require email addresses for users"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision = "t036_user_email_required"
down_revision = ("schema_cleanup_006", "t035_job_user_id_string")
branch_labels = None
depends_on = None


DEFAULT_ADMIN_EMAIL = "admin@admin.admin"


def _generate_placeholder_email(username: str, user_id: int) -> str:
    """Generate a deterministic placeholder email for existing data."""
    base = (username or f"user{user_id}").strip().lower()
    safe_base = "".join(ch if ch.isalnum() else "-" for ch in base) or f"user{user_id}"
    return f"{safe_base}+{user_id}@local.generated"


def upgrade() -> None:
    """Add the email column, backfill existing rows, and enforce uniqueness."""
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("email", sa.String(length=320), nullable=True))

    conn = op.get_bind()
    results = conn.execute(
        text("SELECT id, username FROM users WHERE email IS NULL OR email = ''")
    ).fetchall()

    for row in results:
        user_id = row.id
        username = row.username or ""

        if username.strip().lower() == "admin":
            email = DEFAULT_ADMIN_EMAIL
        else:
            email = _generate_placeholder_email(username, user_id)

        conn.execute(
            text("UPDATE users SET email = :email WHERE id = :id"),
            {"email": email, "id": user_id},
        )

    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("email", existing_type=sa.String(length=320), nullable=False)
        batch_op.create_index("idx_users_email", ["email"], unique=True)


def downgrade() -> None:
    """Remove the email index and column."""
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_index("idx_users_email")
        batch_op.drop_column("email")
