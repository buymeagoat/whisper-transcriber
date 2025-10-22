#!/bin/bash

# T031: Production Deployment and Monitoring - Health Monitoring System
# Comprehensive health monitoring and alerting system for Whisper Transcriber

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
HEALTH_LOG="/var/log/whisper-health.log"
METRICS_DIR="/var/lib/whisper-metrics"
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
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$HEALTH_LOG"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$HEALTH_LOG"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$HEALTH_LOG"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$HEALTH_LOG"
}

log_critical() {
    echo -e "${RED}[CRITICAL]${NC} $1" | tee -a "$HEALTH_LOG"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1" | tee -a "$HEALTH_LOG"
}

# Default configuration
MONITORING_MODE="continuous"
CHECK_INTERVAL=30
ALERT_THRESHOLD=3
ENVIRONMENT="production"
ENABLE_ALERTS=true
ENABLE_METRICS=true
DRY_RUN=false
DURATION=0

# Service configuration
API_HOST="${API_HOST:-http://localhost:8000}"
DB_HOST="${DATABASE_HOST:-localhost}"
DB_PORT="${DATABASE_PORT:-5432}"
DB_NAME="${DATABASE_NAME:-whisper_db}"
DB_USER="${DATABASE_USER:-whisper_user}"
DB_PASSWORD="${DATABASE_PASSWORD}"
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_PASSWORD="${REDIS_PASSWORD}"

# Alert configuration
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL}"
EMAIL_ALERTS="${EMAIL_ALERTS:-admin@example.com}"
PAGERDUTY_SERVICE_KEY="${PAGERDUTY_SERVICE_KEY}"

# Health check thresholds
CPU_THRESHOLD=80
MEMORY_THRESHOLD=85
DISK_THRESHOLD=90
RESPONSE_TIME_THRESHOLD=2000  # milliseconds
ERROR_RATE_THRESHOLD=5        # percentage
QUEUE_SIZE_THRESHOLD=1000

# Parse command line arguments
usage() {
    cat << EOF
Health Monitoring System for Whisper Transcriber

Usage: $0 [OPTIONS]

OPTIONS:
    -m, --mode MODE         Monitoring mode: continuous, once, scheduled (default: continuous)
    -i, --interval SECONDS  Check interval for continuous mode (default: 30)
    -d, --duration SECONDS  Run for specified duration (0 = infinite, default: 0)
    -t, --threshold COUNT   Alert threshold - alerts after N consecutive failures (default: 3)
    -e, --environment ENV   Environment: production, staging, development (default: production)
    --no-alerts            Disable alert notifications
    --no-metrics           Disable metrics collection
    --dry-run              Show what would be checked without executing
    --api-host HOST        API host URL (default: http://localhost:8000)
    --help                 Show this help message

MODES:
    continuous      Monitor continuously with specified interval
    once            Run health checks once and exit
    scheduled       Run from cron with comprehensive reporting

EXAMPLES:
    $0                                    # Continuous monitoring with defaults
    $0 -m once                           # Single health check
    $0 -i 60 -d 3600                    # Monitor for 1 hour with 60s intervals
    $0 --dry-run                        # Show what would be monitored
    $0 -e staging --no-alerts           # Monitor staging without alerts

EOF
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--mode)
            MONITORING_MODE="$2"
            shift 2
            ;;
        -i|--interval)
            CHECK_INTERVAL="$2"
            shift 2
            ;;
        -d|--duration)
            DURATION="$2"
            shift 2
            ;;
        -t|--threshold)
            ALERT_THRESHOLD="$2"
            shift 2
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --no-alerts)
            ENABLE_ALERTS=false
            shift
            ;;
        --no-metrics)
            ENABLE_METRICS=false
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --api-host)
            API_HOST="$2"
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

# Initialize logging and metrics directories
mkdir -p "$(dirname "$HEALTH_LOG")"
mkdir -p "$METRICS_DIR"

log_info "=== Whisper Transcriber Health Monitoring ==="
log_info "Mode: $MONITORING_MODE"
log_info "Environment: $ENVIRONMENT"
log_info "Check Interval: ${CHECK_INTERVAL}s"
log_info "Alert Threshold: $ALERT_THRESHOLD consecutive failures"
log_info "Alerts Enabled: $ENABLE_ALERTS"
log_info "Metrics Enabled: $ENABLE_METRICS"

# Global counters for consecutive failures
declare -A FAILURE_COUNTS
declare -A LAST_ALERT_TIME

# Send alert notification
send_alert() {
    local service="$1"
    local message="$2"
    local severity="${3:-warning}"
    local current_time=$(date +%s)
    
    if [ "$ENABLE_ALERTS" = false ] || [ "$DRY_RUN" = true ]; then
        log_info "DRY RUN: Would send $severity alert for $service: $message"
        return 0
    fi
    
    # Rate limiting - don't send alerts more than once every 5 minutes for the same service
    local last_alert=${LAST_ALERT_TIME[$service]:-0}
    if [ $((current_time - last_alert)) -lt 300 ]; then
        log_info "Rate limiting alert for $service (last alert: $((current_time - last_alert))s ago)"
        return 0
    fi
    
    LAST_ALERT_TIME[$service]=$current_time
    
    # Slack notification
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        local color="warning"
        case $severity in
            critical) color="danger" ;;
            warning) color="warning" ;;
            info) color="good" ;;
        esac
        
        local slack_message="🚨 *$severity* - $service\n$message\nEnvironment: $ENVIRONMENT\nTime: $(date)"
        
        curl -s -X POST -H 'Content-type: application/json' \
            --data "{\"attachments\":[{\"color\":\"$color\",\"text\":\"$slack_message\"}]}" \
            "$SLACK_WEBHOOK_URL" || log_warning "Failed to send Slack alert"
    fi
    
    # Email notification (if sendmail is available)
    if command -v sendmail >/dev/null && [ -n "$EMAIL_ALERTS" ]; then
        {
            echo "Subject: [$ENVIRONMENT] Whisper Transcriber $severity Alert - $service"
            echo "To: $EMAIL_ALERTS"
            echo ""
            echo "$message"
            echo ""
            echo "Time: $(date)"
            echo "Environment: $ENVIRONMENT"
            echo "Host: $(hostname)"
        } | sendmail "$EMAIL_ALERTS" || log_warning "Failed to send email alert"
    fi
    
    # PagerDuty (if configured)
    if [ -n "$PAGERDUTY_SERVICE_KEY" ] && [ "$severity" = "critical" ]; then
        local pd_payload=$(cat << EOF
{
    "service_key": "$PAGERDUTY_SERVICE_KEY",
    "event_type": "trigger",
    "incident_key": "$service-$(date +%s)",
    "description": "$message",
    "details": {
        "environment": "$ENVIRONMENT",
        "service": "$service",
        "timestamp": "$(date -Iseconds)",
        "host": "$(hostname)"
    }
}
EOF
        )
        
        curl -s -X POST -H 'Content-type: application/json' \
            --data "$pd_payload" \
            https://events.pagerduty.com/generic/2010-04-15/create_event.json || log_warning "Failed to send PagerDuty alert"
    fi
    
    log_info "Alert sent for $service: $message"
}

# Record health check result
record_failure() {
    local service="$1"
    local current_count=${FAILURE_COUNTS[$service]:-0}
    FAILURE_COUNTS[$service]=$((current_count + 1))
    
    if [ "${FAILURE_COUNTS[$service]}" -ge "$ALERT_THRESHOLD" ]; then
        return 0  # Threshold reached
    else
        return 1  # Below threshold
    fi
}

record_success() {
    local service="$1"
    FAILURE_COUNTS[$service]=0
}

# Check API health
check_api_health() {
    log_step "Checking API health"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "DRY RUN: Would check API health at $API_HOST"
        return 0
    fi
    
    local start_time=$(date +%s%3N)
    local response=$(curl -s -w "%{http_code}|%{time_total}" "$API_HOST/health" 2>/dev/null || echo "000|999")
    local end_time=$(date +%s%3N)
    
    local http_code=$(echo "$response" | cut -d'|' -f1)
    local response_time_ms=$(echo "scale=0; $(echo "$response" | cut -d'|' -f2) * 1000" | bc 2>/dev/null || echo "999")
    
    if [ "$http_code" = "200" ]; then
        record_success "api"
        log_success "API health check passed (${response_time_ms}ms)"
        
        # Check response time threshold
        if [ "$response_time_ms" -gt "$RESPONSE_TIME_THRESHOLD" ]; then
            if record_failure "api_response_time"; then
                send_alert "API Response Time" "API response time is ${response_time_ms}ms (threshold: ${RESPONSE_TIME_THRESHOLD}ms)" "warning"
            fi
        else
            record_success "api_response_time"
        fi
        
        # Record metrics
        if [ "$ENABLE_METRICS" = true ]; then
            echo "${TIMESTAMP},api_response_time,$response_time_ms" >> "$METRICS_DIR/api_metrics.csv"
            echo "${TIMESTAMP},api_status,1" >> "$METRICS_DIR/api_metrics.csv"
        fi
        
        return 0
    else
        if record_failure "api"; then
            send_alert "API Health" "API health check failed with HTTP code: $http_code" "critical"
        fi
        log_error "API health check failed (HTTP: $http_code)"
        
        if [ "$ENABLE_METRICS" = true ]; then
            echo "${TIMESTAMP},api_status,0" >> "$METRICS_DIR/api_metrics.csv"
        fi
        
        return 1
    fi
}

# Check database connectivity
check_database_health() {
    log_step "Checking database health"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "DRY RUN: Would check database connectivity"
        return 0
    fi
    
    # Set PGPASSWORD for non-interactive operation
    export PGPASSWORD="$DB_PASSWORD"
    
    local start_time=$(date +%s%3N)
    if pg_isready -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -U "$DB_USER" >/dev/null 2>&1; then
        local end_time=$(date +%s%3N)
        local connection_time=$((end_time - start_time))
        
        record_success "database"
        log_success "Database connectivity check passed (${connection_time}ms)"
        
        # Check database performance
        local query_time=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT EXTRACT(EPOCH FROM NOW());" 2>/dev/null | tr -d ' \n' || echo "0")
        if [ -n "$query_time" ] && [ "$query_time" != "0" ]; then
            record_success "database_query"
            log_success "Database query test passed"
        else
            if record_failure "database_query"; then
                send_alert "Database Query" "Database query test failed" "warning"
            fi
            log_warning "Database query test failed"
        fi
        
        # Record metrics
        if [ "$ENABLE_METRICS" = true ]; then
            echo "${TIMESTAMP},db_connection_time,$connection_time" >> "$METRICS_DIR/db_metrics.csv"
            echo "${TIMESTAMP},db_status,1" >> "$METRICS_DIR/db_metrics.csv"
        fi
        
        return 0
    else
        if record_failure "database"; then
            send_alert "Database Connectivity" "Database connectivity check failed" "critical"
        fi
        log_error "Database connectivity check failed"
        
        if [ "$ENABLE_METRICS" = true ]; then
            echo "${TIMESTAMP},db_status,0" >> "$METRICS_DIR/db_metrics.csv"
        fi
        
        return 1
    fi
}

# Check Redis connectivity
check_redis_health() {
    log_step "Checking Redis health"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "DRY RUN: Would check Redis connectivity"
        return 0
    fi
    
    local redis_cmd="redis-cli -h $REDIS_HOST -p $REDIS_PORT"
    if [ -n "$REDIS_PASSWORD" ]; then
        redis_cmd="$redis_cmd -a $REDIS_PASSWORD"
    fi
    
    local start_time=$(date +%s%3N)
    if $redis_cmd ping >/dev/null 2>&1; then
        local end_time=$(date +%s%3N)
        local ping_time=$((end_time - start_time))
        
        record_success "redis"
        log_success "Redis connectivity check passed (${ping_time}ms)"
        
        # Check Redis info
        local redis_info=$($redis_cmd info server 2>/dev/null || echo "")
        if [ -n "$redis_info" ]; then
            local redis_version=$(echo "$redis_info" | grep "^redis_version:" | cut -d: -f2 | tr -d '\r')
            log_info "Redis version: $redis_version"
        fi
        
        # Record metrics
        if [ "$ENABLE_METRICS" = true ]; then
            echo "${TIMESTAMP},redis_ping_time,$ping_time" >> "$METRICS_DIR/redis_metrics.csv"
            echo "${TIMESTAMP},redis_status,1" >> "$METRICS_DIR/redis_metrics.csv"
        fi
        
        return 0
    else
        if record_failure "redis"; then
            send_alert "Redis Connectivity" "Redis connectivity check failed" "critical"
        fi
        log_error "Redis connectivity check failed"
        
        if [ "$ENABLE_METRICS" = true ]; then
            echo "${TIMESTAMP},redis_status,0" >> "$METRICS_DIR/redis_metrics.csv"
        fi
        
        return 1
    fi
}

# Check system resources
check_system_resources() {
    log_step "Checking system resources"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "DRY RUN: Would check system resources"
        return 0
    fi
    
    # CPU usage
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1 | cut -d'u' -f1 | tr -d ' ')
    if [ -n "$cpu_usage" ]; then
        if [ "${cpu_usage%.*}" -gt "$CPU_THRESHOLD" ]; then
            if record_failure "cpu_usage"; then
                send_alert "High CPU Usage" "CPU usage is ${cpu_usage}% (threshold: ${CPU_THRESHOLD}%)" "warning"
            fi
            log_warning "High CPU usage: ${cpu_usage}%"
        else
            record_success "cpu_usage"
            log_success "CPU usage: ${cpu_usage}%"
        fi
        
        if [ "$ENABLE_METRICS" = true ]; then
            echo "${TIMESTAMP},cpu_usage,$cpu_usage" >> "$METRICS_DIR/system_metrics.csv"
        fi
    fi
    
    # Memory usage
    local memory_info=$(free | grep Mem)
    local total_mem=$(echo "$memory_info" | awk '{print $2}')
    local used_mem=$(echo "$memory_info" | awk '{print $3}')
    local memory_usage=$(echo "scale=1; $used_mem * 100 / $total_mem" | bc)
    
    if [ "${memory_usage%.*}" -gt "$MEMORY_THRESHOLD" ]; then
        if record_failure "memory_usage"; then
            send_alert "High Memory Usage" "Memory usage is ${memory_usage}% (threshold: ${MEMORY_THRESHOLD}%)" "warning"
        fi
        log_warning "High memory usage: ${memory_usage}%"
    else
        record_success "memory_usage"
        log_success "Memory usage: ${memory_usage}%"
    fi
    
    if [ "$ENABLE_METRICS" = true ]; then
        echo "${TIMESTAMP},memory_usage,$memory_usage" >> "$METRICS_DIR/system_metrics.csv"
    fi
    
    # Disk usage
    local disk_usage=$(df / | tail -1 | awk '{print $5}' | cut -d'%' -f1)
    if [ "$disk_usage" -gt "$DISK_THRESHOLD" ]; then
        if record_failure "disk_usage"; then
            send_alert "High Disk Usage" "Disk usage is ${disk_usage}% (threshold: ${DISK_THRESHOLD}%)" "critical"
        fi
        log_error "High disk usage: ${disk_usage}%"
    else
        record_success "disk_usage"
        log_success "Disk usage: ${disk_usage}%"
    fi
    
    if [ "$ENABLE_METRICS" = true ]; then
        echo "${TIMESTAMP},disk_usage,$disk_usage" >> "$METRICS_DIR/system_metrics.csv"
    fi
}

# Check application-specific metrics
check_application_metrics() {
    log_step "Checking application metrics"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "DRY RUN: Would check application metrics"
        return 0
    fi
    
    # Check if metrics endpoint is available
    local metrics_response=$(curl -s "$API_HOST/metrics" 2>/dev/null || echo "")
    
    if [ -n "$metrics_response" ]; then
        # Parse Prometheus metrics
        local active_jobs=$(echo "$metrics_response" | grep "^whisper_active_jobs" | awk '{print $2}' || echo "0")
        local queue_size=$(echo "$metrics_response" | grep "^whisper_queue_size" | awk '{print $2}' || echo "0")
        local error_rate=$(echo "$metrics_response" | grep "^whisper_error_rate" | awk '{print $2}' || echo "0")
        
        log_info "Active jobs: $active_jobs"
        log_info "Queue size: $queue_size"
        log_info "Error rate: $error_rate%"
        
        # Check queue size threshold
        if [ "$queue_size" -gt "$QUEUE_SIZE_THRESHOLD" ]; then
            if record_failure "queue_size"; then
                send_alert "High Queue Size" "Job queue size is $queue_size (threshold: $QUEUE_SIZE_THRESHOLD)" "warning"
            fi
            log_warning "High queue size: $queue_size"
        else
            record_success "queue_size"
        fi
        
        # Check error rate threshold
        if [ "${error_rate%.*}" -gt "$ERROR_RATE_THRESHOLD" ]; then
            if record_failure "error_rate"; then
                send_alert "High Error Rate" "Error rate is ${error_rate}% (threshold: ${ERROR_RATE_THRESHOLD}%)" "critical"
            fi
            log_error "High error rate: ${error_rate}%"
        else
            record_success "error_rate"
        fi
        
        # Record metrics
        if [ "$ENABLE_METRICS" = true ]; then
            echo "${TIMESTAMP},active_jobs,$active_jobs" >> "$METRICS_DIR/app_metrics.csv"
            echo "${TIMESTAMP},queue_size,$queue_size" >> "$METRICS_DIR/app_metrics.csv"
            echo "${TIMESTAMP},error_rate,$error_rate" >> "$METRICS_DIR/app_metrics.csv"
        fi
    else
        if record_failure "metrics_endpoint"; then
            send_alert "Metrics Endpoint" "Application metrics endpoint is not responding" "warning"
        fi
        log_warning "Application metrics endpoint not available"
    fi
}

# Perform comprehensive health check
perform_health_check() {
    log_info "Starting comprehensive health check at $(date)"
    
    local checks_passed=0
    local checks_total=5
    
    # Run all health checks
    if check_api_health; then
        ((checks_passed++))
    fi
    
    if check_database_health; then
        ((checks_passed++))
    fi
    
    if check_redis_health; then
        ((checks_passed++))
    fi
    
    if check_system_resources; then
        ((checks_passed++))
    fi
    
    if check_application_metrics; then
        ((checks_passed++))
    fi
    
    # Calculate health score
    local health_score=$(echo "scale=1; $checks_passed * 100 / $checks_total" | bc)
    
    log_info "Health check completed: $checks_passed/$checks_total checks passed (${health_score}%)"
    
    # Record overall health score
    if [ "$ENABLE_METRICS" = true ]; then
        echo "${TIMESTAMP},health_score,$health_score" >> "$METRICS_DIR/health_metrics.csv"
    fi
    
    # Alert on low health score
    if [ "${health_score%.*}" -lt 80 ]; then
        send_alert "System Health" "System health score is ${health_score}% (${checks_passed}/${checks_total} checks passed)" "critical"
    fi
    
    return $((checks_total - checks_passed))
}

# Generate health report
generate_health_report() {
    local report_file="$METRICS_DIR/health_report_${TIMESTAMP}.json"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "DRY RUN: Would generate health report: $report_file"
        return 0
    fi
    
    cat > "$report_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "environment": "$ENVIRONMENT",
    "monitoring_mode": "$MONITORING_MODE",
    "failure_counts": {
EOF
    
    local first_entry=true
    for service in "${!FAILURE_COUNTS[@]}"; do
        if [ "$first_entry" = true ]; then
            first_entry=false
        else
            echo "," >> "$report_file"
        fi
        echo "        \"$service\": ${FAILURE_COUNTS[$service]}" >> "$report_file"
    done
    
    cat >> "$report_file" << EOF
    },
    "system_info": {
        "hostname": "$(hostname)",
        "uptime": "$(uptime | awk -F'up ' '{print $2}' | awk -F',' '{print $1}')",
        "load_average": "$(uptime | awk -F'load average:' '{print $2}')",
        "disk_space": "$(df -h / | tail -1 | awk '{print $4}')"
    },
    "check_results": {
        "api_health": $([ "${FAILURE_COUNTS[api]:-0}" -eq 0 ] && echo "true" || echo "false"),
        "database_health": $([ "${FAILURE_COUNTS[database]:-0}" -eq 0 ] && echo "true" || echo "false"),
        "redis_health": $([ "${FAILURE_COUNTS[redis]:-0}" -eq 0 ] && echo "true" || echo "false"),
        "system_resources": $([ "${FAILURE_COUNTS[cpu_usage]:-0}" -eq 0 ] && [ "${FAILURE_COUNTS[memory_usage]:-0}" -eq 0 ] && [ "${FAILURE_COUNTS[disk_usage]:-0}" -eq 0 ] && echo "true" || echo "false")
    }
}
EOF
    
    log_success "Health report generated: $report_file"
}

# Main monitoring loop
start_monitoring() {
    log_info "Starting health monitoring in $MONITORING_MODE mode"
    
    local start_time=$(date +%s)
    local check_count=0
    
    case $MONITORING_MODE in
        once)
            perform_health_check
            generate_health_report
            ;;
        continuous)
            while true; do
                perform_health_check
                ((check_count++))
                
                # Check if duration limit reached
                if [ "$DURATION" -gt 0 ]; then
                    local current_time=$(date +%s)
                    local elapsed=$((current_time - start_time))
                    if [ "$elapsed" -ge "$DURATION" ]; then
                        log_info "Duration limit reached ($DURATION seconds), stopping monitoring"
                        break
                    fi
                fi
                
                log_info "Waiting ${CHECK_INTERVAL} seconds until next check..."
                sleep "$CHECK_INTERVAL"
            done
            
            log_success "Monitoring completed after $check_count checks"
            generate_health_report
            ;;
        scheduled)
            perform_health_check
            generate_health_report
            
            # Cleanup old metrics files (keep last 30 days)
            find "$METRICS_DIR" -name "*.csv" -mtime +30 -delete 2>/dev/null || true
            find "$METRICS_DIR" -name "health_report_*.json" -mtime +30 -delete 2>/dev/null || true
            ;;
        *)
            log_error "Unknown monitoring mode: $MONITORING_MODE"
            exit 1
            ;;
    esac
}

# Signal handlers for graceful shutdown
cleanup() {
    log_info "Received signal, shutting down health monitoring..."
    generate_health_report
    exit 0
}

trap cleanup SIGINT SIGTERM

# Main execution
if [ "$DRY_RUN" = true ]; then
    log_info "DRY RUN MODE - No actual checks will be performed"
fi

start_monitoring

log_success "Health monitoring completed successfully!"