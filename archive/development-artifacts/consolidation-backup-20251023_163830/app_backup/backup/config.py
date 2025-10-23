# Backup System Configuration
# This file contains the default configuration for the backup and recovery system

import os
from pathlib import Path

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
BACKUP_BASE_DIR = PROJECT_ROOT / "backups"
DATABASE_PATH = PROJECT_ROOT / "app.db"

# Default backup configuration
DEFAULT_BACKUP_CONFIG = {
    # Database backup settings
    "database": {
        "path": str(DATABASE_PATH),
        "enable_wal": True,
        "backup_interval_minutes": 15,  # Full backup every 15 minutes
        "wal_backup_interval_minutes": 5,  # WAL backup every 5 minutes
        "retention_days": 30
    },
    
    # File backup settings
    "files": {
        "watch_directories": [
            str(PROJECT_ROOT / "storage" / "uploads"),
            str(PROJECT_ROOT / "storage" / "transcripts"),
            str(PROJECT_ROOT / "config"),
            str(PROJECT_ROOT / "logs")
        ],
        "enable_realtime": True,
        "backup_interval_minutes": 60,  # Scan for changes every hour
        "retention_days": 30,
        "excluded_patterns": [
            "*.tmp", "*.temp", "*.lock", "*.pyc", "*.pyo",
            "__pycache__", ".pytest_cache", ".git", "node_modules"
        ]
    },
    
    # Compression settings
    "compression": {
        "enabled": True,
        "level": 3,  # Balance between speed and compression ratio
        "use_zstd": True  # Use ZSTD if available, fallback to gzip
    },
    
    # Encryption settings (optional)
    "encryption": {
        "enabled": False,  # Disabled by default for simplicity
        "algorithm": "AES-256-GCM",
        "key_file": str(PROJECT_ROOT / "secrets" / "backup_key.key")
    },
    
    # Storage backends
    "storage_backends": [
        {
            "type": "local",
            "path": str(BACKUP_BASE_DIR / "local_storage"),
            "create_directories": True,
            "primary": True
        }
        # Additional backends can be configured:
        # {
        #     "type": "s3",
        #     "bucket_name": "my-backup-bucket",
        #     "access_key": "AKIAIOSFODNN7EXAMPLE",
        #     "secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        #     "region": "us-east-1",
        #     "endpoint_url": None  # For AWS S3, None for custom endpoints like MinIO
        # },
        # {
        #     "type": "sftp",
        #     "hostname": "backup.example.com",
        #     "username": "backup_user",
        #     "password": "secure_password",  # Or use private_key_path
        #     "port": 22,
        #     "remote_base_path": "/backups/whisper-transcriber"
        # }
    ],
    
    # Backup base directory
    "backup_base_dir": str(BACKUP_BASE_DIR),
    
    # Scheduling settings
    "scheduling": {
        "enabled": True,
        "full_backup_cron": "0 2 * * *",      # Daily at 2 AM
        "incremental_backup_cron": "*/15 * * * *",  # Every 15 minutes
        "cleanup_cron": "0 3 * * 0"           # Weekly cleanup on Sunday at 3 AM
    },
    
    # Monitoring and alerting
    "monitoring": {
        "enabled": True,
        "health_check_interval_minutes": 5,
        "alert_on_failure": True,
        "alert_email": None,  # Set to email address for alerts
        "alert_webhook": None,  # Set to webhook URL for alerts
        "metrics_retention_days": 90
    },
    
    # Recovery settings
    "recovery": {
        "validation_enabled": True,
        "create_recovery_backups": True,
        "test_recovery_frequency_days": 7  # Test recovery procedures weekly
    },
    
    # Performance settings
    "performance": {
        "max_concurrent_backups": 3,
        "io_timeout_seconds": 300,
        "compression_threads": 2,
        "upload_timeout_seconds": 600
    }
}

def get_backup_config():
    """
    Get backup configuration with environment variable overrides.
    
    Returns:
        Dict: Complete backup configuration
    """
    config = DEFAULT_BACKUP_CONFIG.copy()
    
    # Environment variable overrides
    if os.getenv("BACKUP_BASE_DIR"):
        config["backup_base_dir"] = os.getenv("BACKUP_BASE_DIR")
    
    if os.getenv("DATABASE_PATH"):
        config["database"]["path"] = os.getenv("DATABASE_PATH")
    
    if os.getenv("BACKUP_COMPRESSION_ENABLED"):
        config["compression"]["enabled"] = os.getenv("BACKUP_COMPRESSION_ENABLED").lower() == "true"
    
    if os.getenv("BACKUP_ENCRYPTION_ENABLED"):
        config["encryption"]["enabled"] = os.getenv("BACKUP_ENCRYPTION_ENABLED").lower() == "true"
    
    if os.getenv("BACKUP_REALTIME_ENABLED"):
        config["files"]["enable_realtime"] = os.getenv("BACKUP_REALTIME_ENABLED").lower() == "true"
    
    # S3 configuration from environment
    if all([
        os.getenv("S3_BACKUP_BUCKET"),
        os.getenv("S3_ACCESS_KEY"),
        os.getenv("S3_SECRET_KEY")
    ]):
        s3_config = {
            "type": "s3",
            "bucket_name": os.getenv("S3_BACKUP_BUCKET"),
            "access_key": os.getenv("S3_ACCESS_KEY"),
            "secret_key": os.getenv("S3_SECRET_KEY"),
            "region": os.getenv("S3_REGION", "us-east-1"),
            "endpoint_url": os.getenv("S3_ENDPOINT_URL")
        }
        config["storage_backends"].append(s3_config)
    
    # SFTP configuration from environment
    if all([
        os.getenv("SFTP_BACKUP_HOST"),
        os.getenv("SFTP_BACKUP_USER")
    ]):
        sftp_config = {
            "type": "sftp",
            "hostname": os.getenv("SFTP_BACKUP_HOST"),
            "username": os.getenv("SFTP_BACKUP_USER"),
            "password": os.getenv("SFTP_BACKUP_PASSWORD"),
            "private_key_path": os.getenv("SFTP_BACKUP_KEY_PATH"),
            "port": int(os.getenv("SFTP_BACKUP_PORT", "22")),
            "remote_base_path": os.getenv("SFTP_BACKUP_PATH", "/backups")
        }
        config["storage_backends"].append(sftp_config)
    
    return config

def validate_backup_config(config):
    """
    Validate backup configuration.
    
    Args:
        config: Backup configuration dict
        
    Returns:
        Tuple[bool, List[str]]: (is_valid, error_messages)
    """
    errors = []
    
    # Check required paths
    if not config.get("backup_base_dir"):
        errors.append("backup_base_dir is required")
    
    if not config.get("database", {}).get("path"):
        errors.append("database.path is required")
    
    # Check storage backends
    if not config.get("storage_backends"):
        errors.append("At least one storage backend must be configured")
    
    # Validate storage backend configurations
    for i, backend in enumerate(config.get("storage_backends", [])):
        if not backend.get("type"):
            errors.append(f"storage_backends[{i}].type is required")
        
        backend_type = backend.get("type")
        
        if backend_type == "local":
            if not backend.get("path"):
                errors.append(f"storage_backends[{i}].path is required for local backend")
        
        elif backend_type == "s3":
            required_s3_fields = ["bucket_name", "access_key", "secret_key"]
            for field in required_s3_fields:
                if not backend.get(field):
                    errors.append(f"storage_backends[{i}].{field} is required for S3 backend")
        
        elif backend_type == "sftp":
            required_sftp_fields = ["hostname", "username"]
            for field in required_sftp_fields:
                if not backend.get(field):
                    errors.append(f"storage_backends[{i}].{field} is required for SFTP backend")
            
            if not backend.get("password") and not backend.get("private_key_path"):
                errors.append(f"storage_backends[{i}] requires either password or private_key_path")
    
    # Check file watch directories exist
    for watch_dir in config.get("files", {}).get("watch_directories", []):
        if not Path(watch_dir).exists():
            errors.append(f"Watch directory does not exist: {watch_dir}")
    
    return len(errors) == 0, errors
