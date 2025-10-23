"""T034 Multi-Format Export System Migration

Creates tables for export templates, jobs, batch exports, history, and format configurations.
Supports comprehensive export functionality with customizable templates and batch processing.

Revision ID: t034_export_system
Revises: t033_transcript_management
Create Date: 2025-10-22 02:45:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite
import json
from datetime import datetime


# revision identifiers
revision = 't034_export_system'
down_revision = 't033_transcript_management'
branch_labels = None
depends_on = None


def upgrade():
    """Create export system tables and initialize default configurations."""
    
    # Export Templates table
    op.create_table('export_templates',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('template_type', sa.String(50), nullable=False, index=True),
        sa.Column('supported_formats', sa.JSON(), nullable=False),
        sa.Column('template_config', sa.JSON(), nullable=False),
        sa.Column('styling_config', sa.JSON(), nullable=True),
        sa.Column('layout_config', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.String(255), nullable=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('is_system_template', sa.Boolean(), default=False, nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('usage_count', sa.Integer(), default=0, nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # Export Format Configurations table
    op.create_table('export_format_configs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('format', sa.String(20), nullable=False, unique=True, index=True),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('file_extension', sa.String(10), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('supports_timestamps', sa.Boolean(), default=False, nullable=False),
        sa.Column('supports_styling', sa.Boolean(), default=False, nullable=False),
        sa.Column('supports_metadata', sa.Boolean(), default=False, nullable=False),
        sa.Column('default_config', sa.JSON(), nullable=False),
        sa.Column('validation_schema', sa.JSON(), nullable=True),
        sa.Column('max_file_size_mb', sa.Integer(), default=50, nullable=False),
        sa.Column('processing_timeout_seconds', sa.Integer(), default=300, nullable=False),
        sa.Column('requires_external_tool', sa.Boolean(), default=False, nullable=False),
        sa.Column('external_tool_path', sa.String(500), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now())
    )
    
    # Batch Exports table
    op.create_table('batch_exports',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('export_format', sa.String(20), nullable=False, index=True),
        sa.Column('template_id', sa.Integer(), sa.ForeignKey('export_templates.id'), nullable=True),
        sa.Column('batch_config', sa.JSON(), nullable=True),
        sa.Column('job_ids', sa.JSON(), nullable=False),
        sa.Column('filter_criteria', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(20), default='created', nullable=False, index=True),
        sa.Column('total_jobs', sa.Integer(), nullable=False),
        sa.Column('completed_jobs', sa.Integer(), default=0, nullable=False),
        sa.Column('failed_jobs', sa.Integer(), default=0, nullable=False),
        sa.Column('progress_percentage', sa.Float(), default=0.0, nullable=False),
        sa.Column('archive_filename', sa.String(500), nullable=True),
        sa.Column('archive_path', sa.String(1000), nullable=True),
        sa.Column('archive_size_bytes', sa.Integer(), nullable=True),
        sa.Column('download_url', sa.String(1000), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_duration_seconds', sa.Float(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('partial_success', sa.Boolean(), default=False, nullable=False),
        sa.Column('created_by', sa.String(255), nullable=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # Export Jobs table
    op.create_table('export_jobs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('job_id', sa.String(255), sa.ForeignKey('jobs.id'), nullable=False, index=True),
        sa.Column('batch_export_id', sa.Integer(), sa.ForeignKey('batch_exports.id'), nullable=True, index=True),
        sa.Column('format', sa.String(20), nullable=False, index=True),
        sa.Column('template_id', sa.Integer(), sa.ForeignKey('export_templates.id'), nullable=True),
        sa.Column('custom_config', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(20), default='pending', nullable=False, index=True),
        sa.Column('progress_percentage', sa.Float(), default=0.0, nullable=False),
        sa.Column('output_filename', sa.String(500), nullable=True),
        sa.Column('output_path', sa.String(1000), nullable=True),
        sa.Column('output_size_bytes', sa.Integer(), nullable=True),
        sa.Column('output_url', sa.String(1000), nullable=True),
        sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_duration_seconds', sa.Float(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), default=0, nullable=False),
        sa.Column('max_retries', sa.Integer(), default=3, nullable=False),
        sa.Column('created_by', sa.String(255), nullable=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # Export History table
    op.create_table('export_history',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('export_job_id', sa.Integer(), sa.ForeignKey('export_jobs.id'), nullable=True, index=True),
        sa.Column('batch_export_id', sa.Integer(), sa.ForeignKey('batch_exports.id'), nullable=True, index=True),
        sa.Column('export_type', sa.String(20), nullable=False, index=True),
        sa.Column('format', sa.String(20), nullable=False, index=True),
        sa.Column('template_name', sa.String(255), nullable=True),
        sa.Column('user_id', sa.String(255), nullable=True, index=True),
        sa.Column('user_email', sa.String(255), nullable=True, index=True),
        sa.Column('processing_time_seconds', sa.Float(), nullable=True),
        sa.Column('output_size_bytes', sa.Integer(), nullable=True),
        sa.Column('job_count', sa.Integer(), default=1, nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False, index=True),
        sa.Column('error_type', sa.String(100), nullable=True, index=True),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.Column('exported_at', sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
        sa.Column('downloaded_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # Create indexes for better performance
    op.create_index('idx_export_templates_type_active', 'export_templates', ['template_type', 'is_active'])
    op.create_index('idx_export_templates_system_active', 'export_templates', ['is_system_template', 'is_active'])
    op.create_index('idx_export_jobs_job_format', 'export_jobs', ['job_id', 'format'])
    op.create_index('idx_export_jobs_status_created', 'export_jobs', ['status', 'created_at'])
    op.create_index('idx_batch_exports_status_created', 'batch_exports', ['status', 'created_at'])
    op.create_index('idx_export_history_user_date', 'export_history', ['user_id', 'exported_at'])
    op.create_index('idx_export_history_success_date', 'export_history', ['success', 'exported_at'])


def insert_default_data():
    """Insert default export format configurations and system templates."""
    
    # Create connection for data insertion
    connection = op.get_bind()
    
    # Default export format configurations
    format_configs = [
        {
            'format': 'srt',
            'display_name': 'SubRip Subtitle (SRT)',
            'file_extension': '.srt',
            'mime_type': 'application/x-subrip',
            'supports_timestamps': True,
            'supports_styling': False,
            'supports_metadata': False,
            'default_config': json.dumps({
                'include_timestamps': True,
                'timestamp_format': 'HH:MM:SS,mmm',
                'line_breaks': '\\n',
                'max_line_length': 80,
                'speaker_labels': False,
                'words_per_minute': 150
            }),
            'max_file_size_mb': 10,
            'processing_timeout_seconds': 60,
            'is_enabled': True
        },
        {
            'format': 'vtt',
            'display_name': 'WebVTT Subtitle',
            'file_extension': '.vtt',
            'mime_type': 'text/vtt',
            'supports_timestamps': True,
            'supports_styling': True,
            'supports_metadata': False,
            'default_config': json.dumps({
                'include_timestamps': True,
                'timestamp_format': 'HH:MM:SS.mmm',
                'line_breaks': '\\n',
                'max_line_length': 80,
                'speaker_labels': True,
                'include_header': True,
                'header_text': 'WEBVTT',
                'words_per_minute': 150
            }),
            'max_file_size_mb': 10,
            'processing_timeout_seconds': 60,
            'is_enabled': True
        },
        {
            'format': 'docx',
            'display_name': 'Microsoft Word Document',
            'file_extension': '.docx',
            'mime_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'supports_timestamps': True,
            'supports_styling': True,
            'supports_metadata': True,
            'default_config': json.dumps({
                'include_timestamps': True,
                'include_metadata': True,
                'paragraph_spacing': 1.15,
                'show_speaker_labels': True,
                'timestamp_in_margin': False
            }),
            'max_file_size_mb': 25,
            'processing_timeout_seconds': 120,
            'requires_external_tool': False,
            'is_enabled': True
        },
        {
            'format': 'pdf',
            'display_name': 'Portable Document Format (PDF)',
            'file_extension': '.pdf',
            'mime_type': 'application/pdf',
            'supports_timestamps': True,
            'supports_styling': True,
            'supports_metadata': True,
            'default_config': json.dumps({
                'include_timestamps': True,
                'include_metadata': True,
                'show_speaker_labels': True,
                'page_size': 'letter',
                'font_family': 'Helvetica',
                'font_size': 11
            }),
            'max_file_size_mb': 25,
            'processing_timeout_seconds': 120,
            'requires_external_tool': False,
            'is_enabled': True
        },
        {
            'format': 'json',
            'display_name': 'JSON Structured Data',
            'file_extension': '.json',
            'mime_type': 'application/json',
            'supports_timestamps': True,
            'supports_styling': False,
            'supports_metadata': True,
            'default_config': json.dumps({
                'include_metadata': True,
                'include_timestamps': True,
                'segment_level': 'sentence',
                'include_confidence': True,
                'include_speaker_info': True,
                'pretty_print': True
            }),
            'max_file_size_mb': 50,
            'processing_timeout_seconds': 60,
            'is_enabled': True
        },
        {
            'format': 'txt',
            'display_name': 'Plain Text',
            'file_extension': '.txt',
            'mime_type': 'text/plain',
            'supports_timestamps': True,
            'supports_styling': False,
            'supports_metadata': True,
            'default_config': json.dumps({
                'include_timestamps': True,
                'include_metadata': True,
                'show_speaker_labels': True,
                'line_spacing': 'single'
            }),
            'max_file_size_mb': 10,
            'processing_timeout_seconds': 30,
            'is_enabled': True
        }
    ]
    
    # Insert format configurations
    for config in format_configs:
        connection.execute(
            sa.text("""
                INSERT INTO export_format_configs 
                (format, display_name, file_extension, mime_type, supports_timestamps, 
                 supports_styling, supports_metadata, default_config, max_file_size_mb, 
                 processing_timeout_seconds, requires_external_tool, is_enabled)
                VALUES 
                (:format, :display_name, :file_extension, :mime_type, :supports_timestamps,
                 :supports_styling, :supports_metadata, :default_config, :max_file_size_mb,
                 :processing_timeout_seconds, :requires_external_tool, :is_enabled)
            """),
            **config
        )
    
    # Default system templates
    templates = [
        {
            'name': 'Standard SRT',
            'description': 'Default SRT subtitle template with timestamps',
            'template_type': 'subtitle',
            'supported_formats': json.dumps(['srt']),
            'template_config': json.dumps({
                'include_timestamps': True,
                'timestamp_format': 'HH:MM:SS,mmm',
                'line_breaks': '\\n',
                'max_line_length': 80,
                'speaker_labels': False
            }),
            'is_system_template': True,
            'created_by': 'system'
        },
        {
            'name': 'Standard WebVTT',
            'description': 'Default WebVTT subtitle template with speaker labels',
            'template_type': 'subtitle',
            'supported_formats': json.dumps(['vtt']),
            'template_config': json.dumps({
                'include_timestamps': True,
                'timestamp_format': 'HH:MM:SS.mmm',
                'line_breaks': '\\n',
                'max_line_length': 80,
                'speaker_labels': True,
                'include_header': True,
                'header_text': 'WEBVTT'
            }),
            'is_system_template': True,
            'created_by': 'system'
        },
        {
            'name': 'Standard Document',
            'description': 'Default document template for DOCX and PDF exports',
            'template_type': 'document',
            'supported_formats': json.dumps(['docx', 'pdf']),
            'template_config': json.dumps({
                'include_timestamps': True,
                'include_metadata': True,
                'paragraph_spacing': 1.15,
                'show_speaker_labels': True,
                'timestamp_in_margin': False
            }),
            'styling_config': json.dumps({
                'font_family': 'Calibri',
                'font_size': 11,
                'line_spacing': 1.15,
                'margin_inches': 1.0
            }),
            'is_system_template': True,
            'created_by': 'system'
        },
        {
            'name': 'Structured JSON',
            'description': 'Comprehensive JSON export with all metadata',
            'template_type': 'structured',
            'supported_formats': json.dumps(['json']),
            'template_config': json.dumps({
                'include_metadata': True,
                'include_timestamps': True,
                'segment_level': 'sentence',
                'include_confidence': True,
                'include_speaker_info': True,
                'pretty_print': True
            }),
            'is_system_template': True,
            'created_by': 'system'
        },
        {
            'name': 'Clean Text',
            'description': 'Simple plain text format with optional timestamps',
            'template_type': 'plain_text',
            'supported_formats': json.dumps(['txt']),
            'template_config': json.dumps({
                'include_timestamps': True,
                'include_metadata': True,
                'show_speaker_labels': True,
                'line_spacing': 'single'
            }),
            'is_system_template': True,
            'created_by': 'system'
        }
    ]
    
    # Insert system templates
    for template in templates:
        connection.execute(
            sa.text("""
                INSERT INTO export_templates 
                (name, description, template_type, supported_formats, template_config, 
                 styling_config, is_system_template, created_by)
                VALUES 
                (:name, :description, :template_type, :supported_formats, :template_config,
                 :styling_config, :is_system_template, :created_by)
            """),
            **template
        )


def upgrade():
    """Create export system tables and initialize default configurations."""
    
    # Export Templates table
    op.create_table('export_templates',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('template_type', sa.String(50), nullable=False, index=True),
        sa.Column('supported_formats', sa.JSON(), nullable=False),
        sa.Column('template_config', sa.JSON(), nullable=False),
        sa.Column('styling_config', sa.JSON(), nullable=True),
        sa.Column('layout_config', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.String(255), nullable=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('is_system_template', sa.Boolean(), default=False, nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('usage_count', sa.Integer(), default=0, nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # Export Format Configurations table
    op.create_table('export_format_configs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('format', sa.String(20), nullable=False, unique=True, index=True),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('file_extension', sa.String(10), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('supports_timestamps', sa.Boolean(), default=False, nullable=False),
        sa.Column('supports_styling', sa.Boolean(), default=False, nullable=False),
        sa.Column('supports_metadata', sa.Boolean(), default=False, nullable=False),
        sa.Column('default_config', sa.JSON(), nullable=False),
        sa.Column('validation_schema', sa.JSON(), nullable=True),
        sa.Column('max_file_size_mb', sa.Integer(), default=50, nullable=False),
        sa.Column('processing_timeout_seconds', sa.Integer(), default=300, nullable=False),
        sa.Column('requires_external_tool', sa.Boolean(), default=False, nullable=False),
        sa.Column('external_tool_path', sa.String(500), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now())
    )
    
    # Batch Exports table
    op.create_table('batch_exports',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('export_format', sa.String(20), nullable=False, index=True),
        sa.Column('template_id', sa.Integer(), sa.ForeignKey('export_templates.id'), nullable=True),
        sa.Column('batch_config', sa.JSON(), nullable=True),
        sa.Column('job_ids', sa.JSON(), nullable=False),
        sa.Column('filter_criteria', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(20), default='created', nullable=False, index=True),
        sa.Column('total_jobs', sa.Integer(), nullable=False),
        sa.Column('completed_jobs', sa.Integer(), default=0, nullable=False),
        sa.Column('failed_jobs', sa.Integer(), default=0, nullable=False),
        sa.Column('progress_percentage', sa.Float(), default=0.0, nullable=False),
        sa.Column('archive_filename', sa.String(500), nullable=True),
        sa.Column('archive_path', sa.String(1000), nullable=True),
        sa.Column('archive_size_bytes', sa.Integer(), nullable=True),
        sa.Column('download_url', sa.String(1000), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_duration_seconds', sa.Float(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('partial_success', sa.Boolean(), default=False, nullable=False),
        sa.Column('created_by', sa.String(255), nullable=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # Export Jobs table
    op.create_table('export_jobs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('job_id', sa.String(255), sa.ForeignKey('jobs.id'), nullable=False, index=True),
        sa.Column('batch_export_id', sa.Integer(), sa.ForeignKey('batch_exports.id'), nullable=True, index=True),
        sa.Column('format', sa.String(20), nullable=False, index=True),
        sa.Column('template_id', sa.Integer(), sa.ForeignKey('export_templates.id'), nullable=True),
        sa.Column('custom_config', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(20), default='pending', nullable=False, index=True),
        sa.Column('progress_percentage', sa.Float(), default=0.0, nullable=False),
        sa.Column('output_filename', sa.String(500), nullable=True),
        sa.Column('output_path', sa.String(1000), nullable=True),
        sa.Column('output_size_bytes', sa.Integer(), nullable=True),
        sa.Column('output_url', sa.String(1000), nullable=True),
        sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_duration_seconds', sa.Float(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), default=0, nullable=False),
        sa.Column('max_retries', sa.Integer(), default=3, nullable=False),
        sa.Column('created_by', sa.String(255), nullable=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # Export History table
    op.create_table('export_history',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('export_job_id', sa.Integer(), sa.ForeignKey('export_jobs.id'), nullable=True, index=True),
        sa.Column('batch_export_id', sa.Integer(), sa.ForeignKey('batch_exports.id'), nullable=True, index=True),
        sa.Column('export_type', sa.String(20), nullable=False, index=True),
        sa.Column('format', sa.String(20), nullable=False, index=True),
        sa.Column('template_name', sa.String(255), nullable=True),
        sa.Column('user_id', sa.String(255), nullable=True, index=True),
        sa.Column('user_email', sa.String(255), nullable=True, index=True),
        sa.Column('processing_time_seconds', sa.Float(), nullable=True),
        sa.Column('output_size_bytes', sa.Integer(), nullable=True),
        sa.Column('job_count', sa.Integer(), default=1, nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False, index=True),
        sa.Column('error_type', sa.String(100), nullable=True, index=True),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.Column('exported_at', sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
        sa.Column('downloaded_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # Create indexes for better performance
    op.create_index('idx_export_templates_type_active', 'export_templates', ['template_type', 'is_active'])
    op.create_index('idx_export_templates_system_active', 'export_templates', ['is_system_template', 'is_active'])
    op.create_index('idx_export_jobs_job_format', 'export_jobs', ['job_id', 'format'])
    op.create_index('idx_export_jobs_status_created', 'export_jobs', ['status', 'created_at'])
    op.create_index('idx_batch_exports_status_created', 'batch_exports', ['status', 'created_at'])
    op.create_index('idx_export_history_user_date', 'export_history', ['user_id', 'exported_at'])
    op.create_index('idx_export_history_success_date', 'export_history', ['success', 'exported_at'])
    
    # Insert default data
    insert_default_data()


def downgrade():
    """Reverse the migration."""
    # Drop tables in reverse order (due to foreign key constraints)
    op.drop_table('export_history')
    op.drop_table('export_jobs')
    op.drop_table('batch_exports')
    op.drop_table('export_format_configs')
    op.drop_table('export_templates')