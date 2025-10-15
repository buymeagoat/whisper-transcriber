# Backup & Recovery System Documentation

## Overview

The Whisper Transcriber Backup & Recovery System provides comprehensive data protection for the application, including automated database backups, file system monitoring, compression, multiple storage backends, and disaster recovery capabilities.

## Architecture

The backup system consists of several core components:

- **Database Backup Engine** (`/app/backup/database.py`) - SQLite-specialized backup with WAL mode support
- **File Backup Engine** (`/app/backup/files.py`) - Real-time file monitoring and backup with deduplication
- **Compression Engine** (`/app/backup/compression.py`) - High-performance compression with ZSTD and gzip
- **Storage Backends** (`/app/backup/storage.py`) - Local, S3, and SFTP storage abstractions
- **Backup Orchestrator** (`/app/backup/orchestrator.py`) - Central coordination of backup operations
- **Recovery Manager** (`/app/backup/recovery.py`) - Disaster recovery and system restoration
- **Configuration System** (`/app/backup/config.py`) - Environment-based configuration management
- **Backup Service** (`/app/backup/service.py`) - Main service with scheduling and CLI interface
- **API Integration** (`/app/backup_api.py`) - REST API endpoints for backup management

## Features

### Database Protection
- **Zero-downtime backups** using SQLite WAL mode
- **Point-in-time recovery** with transaction-level precision
- **Integrity validation** with automatic corruption detection
- **Incremental backups** for efficient storage utilization

### File System Protection
- **Real-time monitoring** using the `watchdog` library
- **Content-based deduplication** with SHA-256 hashing
- **Selective backup** with configurable include/exclude patterns
- **Atomic operations** to prevent corruption during backup

### Compression & Storage
- **High-performance compression** with ZSTD (fallback to gzip)
- **Multiple storage backends** - local filesystem, S3-compatible, SFTP/SSH
- **Encryption support** with AES-256-GCM (configurable)
- **Bandwidth optimization** with streaming compression

### Scheduling & Automation
- **Flexible scheduling** using cron-like expressions
- **Background service** with signal handling for graceful shutdown
- **Health monitoring** with automated failure notifications
- **Retention policies** with automatic cleanup of expired backups

### Disaster Recovery
- **Full system restoration** from any backup point
- **Selective recovery** for specific files or database tables
- **Validation testing** to ensure backup integrity
- **Recovery time objectives** with measured restoration performance

## Configuration

The backup system is configured through environment variables or configuration files:

### Core Configuration
```bash
# Base backup directory
BACKUP_BASE_DIR=/home/app/backups

# Database configuration
BACKUP_DB_PATH=/home/app/app.db
BACKUP_DB_ENABLE_WAL=true
BACKUP_DB_RETENTION_DAYS=30

# File backup configuration
BACKUP_FILES_SOURCE_DIRS=/home/app/uploads,/home/app/transcripts
BACKUP_FILES_RETENTION_DAYS=30

# Compression settings
BACKUP_COMPRESSION_ENABLED=true
BACKUP_COMPRESSION_USE_ZSTD=true
BACKUP_COMPRESSION_LEVEL=3

# Scheduling
BACKUP_SCHEDULING_ENABLED=true
BACKUP_FULL_SCHEDULE="0 2 * * *"  # Daily at 2 AM
BACKUP_INCREMENTAL_SCHEDULE="0 */6 * * *"  # Every 6 hours
```

### Storage Backend Configuration

#### Local Storage
```bash
BACKUP_STORAGE_LOCAL_ENABLED=true
BACKUP_STORAGE_LOCAL_PATH=/home/app/backup_storage
```

#### S3 Storage
```bash
BACKUP_STORAGE_S3_ENABLED=true
BACKUP_STORAGE_S3_BUCKET=my-backup-bucket
BACKUP_STORAGE_S3_REGION=us-east-1
BACKUP_STORAGE_S3_ACCESS_KEY=your-access-key
BACKUP_STORAGE_S3_SECRET_KEY=your-secret-key
BACKUP_STORAGE_S3_ENDPOINT_URL=https://s3.amazonaws.com  # Optional for custom S3-compatible services
```

#### SFTP Storage
```bash
BACKUP_STORAGE_SFTP_ENABLED=true
BACKUP_STORAGE_SFTP_HOST=backup.example.com
BACKUP_STORAGE_SFTP_PORT=22
BACKUP_STORAGE_SFTP_USERNAME=backup_user
BACKUP_STORAGE_SFTP_PRIVATE_KEY_PATH=/home/app/ssh/backup_key
BACKUP_STORAGE_SFTP_REMOTE_PATH=/backups/whisper-transcriber
```

## API Endpoints

The backup system provides REST API endpoints for management and monitoring:

### Status and Monitoring
- `GET /admin/backup/status` - Comprehensive system status
- `GET /admin/backup/health` - Simple health check for monitoring

### Backup Operations
- `POST /admin/backup/create` - Create manual backup
- `GET /admin/backup/list` - List available backups
- `POST /admin/backup/cleanup` - Clean up expired backups

### Recovery Operations
- `POST /admin/backup/recovery` - Perform system recovery
- `POST /admin/backup/validate-recovery` - Validate recovery state

### Testing and Maintenance
- `POST /admin/backup/test` - Test backup system functionality

## Usage Examples

### Manual Backup Creation
```bash
# Create full backup
curl -X POST http://localhost:8000/admin/backup/create \
  -H "Content-Type: application/json" \
  -d '{"backup_type": "full", "upload_to_storage": true}'

# Create incremental backup
curl -X POST http://localhost:8000/admin/backup/create \
  -H "Content-Type: application/json" \
  -d '{"backup_type": "incremental", "upload_to_storage": true}'
```

### System Recovery
```bash
# Database recovery from specific backup
curl -X POST http://localhost:8000/admin/backup/recovery \
  -H "Content-Type: application/json" \
  -d '{
    "recovery_type": "database",
    "backup_id": "full_20251015_143000",
    "restore_to_original": true
  }'

# Point-in-time recovery
curl -X POST http://localhost:8000/admin/backup/recovery \
  -H "Content-Type: application/json" \
  -d '{
    "recovery_type": "database",
    "point_in_time": "2025-10-15T14:30:00",
    "restore_to_original": true
  }'

# File recovery with patterns
curl -X POST http://localhost:8000/admin/backup/recovery \
  -H "Content-Type: application/json" \
  -d '{
    "recovery_type": "files",
    "file_patterns": ["*.wav", "*.mp3"],
    "restore_to_original": false,
    "target_directory": "/tmp/recovered_audio"
  }'
```

### System Status Check
```bash
# Get detailed status
curl http://localhost:8000/admin/backup/status

# Simple health check
curl http://localhost:8000/admin/backup/health
```

## Command Line Interface

The backup service can also be controlled via command line:

```bash
# Start backup service with scheduling
python -m app.backup.service start

# Create manual backup
python -m app.backup.service backup --type full

# List available backups
python -m app.backup.service list

# Perform recovery
python -m app.backup.service recover --type database --backup-id full_20251015_143000

# Test backup system
python -m app.backup.service test

# Stop backup service
python -m app.backup.service stop
```

## Monitoring and Alerting

The backup system provides comprehensive monitoring capabilities:

### Health Checks
- Service availability and status
- Storage backend connectivity
- Backup success/failure rates
- Disk space utilization
- Recovery validation results

### Failure Notifications
- Failed backup operations
- Storage backend connectivity issues
- Disk space warnings
- Configuration validation errors
- Recovery operation failures

### Performance Metrics
- Backup duration and throughput
- Compression ratios
- Storage utilization
- Recovery time objectives
- Deduplication efficiency

## Security Considerations

### Encryption
- Backups can be encrypted using AES-256-GCM
- Encryption keys should be stored separately from backups
- Key rotation is supported for enhanced security

### Access Control
- API endpoints require admin authentication
- Storage backend credentials should be properly secured
- File system permissions should restrict backup access

### Network Security
- SFTP connections use SSH key authentication
- S3 connections use HTTPS with proper SSL/TLS
- All data transmission is encrypted in transit

## Disaster Recovery Procedures

### Recovery Time Objectives (RTO)
- Database recovery: < 5 minutes for full restoration
- File recovery: < 15 minutes for selective restoration
- Full system recovery: < 30 minutes for complete restoration

### Recovery Point Objectives (RPO)
- Database: < 15 minutes (with incremental WAL backups)
- Files: < 1 hour (with real-time monitoring)
- Full system: < 6 hours (with scheduled full backups)

### Testing and Validation
- Automated backup validation on creation
- Regular recovery testing (monthly recommended)
- Integrity checks on all backup files
- Performance benchmarking for recovery operations

## Troubleshooting

### Common Issues

#### Permission Errors
```bash
# Ensure proper directory permissions
chmod 755 /home/app/backups
chown app:app /home/app/backups
```

#### Storage Backend Connectivity
```bash
# Test S3 connectivity
aws s3 ls s3://your-backup-bucket/

# Test SFTP connectivity
sftp -i /path/to/key user@backup-server
```

#### Database Lock Issues
```bash
# Check for long-running transactions
sqlite3 /path/to/database.db "PRAGMA busy_timeout=30000;"
```

### Log Files
- Application logs: `/home/app/logs/backup.log`
- Service logs: Check systemd journal for service-related issues
- Storage logs: Individual backend logs in backup directories

### Performance Optimization
- Adjust compression levels based on CPU/storage trade-offs
- Configure retention policies to manage storage costs
- Monitor deduplication ratios for file backup efficiency
- Tune backup schedules to avoid resource conflicts

## Integration with Existing System

The backup system integrates seamlessly with the Whisper Transcriber application:

- **Database Integration** - Automatically detects and backs up the main application database
- **File Integration** - Monitors upload and transcript directories for changes
- **API Integration** - Backup endpoints are automatically registered with the main FastAPI application
- **Service Integration** - Backup service lifecycle is managed during application startup/shutdown
- **Configuration Integration** - Uses existing configuration patterns and environment variables

## Future Enhancements

Planned improvements for future releases:

- **Cloud Storage Integration** - Additional backends for Azure Blob Storage, Google Cloud Storage
- **Advanced Encryption** - Hardware security module (HSM) integration
- **Replication** - Multi-region backup replication for enhanced durability
- **Differential Backups** - Block-level differential backups for large files
- **Backup Analytics** - Advanced reporting and analytics dashboard
- **Integration APIs** - Webhooks and notifications for external monitoring systems

## Dependencies

The backup system requires the following Python packages:

- `zstandard>=0.22.0` - High-performance compression
- `watchdog>=4.0.0` - File system monitoring
- `schedule>=1.2.0` - Task scheduling
- `boto3>=1.34.0` - AWS S3 integration (optional)
- `paramiko>=3.4.0` - SFTP/SSH connectivity (optional)

All dependencies are automatically installed when the backup system is enabled.

## Support and Documentation

For additional support and documentation:

- **API Reference** - `/docs` endpoint provides interactive API documentation
- **Configuration Reference** - See `/app/backup/config.py` for all available options
- **Architecture Documentation** - Detailed technical documentation in `/docs/` directory
- **Example Configurations** - Sample configurations for different deployment scenarios
