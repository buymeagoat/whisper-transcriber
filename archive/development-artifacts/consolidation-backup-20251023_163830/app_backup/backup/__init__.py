"""
Backup & Recovery System - Core Infrastructure

This module provides enterprise-grade backup and recovery capabilities
for the Whisper Transcriber application, supporting:

- Real-time database backup with SQLite WAL mode
- File system monitoring with immediate backup
- Point-in-time recovery capabilities  
- Multiple storage backends (local, S3, SFTP)
- Compression, encryption, and deduplication
- Automated retention policies
- Monitoring and alerting
"""

try:
    from .orchestrator import BackupOrchestrator
    from .database import DatabaseBackupEngine
    from .files import FileBackupEngine
    from .storage import StorageBackend, LocalStorageBackend, S3StorageBackend
    from .compression import CompressionEngine
    from .recovery import RecoveryManager
    from .service import BackupService, get_backup_service
    from .config import get_backup_config, validate_backup_config

    __all__ = [
        'BackupOrchestrator',
        'DatabaseBackupEngine', 
        'FileBackupEngine',
        'StorageBackend',
        'LocalStorageBackend',
        'S3StorageBackend',
        'CompressionEngine',
        'RecoveryManager',
        'BackupService',
        'get_backup_service',
        'get_backup_config',
        'validate_backup_config',
    ]
except ImportError as e:
    # Graceful degradation if optional dependencies are missing
    import logging
    logging.getLogger(__name__).warning(f"Some backup features unavailable due to missing dependencies: {e}")
    
    __all__ = []
