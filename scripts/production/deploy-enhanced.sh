#!/bin/bash

# T031: Production Deployment and Monitoring - Enhanced Deployment Script
# Comprehensive production deployment with monitoring and security

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

log_config() {
    echo -e "${CYAN}[CONFIG]${NC} $1"
}

# Error handling
error_exit() {
    log_error "$1"
    exit 1
}

# Cleanup function
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        log_error "Deployment failed! Check logs above for details."
        log_info "Cleaning up temporary files..."
        # Add cleanup commands here if needed
    fi
    exit $exit_code
}

trap cleanup EXIT

# Parse command line arguments
ENVIRONMENT="production"
CONFIG_FILE=""
SKIP_BACKUP=false
SKIP_TESTS=false
FORCE_RECREATE=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --force-recreate)
            FORCE_RECREATE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            cat << EOF
Enhanced Production Deployment Script for Whisper Transcriber

Usage: $0 [OPTIONS]

OPTIONS:
    -e, --environment ENV    Deployment environment (default: production)
    -c, --config FILE       Custom configuration file
    --skip-backup           Skip database backup before deployment
    --skip-tests            Skip pre-deployment tests
    --force-recreate        Force recreation of all containers
    --dry-run               Show what would be done without executing
    -h, --help              Show this help message

EXAMPLES:
    $0                                    # Standard production deployment
    $0 --environment staging             # Deploy to staging
    $0 --config .env.custom              # Use custom config
    $0 --force-recreate --skip-backup    # Force recreate without backup
    $0 --dry-run                         # Preview deployment steps

EOF
            exit 0
            ;;
        *)
            error_exit "Unknown option: $1. Use --help for usage information."
            ;;
    esac
done

# Determine configuration file
if [ -z "$CONFIG_FILE" ]; then
    case $ENVIRONMENT in
        production)
            CONFIG_FILE=".env.enhanced.prod"
            ;;
        staging)
            CONFIG_FILE=".env.staging"
            ;;
        development)
            CONFIG_FILE=".env.development"
            ;;
        *)
            CONFIG_FILE=".env.$ENVIRONMENT"
            ;;
    esac
fi

# Check if configuration file exists
if [ ! -f "$PROJECT_ROOT/$CONFIG_FILE" ]; then
    error_exit "Configuration file not found: $CONFIG_FILE"
fi

log_info "Enhanced Production Deployment for Whisper Transcriber"
log_info "=================================================="
log_config "Environment: $ENVIRONMENT"
log_config "Config File: $CONFIG_FILE"
log_config "Project Root: $PROJECT_ROOT"
log_config "Timestamp: $TIMESTAMP"

if [ "$DRY_RUN" = true ]; then
    log_warning "DRY RUN MODE - No changes will be made"
fi

echo

# Step 1: Pre-deployment checks
log_step "1. Pre-deployment System Checks"
echo "----------------------------------------"

# Check Docker and Docker Compose
if ! command -v docker &> /dev/null; then
    error_exit "Docker is not installed or not in PATH"
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    error_exit "Docker Compose is not installed or not in PATH"
fi

DOCKER_COMPOSE_CMD="docker-compose"
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
fi

log_success "Docker and Docker Compose are available"

# Check system resources
log_info "Checking system resources..."
AVAILABLE_MEMORY=$(free -m | awk 'NR==2{printf "%.0f", $7}')
AVAILABLE_DISK=$(df "$PROJECT_ROOT" | awk 'NR==2{print $4}')

if [ "$AVAILABLE_MEMORY" -lt 4096 ]; then
    log_warning "Available memory ($AVAILABLE_MEMORY MB) is below recommended 4GB"
fi

if [ "$AVAILABLE_DISK" -lt 10485760 ]; then # 10GB in KB
    log_warning "Available disk space ($(($AVAILABLE_DISK / 1024 / 1024))GB) is below recommended 10GB"
fi

log_success "System resource check completed"

# Check Docker daemon
if ! docker info &> /dev/null; then
    error_exit "Docker daemon is not running"
fi

log_success "Docker daemon is running"

# Step 2: Configuration validation
log_step "2. Configuration Validation"
echo "----------------------------------------"

cd "$PROJECT_ROOT"

# Load and validate environment variables
if [ "$DRY_RUN" = false ]; then
    source "$CONFIG_FILE"
    
    # Check required variables
    REQUIRED_VARS=(
        "SECRET_KEY"
        "JWT_SECRET_KEY"
        "POSTGRES_PASSWORD"
        "REDIS_PASSWORD"
        "GRAFANA_PASSWORD"
    )
    
    for var in "${REQUIRED_VARS[@]}"; do
        if [ -z "${!var:-}" ]; then
            error_exit "Required environment variable $var is not set in $CONFIG_FILE"
        fi
        
        # Check minimum length for security-critical variables
        if [[ "$var" == *"SECRET"* || "$var" == *"PASSWORD"* ]]; then
            if [ ${#!var} -lt 12 ]; then
                error_exit "$var must be at least 12 characters long"
            fi
        fi
    done
    
    log_success "All required environment variables are set"
    
    # Validate domain configuration
    if [ -n "${DOMAIN:-}" ]; then
        log_info "Domain configured: $DOMAIN"
        
        # Check if SSL certificates exist
        if [ -d "ssl" ] && [ -f "ssl/${DOMAIN}.crt" ] && [ -f "ssl/${DOMAIN}.key" ]; then
            log_success "SSL certificates found for $DOMAIN"
        else
            log_warning "SSL certificates not found. Run setup-ssl.sh first or use self-signed certificates."
        fi
    else
        log_warning "No domain configured. Using localhost configuration."
    fi
fi

# Step 3: Pre-deployment backup
if [ "$SKIP_BACKUP" = false ]; then
    log_step "3. Pre-deployment Backup"
    echo "----------------------------------------"
    
    # Check if database is running
    if docker ps --format "table {{.Names}}" | grep -q whisper-postgres; then
        log_info "Creating database backup before deployment..."
        
        if [ "$DRY_RUN" = false ]; then
            # Create backup directory
            mkdir -p "backups/pre-deployment"
            
            # Database backup
            BACKUP_FILE="backups/pre-deployment/postgres_backup_${TIMESTAMP}.sql"
            if docker exec whisper-postgres pg_dump -U "${POSTGRES_USER:-whisper}" "${POSTGRES_DB:-whisper_prod}" > "$BACKUP_FILE"; then
                log_success "Database backup created: $BACKUP_FILE"
            else
                log_error "Database backup failed"
                read -p "Continue without backup? (y/N): " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    exit 1
                fi
            fi
            
            # Application data backup
            if [ -d "data" ]; then
                STORAGE_BACKUP="backups/pre-deployment/storage_backup_${TIMESTAMP}.tar.gz"
                tar -czf "$STORAGE_BACKUP" data/
                log_success "Storage backup created: $STORAGE_BACKUP"
            fi
        else
            log_info "[DRY RUN] Would create database and storage backups"
        fi
    else
        log_info "No existing database found. Skipping backup."
    fi
else
    log_warning "Skipping pre-deployment backup (--skip-backup specified)"
fi

# Step 4: Pre-deployment tests
if [ "$SKIP_TESTS" = false ]; then
    log_step "4. Pre-deployment Tests"
    echo "----------------------------------------"
    
    if [ -f "tools/comprehensive_validator.py" ]; then
        log_info "Running comprehensive validation..."
        
        if [ "$DRY_RUN" = false ]; then
            if python tools/comprehensive_validator.py --quick; then
                log_success "Pre-deployment tests passed"
            else
                log_error "Pre-deployment tests failed"
                read -p "Continue despite test failures? (y/N): " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    exit 1
                fi
            fi
        else
            log_info "[DRY RUN] Would run comprehensive validation tests"
        fi
    else
        log_warning "Validation script not found. Skipping tests."
    fi
else
    log_warning "Skipping pre-deployment tests (--skip-tests specified)"
fi

# Step 5: Build and prepare images
log_step "5. Building Application Images"
echo "----------------------------------------"

if [ "$DRY_RUN" = false ]; then
    # Build optimized production image
    log_info "Building optimized production Docker image..."
    if docker build -f Dockerfile.optimized --target production -t whisper-transcriber:production .; then
        log_success "Production image built successfully"
    else
        error_exit "Failed to build production image"
    fi
    
    # Build additional images if needed
    if [ "$ENVIRONMENT" = "staging" ]; then
        log_info "Building development image for staging..."
        docker build -f Dockerfile.optimized --target development -t whisper-transcriber:development .
    fi
else
    log_info "[DRY RUN] Would build production Docker images"
fi

# Step 6: Setup data directories
log_step "6. Setting Up Data Directories"
echo "----------------------------------------"

DATA_DIRS=(
    "data/postgres"
    "data/redis"
    "data/storage"
    "data/uploads"
    "data/transcripts"
    "data/models"
    "data/prometheus"
    "data/grafana"
    "data/elasticsearch"
    "backups/postgres"
    "logs"
    "ssl"
)

for dir in "${DATA_DIRS[@]}"; do
    if [ "$DRY_RUN" = false ]; then
        mkdir -p "$dir"
        # Set proper permissions
        case $dir in
            data/postgres|data/redis)
                chmod 700 "$dir"
                ;;
            data/grafana)
                chmod 755 "$dir"
                # Grafana runs as UID 472
                if command -v chown &> /dev/null; then
                    chown 472:472 "$dir" 2>/dev/null || true
                fi
                ;;
            *)
                chmod 755 "$dir"
                ;;
        esac
        log_info "Created directory: $dir"
    else
        log_info "[DRY RUN] Would create directory: $dir"
    fi
done

log_success "Data directories prepared"

# Step 7: Deploy services
log_step "7. Deploying Services"
echo "----------------------------------------"

COMPOSE_FILE="docker-compose.enhanced.yml"
if [ ! -f "$COMPOSE_FILE" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
fi

if [ ! -f "$COMPOSE_FILE" ]; then
    error_exit "No production Docker Compose file found"
fi

if [ "$DRY_RUN" = false ]; then
    # Set environment variables
    export $(grep -v '^#' "$CONFIG_FILE" | xargs)
    
    # Stop existing services if force recreate
    if [ "$FORCE_RECREATE" = true ]; then
        log_info "Stopping existing services..."
        $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" down
    fi
    
    # Deploy services
    log_info "Deploying services with $COMPOSE_FILE..."
    
    # Start core services first
    log_info "Starting database and cache services..."
    $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" up -d postgres redis
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    for i in {1..30}; do
        if $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" exec -T postgres pg_isready -U "${POSTGRES_USER:-whisper}" -d "${POSTGRES_DB:-whisper_prod}" &>/dev/null; then
            break
        fi
        sleep 2
    done
    
    # Start application services
    log_info "Starting application services..."
    $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" up -d app worker scheduler
    
    # Start monitoring services
    log_info "Starting monitoring services..."
    $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" up -d prometheus grafana node_exporter cadvisor
    
    # Start logging services
    if $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" config --services | grep -q elasticsearch; then
        log_info "Starting logging services..."
        $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" up -d elasticsearch filebeat
    fi
    
    # Start load balancer last
    log_info "Starting load balancer..."
    $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" up -d nginx
    
    log_success "All services deployed"
else
    log_info "[DRY RUN] Would deploy services using $COMPOSE_FILE"
fi

# Step 8: Post-deployment verification
log_step "8. Post-deployment Verification"
echo "----------------------------------------"

if [ "$DRY_RUN" = false ]; then
    # Wait for services to stabilize
    log_info "Waiting for services to stabilize..."
    sleep 30
    
    # Check service health
    log_info "Checking service health..."
    
    SERVICES=("app" "postgres" "redis" "prometheus" "grafana")
    FAILED_SERVICES=()
    
    for service in "${SERVICES[@]}"; do
        if $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" ps "$service" | grep -q "Up"; then
            log_success "$service is running"
        else
            log_error "$service is not running"
            FAILED_SERVICES+=("$service")
        fi
    done
    
    if [ ${#FAILED_SERVICES[@]} -gt 0 ]; then
        log_error "The following services failed to start: ${FAILED_SERVICES[*]}"
        log_info "Check logs with: $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE logs [service_name]"
        exit 1
    fi
    
    # Test application endpoints
    log_info "Testing application endpoints..."
    
    # Wait for application to be ready
    for i in {1..60}; do
        if curl -f -s http://localhost/health >/dev/null; then
            log_success "Application health check passed"
            break
        fi
        if [ $i -eq 60 ]; then
            log_error "Application health check failed after 60 seconds"
            exit 1
        fi
        sleep 2
    done
    
    # Test monitoring endpoints
    if curl -f -s http://localhost:9090/prometheus/-/healthy >/dev/null; then
        log_success "Prometheus is accessible"
    else
        log_warning "Prometheus health check failed"
    fi
    
    if curl -f -s http://localhost:3000/grafana/api/health >/dev/null; then
        log_success "Grafana is accessible"
    else
        log_warning "Grafana health check failed"
    fi
else
    log_info "[DRY RUN] Would perform post-deployment verification"
fi

# Step 9: Performance optimization
log_step "9. Performance Optimization"
echo "----------------------------------------"

if [ "$DRY_RUN" = false ]; then
    # Database optimization
    log_info "Optimizing database performance..."
    $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" exec -T postgres psql -U "${POSTGRES_USER:-whisper}" -d "${POSTGRES_DB:-whisper_prod}" -c "ANALYZE;" || true
    
    # Cache warmup
    log_info "Warming up application cache..."
    curl -s http://localhost/api/health >/dev/null || true
    curl -s http://localhost/api/stats >/dev/null || true
    
    log_success "Performance optimization completed"
else
    log_info "[DRY RUN] Would perform performance optimization"
fi

# Step 10: Final summary and next steps
log_step "10. Deployment Summary"
echo "----------------------------------------"

log_success "Deployment completed successfully!"
echo
log_info "Deployment Details:"
log_info "- Environment: $ENVIRONMENT"
log_info "- Configuration: $CONFIG_FILE"
log_info "- Compose File: $COMPOSE_FILE"
log_info "- Timestamp: $TIMESTAMP"
echo
log_info "Service URLs (if running locally):"
log_info "- Application: http://localhost/"
log_info "- Prometheus: http://localhost:9090/prometheus/"
log_info "- Grafana: http://localhost:3000/grafana/ (admin / \$GRAFANA_PASSWORD)"
echo
log_info "Useful Commands:"
log_info "- View logs: $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE logs [service]"
log_info "- Scale workers: $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE up -d --scale worker=N"
log_info "- Update services: $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE pull && $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE up -d"
log_info "- Stop services: $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE down"
echo
log_info "Next Steps:"
log_info "1. Configure DNS to point to your server"
log_info "2. Set up SSL certificates (if not done already)"
log_info "3. Configure monitoring alerts"
log_info "4. Set up automated backups"
log_info "5. Perform load testing"
echo
log_success "Enhanced production deployment complete! 🚀"