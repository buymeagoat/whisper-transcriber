"""T033: Add Advanced Transcript Management Tables

Revision ID: t033_transcript_management
Revises: t032_system_performance
Create Date: 2024-10-21 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


# revision identifiers, used by Alembic.
revision = 't033_transcript_management'
down_revision = 't027_api_key_management'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add advanced transcript management tables for T033."""
    
    # Create transcript_versions table
    op.create_table('transcript_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.String(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('change_summary', sa.Text(), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_transcript_versions_job_id', 'transcript_versions', ['job_id'])
    op.create_index('idx_transcript_versions_job_id_version', 'transcript_versions', ['job_id', 'version_number'])
    op.create_index('idx_transcript_versions_current', 'transcript_versions', ['job_id', 'is_current'])

    # Create transcript_tags table
    op.create_table('transcript_tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create job_tags table (many-to-many relationship)
    op.create_table('job_tags',
        sa.Column('job_id', sa.String(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.Column('assigned_by', sa.String(), nullable=True),
        sa.Column('assigned_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
        sa.ForeignKeyConstraint(['tag_id'], ['transcript_tags.id'], ),
        sa.PrimaryKeyConstraint('job_id', 'tag_id')
    )
    op.create_index('idx_job_tags_job_id', 'job_tags', ['job_id'])
    op.create_index('idx_job_tags_tag_id', 'job_tags', ['tag_id'])

    # Create transcript_bookmarks table
    op.create_table('transcript_bookmarks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.String(), nullable=False),
        sa.Column('timestamp', sa.Float(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_transcript_bookmarks_job_id', 'transcript_bookmarks', ['job_id'])
    op.create_index('idx_transcript_bookmarks_timestamp', 'transcript_bookmarks', ['job_id', 'timestamp'])

    # Create transcript_search_index table
    op.create_table('transcript_search_index',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.String(), nullable=False),
        sa.Column('content_tokens', sa.Text(), nullable=False),
        sa.Column('keywords', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_id')
    )
    op.create_index('idx_transcript_search_job_id', 'transcript_search_index', ['job_id'])

    # Create batch_operations table
    op.create_table('batch_operations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('operation_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('job_ids', sa.JSON(), nullable=False),
        sa.Column('parameters', sa.JSON(), nullable=True),
        sa.Column('result_data', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_batch_operations_status', 'batch_operations', ['status'])
    op.create_index('idx_batch_operations_type', 'batch_operations', ['operation_type'])
    op.create_index('idx_batch_operations_created', 'batch_operations', ['created_at'])

    # Create transcript_exports table
    op.create_table('transcript_exports',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('job_ids', sa.JSON(), nullable=False),
        sa.Column('export_format', sa.String(length=10), nullable=False),
        sa.Column('export_options', sa.JSON(), nullable=True),
        sa.Column('file_path', sa.String(), nullable=True),
        sa.Column('download_count', sa.Integer(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_transcript_exports_format', 'transcript_exports', ['export_format'])
    op.create_index('idx_transcript_exports_created', 'transcript_exports', ['created_at'])
    op.create_index('idx_transcript_exports_expires', 'transcript_exports', ['expires_at'])

    # Add some default tags
    op.execute("""
        INSERT INTO transcript_tags (name, color, created_at, created_by) VALUES
        ('meeting', '#F59E0B', datetime('now'), 'system'),
        ('interview', '#3B82F6', datetime('now'), 'system'),
        ('lecture', '#EF4444', datetime('now'), 'system'),
        ('conversation', '#10B981', datetime('now'), 'system'),
        ('presentation', '#8B5CF6', datetime('now'), 'system'),
        ('important', '#DC2626', datetime('now'), 'system')
    """)


def downgrade() -> None:
    """Remove advanced transcript management tables."""
    
    # Drop tables in reverse order (to handle foreign key constraints)
    op.drop_table('transcript_exports')
    op.drop_table('batch_operations')
    op.drop_table('transcript_search_index')
    op.drop_table('transcript_bookmarks')
    op.drop_table('job_tags')
    op.drop_table('transcript_tags')
    op.drop_table('transcript_versions')