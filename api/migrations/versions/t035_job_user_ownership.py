"""Add user ownership to transcription jobs

Revision ID: t035_job_user_ownership
Revises: t034_export_system
Create Date: 2025-11-15 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 't035_job_user_ownership'
down_revision = 't034_export_system'
branch_labels = None
depends_on = None


def upgrade():
    """Add user ownership tracking to jobs."""
    op.add_column('jobs', sa.Column('user_id', sa.String(length=255), nullable=True))
    op.create_index('idx_jobs_user_id_created', 'jobs', ['user_id', 'created_at'])


def downgrade():
    """Remove user ownership tracking from jobs."""
    op.drop_index('idx_jobs_user_id_created', table_name='jobs')
    op.drop_column('jobs', 'user_id')
