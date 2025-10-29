"""initial_schema

Revision ID: 000_initial
Revises: 
Create Date: 2025-10-27 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import DateTime, Enum, Integer, String, Text, Float, Boolean, Index


# revision identifiers, used by Alembic.
revision = '000_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('must_change_password', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )
    op.create_index('idx_users_username', 'users', ['username'], unique=False)
    op.create_index('idx_users_role', 'users', ['role'], unique=False)

    # Create jobs table
    op.create_table('jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('original_filename', sa.String(), nullable=False),
        sa.Column('status', sa.Enum('QUEUED', 'PROCESSING', 'ENRICHING', 'COMPLETED', 'FAILED', 'FAILED_TIMEOUT', 'FAILED_LAUNCH_ERROR', 'FAILED_WHISPER_ERROR', 'FAILED_THREAD_EXCEPTION', 'FAILED_UNKNOWN', name='jobstatusenum'), nullable=False),
        sa.Column('whisper_model', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('progress', sa.Float(), nullable=False),
        sa.Column('result_text', sa.Text(), nullable=True),
        sa.Column('result_json', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_jobs_status', 'jobs', ['status'], unique=False)
    op.create_index('idx_jobs_created_at', 'jobs', ['created_at'], unique=False)
    op.create_index('idx_jobs_user_id', 'jobs', ['user_id'], unique=False)

    # Create performance_metrics table (for monitoring)
    op.create_table('performance_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('metric_type', sa.String(), nullable=False),
        sa.Column('metric_name', sa.String(), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(), nullable=True),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_performance_metrics_timestamp', 'performance_metrics', ['timestamp'], unique=False)
    op.create_index('idx_performance_metrics_type', 'performance_metrics', ['metric_type'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_performance_metrics_type', table_name='performance_metrics')
    op.drop_index('idx_performance_metrics_timestamp', table_name='performance_metrics')
    op.drop_table('performance_metrics')
    
    op.drop_index('idx_jobs_user_id', table_name='jobs')
    op.drop_index('idx_jobs_created_at', table_name='jobs')
    op.drop_index('idx_jobs_status', table_name='jobs')
    op.drop_table('jobs')
    
    op.drop_index('idx_users_role', table_name='users')
    op.drop_index('idx_users_username', table_name='users')
    op.drop_table('users')