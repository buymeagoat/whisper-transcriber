"""
Models package for the whisper-transcriber API.
Contains database models and related classes.
"""

# Import core models from the main models module
from api.models import (
    User, 
    Job, 
    JobStatusEnum, 
    TranscriptMetadata, 
    ConfigEntry, 
    UserSetting, 
    AuditLog, 
    PerformanceMetric, 
    QueryPerformanceLog
)

# Import extended models from submodules
from .api_keys import (
    APIKey,
    APIKeyStatus,
    APIKeyPermission,
    APIKeyUsageLog,
    APIKeyQuotaUsage
)

from .export_system import (
    ExportTemplate,
    ExportJob,
    BatchExport,
    ExportHistory,
    ExportFormatConfig,
    ExportFormat,
    TemplateType,
    ExportStatus,
    BatchExportStatus,
    TranscriptExport  # Alias
)

from .transcript_management import (
    TranscriptVersion,
    TranscriptTag,
    JobTag,
    TranscriptBookmark,
    TranscriptSearchIndex,
    BatchOperation
)

# Export all models for easy importing
__all__ = [
    # Core models
    'User',
    'Job', 
    'JobStatusEnum',
    'TranscriptMetadata',
    'ConfigEntry',
    'UserSetting',
    'AuditLog',
    'PerformanceMetric',
    'QueryPerformanceLog',
    
    # API Key models
    'APIKey',
    'APIKeyStatus', 
    'APIKeyPermission',
    'APIKeyUsageLog',
    'APIKeyQuotaUsage',
    
    # Export system models
    'ExportTemplate',
    'ExportJob', 
    'BatchExport',
    'ExportHistory',
    'ExportFormatConfig',
    'ExportFormat',
    'TemplateType',
    'ExportStatus',
    'BatchExportStatus',
    'TranscriptExport',
    
    # Transcript management models
    'TranscriptVersion',
    'TranscriptTag',
    'JobTag',
    'TranscriptBookmark', 
    'TranscriptSearchIndex',
    'BatchOperation'
]