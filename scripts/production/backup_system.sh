#!/bin/bash

# T031: Production Deployment and Monitoring - Backup and Recovery System
# Comprehensive backup solution for Whisper Transcriber production environment

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/whisper-transcriber}"
LOG_FILE="/var/log/whisper-backup.log"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Load environment variables
if [ -f "$PROJECT_ROOT/.env.prod" ]; then
    source "$PROJECT_ROOT/.env.prod"
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1" | tee -a "$LOG_FILE"
}

# Default configuration
BACKUP_TYPE="full"
RETENTION_DAYS=30
COMPRESSION_LEVEL=6
ENCRYPT_BACKUP=true
VERIFY_BACKUP=true
UPLOAD_TO_S3=false
DRY_RUN=false
NOTIFY_SLACK=false

# Database configuration
DB_HOST="${DATABASE_HOST:-localhost}"
DB_PORT="${DATABASE_PORT:-5432}"
DB_NAME="${DATABASE_NAME:-whisper_db}"
DB_USER="${DATABASE_USER:-whisper_user}"
DB_PASSWORD="${DATABASE_PASSWORD}"

# Redis configuration
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_PASSWORD="${REDIS_PASSWORD}"

# S3 configuration
S3_BUCKET="${BACKUP_S3_BUCKET}"
S3_PREFIX="${BACKUP_S3_PREFIX:-backups/whisper-transcriber}"
AWS_REGION="${AWS_REGION:-us-east-1}"

# Slack configuration
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL}"

# Parse command line arguments
usage() {
    cat << EOF
Backup and Recovery System for Whisper Transcriber

Usage: $0 [COMMAND] [OPTIONS]

COMMANDS:
    backup      Create a backup (default)
    restore     Restore from backup
    list        List available backups
    cleanup     Clean up old backups
    verify      Verify backup integrity
    test        Test backup/restore process

OPTIONS:
    -t, --type TYPE         Backup type: full, incremental, differential (default: full)
    -d, --retention DAYS    Retention period in days (default: 30)
    -c, --compression LEVEL Compression level 1-9 (default: 6)
    --no-encrypt           Skip backup encryption
    --no-verify            Skip backup verification
    --upload-s3            Upload backup to S3
    --dry-run              Show what would be done without executing
    --notify-slack         Send notifications to Slack
    --restore-file FILE    Backup file to restore from
    --restore-date DATE    Restore from backup on specific date (YYYY-MM-DD)
    --help                 Show this help message

EXAMPLES:
    $0                                    # Full backup with default settings
    $0 backup -t incremental             # Incremental backup
    $0 restore --restore-date 2024-01-15 # Restore from specific date
    $0 cleanup -d 7                      # Keep only 7 days of backups
    $0 list                              # List all available backups
    $0 verify --restore-file backup.tar.gz # Verify specific backup

EOF
}

# Parse arguments
COMMAND="backup"
if [[ $# -gt 0 && ! $1 =~ ^- ]]; then
    COMMAND="$1"
    shift
fi

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            BACKUP_TYPE="$2"
            shift 2
            ;;
        -d|--retention)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        -c|--compression)
            COMPRESSION_LEVEL="$2"
            shift 2
            ;;
        --no-encrypt)
            ENCRYPT_BACKUP=false
            shift
            ;;
        --no-verify)
            VERIFY_BACKUP=false
            shift
            ;;
        --upload-s3)
            UPLOAD_TO_S3=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --notify-slack)
            NOTIFY_SLACK=true
            shift
            ;;
        --restore-file)
            RESTORE_FILE="$2"
            shift 2
            ;;
        --restore-date)
            RESTORE_DATE="$2"
            shift 2
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Initialize logging
mkdir -p "$(dirname "$LOG_FILE")"
mkdir -p "$BACKUP_DIR"

log_info "=== Whisper Transcriber Backup System ==="
log_info "Command: $COMMAND"
log_info "Timestamp: $TIMESTAMP"
log_info "Backup Directory: $BACKUP_DIR"

# Send notification to Slack
send_slack_notification() {
    local message="$1"
    local color="${2:-good}"
    
    if [ "$NOTIFY_SLACK" = true ] && [ -n "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"attachments\":[{\"color\":\"$color\",\"text\":\"$message\"}]}" \
            "$SLACK_WEBHOOK_URL" || log_warning "Failed to send Slack notification"
    fi
}

# Create database backup
backup_database() {
    log_step "Creating database backup"
    
    local backup_file="$BACKUP_DIR/db_${TIMESTAMP}.sql"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "DRY RUN: Would create database backup: $backup_file"
        return 0
    fi
    
    # Set PGPASSWORD for non-interactive operation
    export PGPASSWORD="$DB_PASSWORD"
    
    # Create database backup
    if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --clean --if-exists --create --verbose > "$backup_file" 2>>"$LOG_FILE"; then
        log_success "Database backup created: $backup_file"
        
        # Compress the backup
        gzip -"$COMPRESSION_LEVEL" "$backup_file"
        log_success "Database backup compressed: ${backup_file}.gz"
        
        return 0
    else
        log_error "Database backup failed"
        return 1
    fi
}

# Create Redis backup
backup_redis() {
    log_step "Creating Redis backup"
    
    local backup_file="$BACKUP_DIR/redis_${TIMESTAMP}.rdb"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "DRY RUN: Would create Redis backup: $backup_file"
        return 0
    fi
    
    # Create Redis backup using BGSAVE
    if [ -n "$REDIS_PASSWORD" ]; then
        redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" BGSAVE
    else
        redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" BGSAVE
    fi
    
    # Wait for background save to complete
    local save_in_progress=true
    while [ "$save_in_progress" = true ]; do
        sleep 2
        local last_save=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ${REDIS_PASSWORD:+-a $REDIS_PASSWORD} LASTSAVE)
        local bg_save_time=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ${REDIS_PASSWORD:+-a $REDIS_PASSWORD} LASTSAVE)
        if [ "$last_save" -eq "$bg_save_time" ]; then
            save_in_progress=false
        fi
    done
    
    # Copy the RDB file
    local redis_data_dir=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ${REDIS_PASSWORD:+-a $REDIS_PASSWORD} CONFIG GET dir | tail -1)
    local rdb_filename=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ${REDIS_PASSWORD:+-a $REDIS_PASSWORD} CONFIG GET dbfilename | tail -1)
    
    if cp "${redis_data_dir}/${rdb_filename}" "$backup_file"; then
        log_success "Redis backup created: $backup_file"
        
        # Compress the backup
        gzip -"$COMPRESSION_LEVEL" "$backup_file"
        log_success "Redis backup compressed: ${backup_file}.gz"
        
        return 0
    else
        log_error "Redis backup failed"
        return 1
    fi
}

# Create application files backup
backup_application() {
    log_step "Creating application files backup"
    
    local backup_file="$BACKUP_DIR/app_${TIMESTAMP}.tar"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "DRY RUN: Would create application backup: $backup_file"
        return 0
    fi
    
    # Create tar archive of application files
    local exclude_patterns=(
        "--exclude=*.pyc"
        "--exclude=__pycache__"
        "--exclude=.git"
        "--exclude=.env*"
        "--exclude=logs/"
        "--exclude=temp/"
        "--exclude=*.tmp"
        "--exclude=node_modules"
        "--exclude=.venv"
        "--exclude=venv"
    )
    
    if tar "${exclude_patterns[@]}" -cf "$backup_file" -C "$PROJECT_ROOT" . 2>>"$LOG_FILE"; then
        log_success "Application backup created: $backup_file"
        
        # Compress the backup
        gzip -"$COMPRESSION_LEVEL" "$backup_file"
        log_success "Application backup compressed: ${backup_file}.gz"
        
        return 0
    else
        log_error "Application backup failed"
        return 1
    fi
}

# Create configuration backup
backup_configuration() {
    log_step "Creating configuration backup"
    
    local backup_file="$BACKUP_DIR/config_${TIMESTAMP}.tar"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "DRY RUN: Would create configuration backup: $backup_file"
        return 0
    fi
    
    # Backup configuration files
    local config_dirs=(
        "/etc/nginx/sites-available"
        "/etc/nginx/sites-enabled"
        "/etc/systemd/system"
        "/etc/ssl/certs"
        "/etc/prometheus"
        "/etc/grafana"
    )
    
    local config_files=(
        "/etc/environment"
        "/etc/hosts"
        "/etc/crontab"
    )
    
    # Create temporary directory for configuration
    local temp_config_dir="/tmp/whisper_config_$TIMESTAMP"
    mkdir -p "$temp_config_dir"
    
    # Copy configuration directories
    for dir in "${config_dirs[@]}"; do
        if [ -d "$dir" ]; then
            cp -r "$dir" "$temp_config_dir/" 2>/dev/null || true
        fi
    done
    
    # Copy configuration files
    for file in "${config_files[@]}"; do
        if [ -f "$file" ]; then
            cp "$file" "$temp_config_dir/" 2>/dev/null || true
        fi
    done
    
    # Create tar archive
    if tar -cf "$backup_file" -C "$temp_config_dir" . 2>>"$LOG_FILE"; then
        log_success "Configuration backup created: $backup_file"
        
        # Compress the backup
        gzip -"$COMPRESSION_LEVEL" "$backup_file"
        log_success "Configuration backup compressed: ${backup_file}.gz"
        
        # Cleanup
        rm -rf "$temp_config_dir"
        return 0
    else
        log_error "Configuration backup failed"
        rm -rf "$temp_config_dir"
        return 1
    fi
}

# Encrypt backup files
encrypt_backups() {
    if [ "$ENCRYPT_BACKUP" = false ]; then
        return 0
    fi
    
    log_step "Encrypting backup files"
    
    local encryption_key="${BACKUP_ENCRYPTION_KEY}"
    if [ -z "$encryption_key" ]; then
        log_warning "No encryption key provided, skipping encryption"
        return 0
    fi
    
    for file in "$BACKUP_DIR"/*_"${TIMESTAMP}".*.gz; do
        if [ -f "$file" ]; then
            if [ "$DRY_RUN" = true ]; then
                log_info "DRY RUN: Would encrypt: $file"
            else
                if openssl enc -aes-256-cbc -salt -in "$file" -out "${file}.enc" -k "$encryption_key"; then
                    rm "$file"  # Remove unencrypted file
                    log_success "Encrypted: ${file}.enc"
                else
                    log_error "Failed to encrypt: $file"
                fi
            fi
        fi
    done
}

# Upload to S3
upload_to_s3() {
    if [ "$UPLOAD_TO_S3" = false ]; then
        return 0
    fi
    
    log_step "Uploading backups to S3"
    
    if [ -z "$S3_BUCKET" ]; then
        log_warning "S3 bucket not configured, skipping upload"
        return 0
    fi
    
    local s3_path="s3://$S3_BUCKET/$S3_PREFIX/$TIMESTAMP/"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "DRY RUN: Would upload to: $s3_path"
        return 0
    fi
    
    # Upload all backup files
    if aws s3 cp "$BACKUP_DIR" "$s3_path" --recursive --include "*_${TIMESTAMP}*" --region "$AWS_REGION"; then
        log_success "Backups uploaded to S3: $s3_path"
    else
        log_error "Failed to upload backups to S3"
        return 1
    fi
}

# Verify backup integrity
verify_backups() {
    if [ "$VERIFY_BACKUP" = false ]; then
        return 0
    fi
    
    log_step "Verifying backup integrity"
    
    local verification_failed=false
    
    for file in "$BACKUP_DIR"/*_"${TIMESTAMP}".*.gz*; do
        if [ -f "$file" ]; then
            if [ "$DRY_RUN" = true ]; then
                log_info "DRY RUN: Would verify: $file"
                continue
            fi
            
            case "$file" in
                *.gz.enc)
                    # Encrypted file - verify encryption format
                    if file "$file" | grep -q "openssl enc"; then
                        log_success "Verified encrypted file: $file"
                    else
                        log_error "Verification failed for encrypted file: $file"
                        verification_failed=true
                    fi
                    ;;
                *.gz)
                    # Compressed file - test decompression
                    if gzip -t "$file"; then
                        log_success "Verified compressed file: $file"
                    else
                        log_error "Verification failed for compressed file: $file"
                        verification_failed=true
                    fi
                    ;;
            esac
        fi
    done
    
    if [ "$verification_failed" = true ]; then
        return 1
    fi
    
    return 0
}

# Create backup manifest
create_manifest() {
    log_step "Creating backup manifest"
    
    local manifest_file="$BACKUP_DIR/manifest_${TIMESTAMP}.json"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "DRY RUN: Would create manifest: $manifest_file"
        return 0
    fi
    
    cat > "$manifest_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "backup_type": "$BACKUP_TYPE",
    "compression_level": $COMPRESSION_LEVEL,
    "encrypted": $ENCRYPT_BACKUP,
    "retention_days": $RETENTION_DAYS,
    "database": {
        "host": "$DB_HOST",
        "port": $DB_PORT,
        "name": "$DB_NAME",
        "user": "$DB_USER"
    },
    "redis": {
        "host": "$REDIS_HOST",
        "port": $REDIS_PORT
    },
    "files": [
EOF
    
    # List all backup files
    local first_file=true
    for file in "$BACKUP_DIR"/*_"${TIMESTAMP}".*.gz*; do
        if [ -f "$file" ]; then
            if [ "$first_file" = true ]; then
                first_file=false
            else
                echo "," >> "$manifest_file"
            fi
            
            local file_size=$(stat -c%s "$file" 2>/dev/null || echo 0)
            local file_hash=$(sha256sum "$file" 2>/dev/null | cut -d' ' -f1 || echo "unknown")
            
            cat >> "$manifest_file" << EOF
        {
            "name": "$(basename "$file")",
            "size": $file_size,
            "sha256": "$file_hash",
            "type": "$(echo "$(basename "$file")" | cut -d'_' -f1)"
        }
EOF
        fi
    done
    
    cat >> "$manifest_file" << EOF
    ],
    "system_info": {
        "hostname": "$(hostname)",
        "os": "$(uname -a)",
        "backup_script_version": "1.0.0"
    }
}
EOF
    
    log_success "Backup manifest created: $manifest_file"
}

# Cleanup old backups
cleanup_old_backups() {
    log_step "Cleaning up old backups (retention: $RETENTION_DAYS days)"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "DRY RUN: Would clean up backups older than $RETENTION_DAYS days"
        find "$BACKUP_DIR" -name "*_20*" -type f -mtime +$RETENTION_DAYS
        return 0
    fi
    
    # Find and remove old backups
    local deleted_count=0
    while IFS= read -r -d '' file; do
        rm "$file"
        ((deleted_count++))
        log_info "Deleted old backup: $(basename "$file")"
    done < <(find "$BACKUP_DIR" -name "*_20*" -type f -mtime +$RETENTION_DAYS -print0)
    
    log_success "Cleaned up $deleted_count old backup files"
}

# List available backups
list_backups() {
    log_step "Listing available backups"
    
    if [ ! -d "$BACKUP_DIR" ]; then
        log_warning "Backup directory does not exist: $BACKUP_DIR"
        return 1
    fi
    
    echo "Available backups in $BACKUP_DIR:"
    echo "=================================================="
    
    # Group backups by timestamp
    local timestamps=($(ls "$BACKUP_DIR" | grep -o '[0-9]\{8\}_[0-9]\{6\}' | sort -u))
    
    for ts in "${timestamps[@]}"; do
        echo
        echo "Backup Set: $ts ($(date -d "${ts%_*} ${ts#*_}" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo 'Date parsing failed'))"
        echo "----------------------------------------"
        
        local manifest_file="$BACKUP_DIR/manifest_${ts}.json"
        if [ -f "$manifest_file" ]; then
            echo "Manifest: $(basename "$manifest_file")"
            if command -v jq >/dev/null; then
                echo "Type: $(jq -r '.backup_type' "$manifest_file" 2>/dev/null || echo 'unknown')"
                echo "Encrypted: $(jq -r '.encrypted' "$manifest_file" 2>/dev/null || echo 'unknown')"
            fi
        fi
        
        # List files for this backup set
        for file in "$BACKUP_DIR"/*_"$ts".*; do
            if [ -f "$file" ]; then
                local size=$(du -h "$file" 2>/dev/null | cut -f1 || echo 'unknown')
                echo "  $(basename "$file") ($size)"
            fi
        done
    done
}

# Main backup function
create_backup() {
    log_info "Starting $BACKUP_TYPE backup process"
    
    send_slack_notification "🔄 Starting backup process for Whisper Transcriber" "warning"
    
    local backup_success=true
    
    # Create individual backups
    if ! backup_database; then
        backup_success=false
    fi
    
    if ! backup_redis; then
        backup_success=false
    fi
    
    if ! backup_application; then
        backup_success=false
    fi
    
    if ! backup_configuration; then
        backup_success=false
    fi
    
    # Post-backup processing
    if [ "$backup_success" = true ]; then
        encrypt_backups
        verify_backups
        create_manifest
        upload_to_s3
        cleanup_old_backups
        
        log_success "Backup process completed successfully"
        send_slack_notification "✅ Backup completed successfully for Whisper Transcriber" "good"
    else
        log_error "Backup process failed"
        send_slack_notification "❌ Backup process failed for Whisper Transcriber" "danger"
        return 1
    fi
}

# Main execution
main() {
    case $COMMAND in
        backup)
            create_backup
            ;;
        restore)
            log_info "Restore functionality not yet implemented"
            exit 1
            ;;
        list)
            list_backups
            ;;
        cleanup)
            cleanup_old_backups
            ;;
        verify)
            verify_backups
            ;;
        test)
            log_info "Test functionality not yet implemented"
            exit 1
            ;;
        *)
            log_error "Unknown command: $COMMAND"
            usage
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"