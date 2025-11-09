"""T035 Convert jobs.user_id to string identifier"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 't035_job_user_id_string'
down_revision = 't034_export_system'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add a non-null string user_id column to jobs."""
    with op.batch_alter_table('jobs') as batch_op:
        batch_op.add_column(
            sa.Column('user_id', sa.String(length=255), nullable=False, server_default='legacy')
        )
        batch_op.create_index('idx_jobs_user_id', ['user_id'])
        batch_op.create_index('idx_jobs_user_status', ['user_id', 'status'])

    # Remove the temporary server default now that existing rows are populated.
    with op.batch_alter_table('jobs') as batch_op:
        batch_op.alter_column('user_id', server_default=None)


def downgrade() -> None:
    """Drop the user_id column and related indexes."""
    with op.batch_alter_table('jobs') as batch_op:
        batch_op.drop_index('idx_jobs_user_status')
        batch_op.drop_index('idx_jobs_user_id')
        batch_op.drop_column('user_id')
