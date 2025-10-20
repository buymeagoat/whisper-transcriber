#!/bin/bash
# Production Deployment Script for Whisper Transcriber
# Automated deployment with health checks and rollback capability

set -euo pipefail

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.prod"
BACKUP_DIR="./backups/deployment"
LOG_FILE="./logs/deployment.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local message="[$(date +'%Y-%m-%d %H:%M:%S')] $1"
    echo -e "${GREEN}${message}${NC}"
    echo "${message}" >> "${LOG_FILE}"
}

warn() {
    local message="[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1"
    echo -e "${YELLOW}${message}${NC}"
    echo "${message}" >> "${LOG_FILE}"
}

error() {
    local message="[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1"
    echo -e "${RED}${message}${NC}"
    echo "${message}" >> "${LOG_FILE}"
    exit 1
}

info() {
    local message="[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1"
    echo -e "${BLUE}${message}${NC}"
    echo "${message}" >> "${LOG_FILE}"
}

# Pre-deployment checks
pre_deployment_checks() {
    log "Running pre-deployment checks..."
    
    # Check if required files exist
    [[ -f "${COMPOSE_FILE}" ]] || error "Production compose file not found: ${COMPOSE_FILE}"
    [[ -f "${ENV_FILE}" ]] || error "Production environment file not found: ${ENV_FILE}"
    
    # Check if Docker is running
    docker info > /dev/null 2>&1 || error "Docker is not running"
    
    # Check if docker-compose is available
    command -v docker-compose > /dev/null 2>&1 || error "docker-compose is not installed"
    
    # Validate environment file
    if grep -q "CHANGE_THIS" "${ENV_FILE}"; then
        error "Environment file contains placeholder values. Please configure ${ENV_FILE}"
    fi
    
    # Check available disk space (minimum 10GB)
    local available_space=$(df . | tail -1 | awk '{print $4}')
    if [[ ${available_space} -lt 10485760 ]]; then  # 10GB in KB
        warn "Low disk space detected. Available: $(df -h . | tail -1 | awk '{print $4}')"
    fi
    
    log "Pre-deployment checks completed successfully"
}

# Create backup of current deployment
create_backup() {
    log "Creating deployment backup..."
    
    local backup_timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_path="${BACKUP_DIR}/${backup_timestamp}"
    
    mkdir -p "${backup_path}"
    
    # Backup database if running
    if docker-compose -f "${COMPOSE_FILE}" ps postgres | grep -q "Up"; then
        log "Backing up database..."
        docker-compose -f "${COMPOSE_FILE}" exec -T postgres pg_dumpall -U "${POSTGRES_USER:-whisper}" > "${backup_path}/database_backup.sql"
    fi
    
    # Backup volumes
    log "Backing up application data..."
    docker run --rm -v whisper-transcriber_app_storage:/data -v "${PWD}/${backup_path}:/backup" alpine tar czf /backup/app_storage.tar.gz -C /data .
    docker run --rm -v whisper-transcriber_app_uploads:/data -v "${PWD}/${backup_path}:/backup" alpine tar czf /backup/app_uploads.tar.gz -C /data .
    
    # Backup configuration
    cp "${ENV_FILE}" "${backup_path}/"
    cp -r nginx/ "${backup_path}/" 2>/dev/null || true
    
    echo "${backup_timestamp}" > "${BACKUP_DIR}/latest"
    log "Backup created at ${backup_path}"
}

# Build and deploy application
deploy_application() {
    log "Starting application deployment..."
    
    # Load environment variables
    set -a
    source "${ENV_FILE}"
    set +a
    
    # Pull latest images
    log "Pulling latest images..."
    docker-compose -f "${COMPOSE_FILE}" pull
    
    # Build application image
    log "Building application image..."
    docker-compose -f "${COMPOSE_FILE}" build --no-cache app
    
    # Start services in dependency order
    log "Starting database services..."
    docker-compose -f "${COMPOSE_FILE}" up -d postgres redis
    
    # Wait for database to be ready
    log "Waiting for database to be ready..."
    timeout 60 bash -c 'until docker-compose -f "${COMPOSE_FILE}" exec postgres pg_isready -U "${POSTGRES_USER:-whisper}"; do sleep 2; done'
    
    # Run database migrations
    log "Running database migrations..."
    docker-compose -f "${COMPOSE_FILE}" run --rm app alembic upgrade head
    
    # Start application services
    log "Starting application services..."
    docker-compose -f "${COMPOSE_FILE}" up -d app worker
    
    # Start reverse proxy
    log "Starting reverse proxy..."
    docker-compose -f "${COMPOSE_FILE}" up -d nginx
    
    # Start monitoring services
    log "Starting monitoring services..."
    docker-compose -f "${COMPOSE_FILE}" up -d prometheus grafana
    
    log "All services started successfully"
}

# Health check function
health_check() {
    log "Running health checks..."
    
    local max_attempts=30
    local attempt=1
    
    while [[ ${attempt} -le ${max_attempts} ]]; do
        info "Health check attempt ${attempt}/${max_attempts}..."
        
        # Check if main services are running
        if docker-compose -f "${COMPOSE_FILE}" ps | grep -E "(app|postgres|redis|nginx)" | grep -q "Up"; then
            
            # Test HTTP endpoint
            if curl -f -s "http://localhost/health" > /dev/null 2>&1; then
                log "Health check passed - application is responding"
                return 0
            fi
            
            # Test HTTPS endpoint if certificates exist
            if [[ -f "ssl/fullchain.pem" ]]; then
                if curl -f -s -k "https://localhost/health" > /dev/null 2>&1; then
                    log "Health check passed - HTTPS application is responding"
                    return 0
                fi
            fi
        fi
        
        sleep 10
        ((attempt++))
    done
    
    error "Health check failed after ${max_attempts} attempts"
}

# Rollback function
rollback() {
    warn "Starting rollback procedure..."
    
    if [[ ! -f "${BACKUP_DIR}/latest" ]]; then
        error "No backup found for rollback"
    fi
    
    local backup_timestamp=$(cat "${BACKUP_DIR}/latest")
    local backup_path="${BACKUP_DIR}/${backup_timestamp}"
    
    log "Rolling back to backup: ${backup_timestamp}"
    
    # Stop current services
    docker-compose -f "${COMPOSE_FILE}" down
    
    # Restore configuration
    cp "${backup_path}/${ENV_FILE##*/}" "${ENV_FILE}"
    
    # Restore database
    if [[ -f "${backup_path}/database_backup.sql" ]]; then
        log "Restoring database..."
        docker-compose -f "${COMPOSE_FILE}" up -d postgres
        sleep 10
        docker-compose -f "${COMPOSE_FILE}" exec -T postgres psql -U "${POSTGRES_USER:-whisper}" < "${backup_path}/database_backup.sql"
    fi
    
    # Restore volumes
    log "Restoring application data..."
    docker run --rm -v whisper-transcriber_app_storage:/data -v "${PWD}/${backup_path}:/backup" alpine tar xzf /backup/app_storage.tar.gz -C /data
    docker run --rm -v whisper-transcriber_app_uploads:/data -v "${PWD}/${backup_path}:/backup" alpine tar xzf /backup/app_uploads.tar.gz -C /data
    
    # Start services
    docker-compose -f "${COMPOSE_FILE}" up -d
    
    log "Rollback completed"
}

# Cleanup old backups
cleanup_backups() {
    log "Cleaning up old backups..."
    
    # Keep last 5 backups
    cd "${BACKUP_DIR}"
    ls -t | tail -n +6 | xargs -r rm -rf
    cd - > /dev/null
    
    log "Backup cleanup completed"
}

# Display deployment summary
deployment_summary() {
    log "Deployment Summary:"
    log "=================="
    
    # Show running services
    info "Running services:"
    docker-compose -f "${COMPOSE_FILE}" ps
    
    # Show resource usage
    info "Resource usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" $(docker-compose -f "${COMPOSE_FILE}" ps -q)
    
    # Show application URLs
    info "Application URLs:"
    info "  HTTP:  http://localhost"
    info "  HTTPS: https://localhost (if SSL configured)"
    info "  Admin: https://localhost/admin"
    info "  Metrics: http://localhost:9090 (Prometheus)"
    info "  Dashboards: http://localhost:3000 (Grafana)"
    
    log "Deployment completed successfully!"
}

# Main deployment function
deploy() {
    log "Starting Whisper Transcriber production deployment..."
    
    # Create log directory
    mkdir -p "$(dirname "${LOG_FILE}")"
    mkdir -p "${BACKUP_DIR}"
    
    # Trap for cleanup on failure
    trap 'error "Deployment failed. Check logs for details."' ERR
    
    pre_deployment_checks
    create_backup
    deploy_application
    health_check
    cleanup_backups
    deployment_summary
}

# Rollback command
cmd_rollback() {
    log "Starting rollback procedure..."
    trap 'error "Rollback failed. Manual intervention required."' ERR
    rollback
    health_check
    log "Rollback completed successfully"
}

# Status command
cmd_status() {
    echo "Whisper Transcriber Production Status"
    echo "===================================="
    echo
    
    # Service status
    echo "Services:"
    docker-compose -f "${COMPOSE_FILE}" ps
    echo
    
    # Health check
    echo "Health Check:"
    if curl -f -s "http://localhost/health" > /dev/null 2>&1; then
        echo "✅ Application is healthy"
    else
        echo "❌ Application is not responding"
    fi
    echo
    
    # Resource usage
    echo "Resource Usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" $(docker-compose -f "${COMPOSE_FILE}" ps -q) 2>/dev/null || echo "No containers running"
}

# Logs command
cmd_logs() {
    local service="${1:-}"
    if [[ -n "${service}" ]]; then
        docker-compose -f "${COMPOSE_FILE}" logs -f "${service}"
    else
        docker-compose -f "${COMPOSE_FILE}" logs -f
    fi
}

# Show usage
usage() {
    echo "Whisper Transcriber Production Deployment Script"
    echo
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  deploy              Deploy application to production"
    echo "  rollback            Rollback to previous deployment"
    echo "  status              Show deployment status"
    echo "  logs [service]      Show logs (optionally for specific service)"
    echo "  help                Show this help message"
    echo
    echo "Examples:"
    echo "  $0 deploy                    # Deploy to production"
    echo "  $0 status                    # Check deployment status"
    echo "  $0 logs app                  # Show application logs"
    echo "  $0 rollback                  # Rollback deployment"
}

# Main command dispatcher
main() {
    case "${1:-deploy}" in
        deploy)
            deploy
            ;;
        rollback)
            cmd_rollback
            ;;
        status)
            cmd_status
            ;;
        logs)
            cmd_logs "${2:-}"
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            error "Unknown command: $1. Use 'help' for usage information."
            ;;
    esac
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
