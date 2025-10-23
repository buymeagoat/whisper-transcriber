"""
T027 Advanced Features: API Key Management Migration
Add API key management tables for developer access.

Revision ID: t027_api_key_management
Revises: t026_security_hardening
Create Date: 2024-12-27 14:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 't027_api_key_management'
down_revision = 't026_security_hardening'
branch_labels = None
depends_on = None

def upgrade():
    """Create API key management tables for T027."""
    
    # Create enum types for API keys
    op.execute("CREATE TYPE api_key_status AS ENUM ('active', 'revoked', 'expired', 'suspended')")
    
    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key_id', sa.String(255), nullable=False),
        sa.Column('key_hash', sa.String(255), nullable=False),
        sa.Column('key_prefix', sa.String(20), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('permissions', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('revoked_by', sa.String(255), nullable=True),
        sa.Column('revoked_reason', sa.Text(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_used_ip', sa.String(45), nullable=True),
        sa.Column('last_used_user_agent', sa.Text(), nullable=True),
        sa.Column('rate_limit_per_hour', sa.Integer(), nullable=True),
        sa.Column('daily_quota', sa.Integer(), nullable=True),
        sa.Column('monthly_quota', sa.Integer(), nullable=True),
        sa.Column('allowed_ips', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_id')
    )
    
    # Create indexes for api_keys
    op.create_index('ix_api_keys_key_id', 'api_keys', ['key_id'])
    op.create_index('ix_api_keys_key_hash', 'api_keys', ['key_hash'])
    op.create_index('ix_api_keys_user_id', 'api_keys', ['user_id'])
    op.create_index('ix_api_keys_status', 'api_keys', ['status'])
    op.create_index('ix_api_keys_expires_at', 'api_keys', ['expires_at'])
    op.create_index('ix_api_keys_last_used_at', 'api_keys', ['last_used_at'])
    
    # Composite indexes for common query patterns
    op.create_index('idx_api_keys_user_status', 'api_keys', ['user_id', 'status'])
    op.create_index('idx_api_keys_expires_status', 'api_keys', ['expires_at', 'status'])
    
    # Create api_key_usage_logs table
    op.create_table(
        'api_key_usage_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('api_key_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('method', sa.String(10), nullable=False),
        sa.Column('endpoint', sa.String(255), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('client_ip', sa.String(45), nullable=False),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('request_size_bytes', sa.Integer(), nullable=True),
        sa.Column('response_size_bytes', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('rate_limited', sa.Boolean(), nullable=False, default=False),
        sa.Column('quota_exceeded', sa.Boolean(), nullable=False, default=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['api_key_id'], ['api_keys.id'], )
    )
    
    # Create indexes for api_key_usage_logs
    op.create_index('ix_api_key_usage_logs_api_key_id', 'api_key_usage_logs', ['api_key_id'])
    op.create_index('ix_api_key_usage_logs_timestamp', 'api_key_usage_logs', ['timestamp'])
    op.create_index('ix_api_key_usage_logs_endpoint', 'api_key_usage_logs', ['endpoint'])
    op.create_index('ix_api_key_usage_logs_status_code', 'api_key_usage_logs', ['status_code'])
    op.create_index('ix_api_key_usage_logs_client_ip', 'api_key_usage_logs', ['client_ip'])
    op.create_index('ix_api_key_usage_logs_rate_limited', 'api_key_usage_logs', ['rate_limited'])
    op.create_index('ix_api_key_usage_logs_quota_exceeded', 'api_key_usage_logs', ['quota_exceeded'])
    
    # Composite indexes for usage logs
    op.create_index('idx_usage_logs_key_time', 'api_key_usage_logs', ['api_key_id', 'timestamp'])
    op.create_index('idx_usage_logs_endpoint_time', 'api_key_usage_logs', ['endpoint', 'timestamp'])
    op.create_index('idx_usage_logs_ip_time', 'api_key_usage_logs', ['client_ip', 'timestamp'])
    
    # Create api_key_quota_usage table
    op.create_table(
        'api_key_quota_usage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('api_key_id', sa.Integer(), nullable=False),
        sa.Column('period_type', sa.String(20), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('request_count', sa.Integer(), nullable=False, default=0),
        sa.Column('success_count', sa.Integer(), nullable=False, default=0),
        sa.Column('error_count', sa.Integer(), nullable=False, default=0),
        sa.Column('total_bytes_uploaded', sa.Integer(), nullable=False, default=0),
        sa.Column('total_bytes_downloaded', sa.Integer(), nullable=False, default=0),
        sa.Column('total_response_time_ms', sa.Integer(), nullable=False, default=0),
        sa.Column('quota_limit', sa.Integer(), nullable=True),
        sa.Column('quota_exceeded', sa.Boolean(), nullable=False, default=False),
        sa.Column('first_quota_exceeded_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['api_key_id'], ['api_keys.id'], )
    )
    
    # Create indexes for api_key_quota_usage
    op.create_index('ix_api_key_quota_usage_api_key_id', 'api_key_quota_usage', ['api_key_id'])
    op.create_index('ix_api_key_quota_usage_period_type', 'api_key_quota_usage', ['period_type'])
    op.create_index('ix_api_key_quota_usage_period_start', 'api_key_quota_usage', ['period_start'])
    op.create_index('ix_api_key_quota_usage_period_end', 'api_key_quota_usage', ['period_end'])
    
    # Composite index for quota usage queries
    op.create_index('idx_quota_usage_key_period', 'api_key_quota_usage', ['api_key_id', 'period_type', 'period_start'])
    
    # Create API key configuration table for system defaults
    op.create_table(
        'api_key_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('config_key', sa.String(255), nullable=False),
        sa.Column('config_value', sa.JSON(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('updated_by', sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('config_key')
    )
    
    # Create indexes for api_key_config
    op.create_index('ix_api_key_config_config_key', 'api_key_config', ['config_key'])
    op.create_index('ix_api_key_config_updated_at', 'api_key_config', ['updated_at'])
    
    # Insert default API key configuration
    op.execute("""
        INSERT INTO api_key_config (config_key, config_value, description, created_at, updated_at)
        VALUES 
        ('default_rate_limit_per_hour',
         '1000',
         'Default rate limit per hour for new API keys',
         NOW(),
         NOW()),
        ('default_expiry_days',
         '365',
         'Default expiration time in days for new API keys',
         NOW(),
         NOW()),
        ('max_keys_per_user',
         '10',
         'Maximum number of API keys per user',
         NOW(),
         NOW()),
        ('available_permissions',
         '["read", "write", "delete", "admin", "batch", "analytics"]',
         'Available permissions for API keys',
         NOW(),
         NOW()),
        ('cleanup_expired_interval_hours',
         '24',
         'Interval in hours for cleaning up expired API keys',
         NOW(),
         NOW())
    """)

def downgrade():
    """Remove API key management tables."""
    
    # Drop tables in reverse order
    op.drop_table('api_key_config')
    op.drop_table('api_key_quota_usage')
    op.drop_table('api_key_usage_logs')
    op.drop_table('api_keys')
    
    # Drop enum type
    op.execute("DROP TYPE IF EXISTS api_key_status")