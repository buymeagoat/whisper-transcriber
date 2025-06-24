from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d99ff9e35597"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "jobs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("original_filename", sa.String(), nullable=False),
        sa.Column("saved_filename", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "queued",
                "processing",
                "completed",
                "failed",
                "stalled",
                name="status_enum",
            ),
            nullable=False,
        ),
        sa.Column("transcript_path", sa.String(), nullable=True),
        sa.Column("log_path", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "metadata",
        sa.Column("job_id", sa.String(), primary_key=True),
        sa.Column("tokens", sa.Integer(), nullable=True),
        sa.Column("duration", sa.Integer(), nullable=True),
        sa.Column("abstract", sa.Text(), nullable=True),
        sa.Column("sample_rate", sa.Integer(), nullable=True),
        sa.Column("generated_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table("metadata")
    op.drop_table("jobs")
