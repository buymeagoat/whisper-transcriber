"""
T026 Security Hardening: Database Migration
Add security audit logging and API key management tables.

Revision ID: t026_security_hardening
Revises: [previous_revision]
Create Date: 2024-12-27 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 't026_security_hardening'
down_revision = 'perf_001'
branch_labels = None
depends_on = None

def upgrade():
    """Create security hardening tables for T026."""
    
    # Create enum types
    op.execute("CREATE TYPE audit_event_type AS ENUM ('LOGIN', 'LOGOUT', 'API_ACCESS', 'RATE_LIMIT_HIT', 'SECURITY_VIOLATION', 'FILE_ACCESS', 'ADMIN_ACTION', 'AUTHENTICATION_FAILURE')")
    op.execute("CREATE TYPE audit_severity AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')")
    op.execute("CREATE TYPE api_key_status AS ENUM ('ACTIVE', 'REVOKED', 'EXPIRED')")
    op.execute("CREATE TYPE incident_status AS ENUM ('OPEN', 'INVESTIGATING', 'RESOLVED', 'CLOSED')")
    
    # Create security_audit_logs table
    op.create_table(
        'security_audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('event_type', postgresql.ENUM('LOGIN', 'LOGOUT', 'API_ACCESS', 'RATE_LIMIT_HIT', 'SECURITY_VIOLATION', 'FILE_ACCESS', 'ADMIN_ACTION', 'AUTHENTICATION_FAILURE', name='audit_event_type'), nullable=False),
        sa.Column('severity', postgresql.ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='audit_severity'), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=True),
        sa.Column('client_ip', sa.String(45), nullable=False),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('request_method', sa.String(10), nullable=True),
        sa.Column('request_url', sa.Text(), nullable=True),
        sa.Column('response_status', sa.Integer(), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('event_description', sa.Text(), nullable=False),
        sa.Column('event_details', sa.JSON(), nullable=True),
        sa.Column('risk_score', sa.Integer(), nullable=True),
        sa.Column('blocked', sa.Boolean(), nullable=False, default=False),
        sa.Column('additional_metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for security_audit_logs
    op.create_index('ix_security_audit_logs_timestamp', 'security_audit_logs', ['timestamp'])
    op.create_index('ix_security_audit_logs_event_type', 'security_audit_logs', ['event_type'])
    op.create_index('ix_security_audit_logs_severity', 'security_audit_logs', ['severity'])
    op.create_index('ix_security_audit_logs_user_id', 'security_audit_logs', ['user_id'])
    op.create_index('ix_security_audit_logs_client_ip', 'security_audit_logs', ['client_ip'])
    op.create_index('ix_security_audit_logs_blocked', 'security_audit_logs', ['blocked'])
    op.create_index('ix_security_audit_logs_risk_score', 'security_audit_logs', ['risk_score'])
    
    # Composite indexes for common query patterns
    op.create_index('ix_security_audit_logs_timestamp_severity', 'security_audit_logs', ['timestamp', 'severity'])
    op.create_index('ix_security_audit_logs_user_event_time', 'security_audit_logs', ['user_id', 'event_type', 'timestamp'])
    op.create_index('ix_security_audit_logs_ip_time', 'security_audit_logs', ['client_ip', 'timestamp'])
    
    # Create api_key_audit table
    op.create_table(
        'api_key_audit',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('api_key_hash', sa.String(255), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('event_type', postgresql.ENUM('LOGIN', 'LOGOUT', 'API_ACCESS', 'RATE_LIMIT_HIT', 'SECURITY_VIOLATION', 'FILE_ACCESS', 'ADMIN_ACTION', 'AUTHENTICATION_FAILURE', name='audit_event_type'), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('client_ip', sa.String(45), nullable=False),
        sa.Column('endpoint', sa.String(255), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('rate_limited', sa.Boolean(), nullable=False, default=False),
        sa.Column('additional_data', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for api_key_audit
    op.create_index('ix_api_key_audit_api_key_hash', 'api_key_audit', ['api_key_hash'])
    op.create_index('ix_api_key_audit_user_id', 'api_key_audit', ['user_id'])
    op.create_index('ix_api_key_audit_timestamp', 'api_key_audit', ['timestamp'])
    op.create_index('ix_api_key_audit_event_type', 'api_key_audit', ['event_type'])
    op.create_index('ix_api_key_audit_success', 'api_key_audit', ['success'])
    op.create_index('ix_api_key_audit_rate_limited', 'api_key_audit', ['rate_limited'])
    
    # Composite indexes for API key audit queries
    op.create_index('ix_api_key_audit_key_time', 'api_key_audit', ['api_key_hash', 'timestamp'])
    op.create_index('ix_api_key_audit_user_time', 'api_key_audit', ['user_id', 'timestamp'])
    
    # Create security_incidents table
    op.create_table(
        'security_incidents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('incident_id', sa.String(255), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('severity', postgresql.ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='audit_severity'), nullable=False),
        sa.Column('status', postgresql.ENUM('OPEN', 'INVESTIGATING', 'RESOLVED', 'CLOSED', name='incident_status'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('affected_users', sa.JSON(), nullable=True),
        sa.Column('impact_assessment', sa.Text(), nullable=True),
        sa.Column('remediation_steps', sa.Text(), nullable=True),
        sa.Column('root_cause', sa.Text(), nullable=True),
        sa.Column('related_audit_log_ids', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('incident_id')
    )
    
    # Create indexes for security_incidents
    op.create_index('ix_security_incidents_incident_id', 'security_incidents', ['incident_id'])
    op.create_index('ix_security_incidents_severity', 'security_incidents', ['severity'])
    op.create_index('ix_security_incidents_status', 'security_incidents', ['status'])
    op.create_index('ix_security_incidents_created_at', 'security_incidents', ['created_at'])
    op.create_index('ix_security_incidents_updated_at', 'security_incidents', ['updated_at'])
    
    # Composite indexes for incident queries
    op.create_index('ix_security_incidents_status_severity', 'security_incidents', ['status', 'severity'])
    op.create_index('ix_security_incidents_created_severity', 'security_incidents', ['created_at', 'severity'])
    
    # Create security configuration table for runtime settings
    op.create_table(
        'security_config',
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
    
    # Create indexes for security_config
    op.create_index('ix_security_config_config_key', 'security_config', ['config_key'])
    op.create_index('ix_security_config_updated_at', 'security_config', ['updated_at'])
    
    # Insert default security configuration
    op.execute("""
        INSERT INTO security_config (config_key, config_value, description, created_at, updated_at)
        VALUES 
        ('rate_limits', 
         '{"auth": {"window": 900, "max_requests": 10}, "api": {"window": 3600, "max_requests": 1000}, "upload": {"window": 3600, "max_requests": 100}, "admin": {"window": 300, "max_requests": 50}, "general": {"window": 300, "max_requests": 100}}',
         'Rate limiting configuration for different endpoint types',
         NOW(),
         NOW()),
        ('audit_retention_days',
         '90',
         'Number of days to retain audit logs',
         NOW(),
         NOW()),
        ('max_failed_attempts',
         '5',
         'Maximum failed authentication attempts before account lockout',
         NOW(),
         NOW()),
        ('csrf_token_expiry_hours',
         '24',
         'CSRF token expiry time in hours',
         NOW(),
         NOW()),
        ('api_key_default_expiry_days',
         '365',
         'Default API key expiry time in days',
         NOW(),
         NOW())
    """)

def downgrade():
    """Remove security hardening tables."""
    
    # Drop tables in reverse order
    op.drop_table('security_config')
    op.drop_table('security_incidents')
    op.drop_table('api_key_audit')
    op.drop_table('security_audit_logs')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS incident_status")
    op.execute("DROP TYPE IF EXISTS api_key_status")
    op.execute("DROP TYPE IF EXISTS audit_severity")
    op.execute("DROP TYPE IF EXISTS audit_event_type")