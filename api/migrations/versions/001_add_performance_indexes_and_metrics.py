"""add_performance_indexes_and_metrics

Revision ID: perf_001
Revises: 
Create Date: 2025-10-14 17:30:00.000000

Add performance optimization indexes and new performance tracking tables
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Index

# revision identifiers
revision = 'perf_001'
down_revision = None  # This is the first migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add performance optimizations and monitoring tables"""
    
    # ────────────────────────────────────────────────────────────────────────────
    # Add new columns to existing tables
    # ────────────────────────────────────────────────────────────────────────────
    
    # Add performance tracking columns to users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_login', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'))
    
    # Add performance tracking columns to jobs table
    with op.batch_alter_table('jobs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('processing_time_seconds', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('file_size_bytes', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('duration_seconds', sa.Float(), nullable=True))
        
        # Add foreign key constraint
        batch_op.create_foreign_key('fk_jobs_user_id', 'users', ['user_id'], ['id'])
    
    # Add tracking columns to config table
    with op.batch_alter_table('config', schema=None) as batch_op:
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=False, 
                                     server_default=sa.text('CURRENT_TIMESTAMP')))
    
    # Add tracking columns to user_settings table
    with op.batch_alter_table('user_settings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=False,
                                     server_default=sa.text('CURRENT_TIMESTAMP')))
    
    # ────────────────────────────────────────────────────────────────────────────
    # Add performance indexes to existing tables
    # ────────────────────────────────────────────────────────────────────────────
    
    # Enhanced indexes for users table
    op.create_index('idx_users_active', 'users', ['is_active'])
    op.create_index('idx_users_created_at', 'users', ['created_at'])
    op.create_index('idx_users_last_login', 'users', ['last_login'])
    op.create_index('idx_users_role_active', 'users', ['role', 'is_active'])
    op.create_index('idx_users_active_created', 'users', ['is_active', 'created_at'])
    
    # Enhanced indexes for jobs table
    op.create_index('idx_jobs_user_id', 'jobs', ['user_id'])
    op.create_index('idx_jobs_user_status', 'jobs', ['user_id', 'status'])
    op.create_index('idx_jobs_user_created', 'jobs', ['user_id', 'created_at'])
    op.create_index('idx_jobs_status_updated', 'jobs', ['status', 'updated_at'])
    op.create_index('idx_jobs_finished_at', 'jobs', ['finished_at'])
    op.create_index('idx_jobs_started_at', 'jobs', ['started_at'])
    op.create_index('idx_jobs_user_status_created', 'jobs', ['user_id', 'status', 'created_at'])
    op.create_index('idx_jobs_status_model_created', 'jobs', ['status', 'model', 'created_at'])
    op.create_index('idx_jobs_created_status_model', 'jobs', ['created_at', 'status', 'model'])
    op.create_index('idx_jobs_processing_time', 'jobs', ['processing_time_seconds'])
    op.create_index('idx_jobs_file_size', 'jobs', ['file_size_bytes'])
    op.create_index('idx_jobs_duration', 'jobs', ['duration_seconds'])
    
    # Enhanced indexes for metadata table
    op.create_index('idx_metadata_language', 'metadata', ['language'])
    op.create_index('idx_metadata_generated_at', 'metadata', ['generated_at'])
    op.create_index('idx_metadata_duration', 'metadata', ['duration'])
    op.create_index('idx_metadata_tokens', 'metadata', ['tokens'])
    op.create_index('idx_metadata_wpm', 'metadata', ['wpm'])
    op.create_index('idx_metadata_sentiment', 'metadata', ['sentiment'])
    op.create_index('idx_metadata_lang_duration', 'metadata', ['language', 'duration'])
    op.create_index('idx_metadata_lang_tokens', 'metadata', ['language', 'tokens'])
    op.create_index('idx_metadata_generated_lang', 'metadata', ['generated_at', 'language'])
    
    # Enhanced indexes for config table
    op.create_index('idx_config_updated_at', 'config', ['updated_at'])
    
    # Enhanced indexes for user_settings table
    op.create_index('idx_user_settings_user_id', 'user_settings', ['user_id'])
    op.create_index('idx_user_settings_key', 'user_settings', ['key'])
    op.create_index('idx_user_settings_updated', 'user_settings', ['updated_at'])
    op.create_index('idx_user_settings_user_key', 'user_settings', ['user_id', 'key'])
    
    # Enhanced indexes for audit_logs table
    op.create_index('idx_audit_endpoint_time', 'audit_logs', ['endpoint', 'timestamp'])
    op.create_index('idx_audit_status_time', 'audit_logs', ['status_code', 'timestamp'])
    op.create_index('idx_audit_method_time', 'audit_logs', ['method', 'timestamp'])
    op.create_index('idx_audit_resource_time', 'audit_logs', ['resource_type', 'timestamp'])
    op.create_index('idx_audit_session_time', 'audit_logs', ['session_id', 'timestamp'])
    op.create_index('idx_audit_ip_event_time', 'audit_logs', ['client_ip', 'event_type', 'timestamp'])
    op.create_index('idx_audit_user_event_time', 'audit_logs', ['user_id', 'event_type', 'timestamp'])
    op.create_index('idx_audit_severity_event_time', 'audit_logs', ['severity', 'event_type', 'timestamp'])
    op.create_index('idx_audit_endpoint_method_time', 'audit_logs', ['endpoint', 'method', 'timestamp'])
    op.create_index('idx_audit_time_status_endpoint', 'audit_logs', ['timestamp', 'status_code', 'endpoint'])
    
    # ────────────────────────────────────────────────────────────────────────────
    # Create new performance monitoring tables
    # ────────────────────────────────────────────────────────────────────────────
    
    # Performance metrics table
    op.create_table('performance_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('metric_type', sa.String(length=50), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=20), nullable=True),
        sa.Column('tags', sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Performance metrics indexes
    op.create_index('idx_perf_timestamp', 'performance_metrics', ['timestamp'])
    op.create_index('idx_perf_metric_type', 'performance_metrics', ['metric_type'])
    op.create_index('idx_perf_metric_name', 'performance_metrics', ['metric_name'])
    op.create_index('idx_perf_type_name', 'performance_metrics', ['metric_type', 'metric_name'])
    op.create_index('idx_perf_time_type', 'performance_metrics', ['timestamp', 'metric_type'])
    op.create_index('idx_perf_name_time', 'performance_metrics', ['metric_name', 'timestamp'])
    op.create_index('idx_perf_value', 'performance_metrics', ['value'])
    op.create_index('idx_perf_type_name_time', 'performance_metrics', ['metric_type', 'metric_name', 'timestamp'])
    
    # Query performance logs table
    op.create_table('query_performance_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('query_type', sa.String(length=50), nullable=False),
        sa.Column('execution_time_ms', sa.Float(), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('table_name', sa.String(length=100), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('endpoint', sa.String(length=200), nullable=True),
        sa.Column('row_count', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Query performance logs indexes
    op.create_index('idx_query_perf_timestamp', 'query_performance_logs', ['timestamp'])
    op.create_index('idx_query_perf_query_type', 'query_performance_logs', ['query_type'])
    op.create_index('idx_query_perf_execution_time', 'query_performance_logs', ['execution_time_ms'])
    op.create_index('idx_query_perf_table_name', 'query_performance_logs', ['table_name'])
    op.create_index('idx_query_perf_user_id', 'query_performance_logs', ['user_id'])
    op.create_index('idx_query_perf_endpoint', 'query_performance_logs', ['endpoint'])
    op.create_index('idx_query_perf_time_duration', 'query_performance_logs', ['timestamp', 'execution_time_ms'])
    op.create_index('idx_query_perf_type_duration', 'query_performance_logs', ['query_type', 'execution_time_ms'])
    op.create_index('idx_query_perf_table_duration', 'query_performance_logs', ['table_name', 'execution_time_ms'])
    op.create_index('idx_query_perf_endpoint_duration', 'query_performance_logs', ['endpoint', 'execution_time_ms'])
    op.create_index('idx_query_perf_user_duration', 'query_performance_logs', ['user_id', 'execution_time_ms'])
    op.create_index('idx_query_perf_slow_queries', 'query_performance_logs', ['execution_time_ms'])


def downgrade() -> None:
    """Remove performance optimizations and monitoring tables"""
    
    # ────────────────────────────────────────────────────────────────────────────
    # Drop new performance monitoring tables
    # ────────────────────────────────────────────────────────────────────────────
    
    op.drop_table('query_performance_logs')
    op.drop_table('performance_metrics')
    
    # ────────────────────────────────────────────────────────────────────────────
    # Drop performance indexes
    # ────────────────────────────────────────────────────────────────────────────
    
    # Drop enhanced audit_logs indexes
    op.drop_index('idx_audit_time_status_endpoint', 'audit_logs')
    op.drop_index('idx_audit_endpoint_method_time', 'audit_logs')
    op.drop_index('idx_audit_severity_event_time', 'audit_logs')
    op.drop_index('idx_audit_user_event_time', 'audit_logs')
    op.drop_index('idx_audit_ip_event_time', 'audit_logs')
    op.drop_index('idx_audit_session_time', 'audit_logs')
    op.drop_index('idx_audit_resource_time', 'audit_logs')
    op.drop_index('idx_audit_method_time', 'audit_logs')
    op.drop_index('idx_audit_status_time', 'audit_logs')
    op.drop_index('idx_audit_endpoint_time', 'audit_logs')
    
    # Drop user_settings indexes
    op.drop_index('idx_user_settings_user_key', 'user_settings')
    op.drop_index('idx_user_settings_updated', 'user_settings')
    op.drop_index('idx_user_settings_key', 'user_settings')
    op.drop_index('idx_user_settings_user_id', 'user_settings')
    
    # Drop config indexes
    op.drop_index('idx_config_updated_at', 'config')
    
    # Drop metadata indexes
    op.drop_index('idx_metadata_generated_lang', 'metadata')
    op.drop_index('idx_metadata_lang_tokens', 'metadata')
    op.drop_index('idx_metadata_lang_duration', 'metadata')
    op.drop_index('idx_metadata_sentiment', 'metadata')
    op.drop_index('idx_metadata_wpm', 'metadata')
    op.drop_index('idx_metadata_tokens', 'metadata')
    op.drop_index('idx_metadata_duration', 'metadata')
    op.drop_index('idx_metadata_generated_at', 'metadata')
    op.drop_index('idx_metadata_language', 'metadata')
    
    # Drop jobs indexes
    op.drop_index('idx_jobs_duration', 'jobs')
    op.drop_index('idx_jobs_file_size', 'jobs')
    op.drop_index('idx_jobs_processing_time', 'jobs')
    op.drop_index('idx_jobs_created_status_model', 'jobs')
    op.drop_index('idx_jobs_status_model_created', 'jobs')
    op.drop_index('idx_jobs_user_status_created', 'jobs')
    op.drop_index('idx_jobs_started_at', 'jobs')
    op.drop_index('idx_jobs_finished_at', 'jobs')
    op.drop_index('idx_jobs_status_updated', 'jobs')
    op.drop_index('idx_jobs_user_created', 'jobs')
    op.drop_index('idx_jobs_user_status', 'jobs')
    op.drop_index('idx_jobs_user_id', 'jobs')
    
    # Drop users indexes
    op.drop_index('idx_users_active_created', 'users')
    op.drop_index('idx_users_role_active', 'users')
    op.drop_index('idx_users_last_login', 'users')
    op.drop_index('idx_users_created_at', 'users')
    op.drop_index('idx_users_active', 'users')
    
    # ────────────────────────────────────────────────────────────────────────────
    # Drop new columns from existing tables
    # ────────────────────────────────────────────────────────────────────────────
    
    # Remove columns from user_settings table
    with op.batch_alter_table('user_settings', schema=None) as batch_op:
        batch_op.drop_column('updated_at')
    
    # Remove columns from config table
    with op.batch_alter_table('config', schema=None) as batch_op:
        batch_op.drop_column('updated_at')
    
    # Remove columns from jobs table
    with op.batch_alter_table('jobs', schema=None) as batch_op:
        batch_op.drop_constraint('fk_jobs_user_id', type_='foreignkey')
        batch_op.drop_column('duration_seconds')
        batch_op.drop_column('file_size_bytes')
        batch_op.drop_column('processing_time_seconds')
        batch_op.drop_column('user_id')
    
    # Remove columns from users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('is_active')
        batch_op.drop_column('last_login')
