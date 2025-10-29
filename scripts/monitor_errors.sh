#!/bin/bash
# Comprehensive Error Monitoring Script
# This script monitors all application logs for errors in real-time

set -e

LOGS_DIR="/home/buymeagoat/dev/whisper-transcriber/logs"
CONTAINER_NAME="whisper-production"
MONITOR_PID_FILE="/tmp/whisper_monitor.pid"

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Error patterns to watch for
ERROR_PATTERNS=(
    "ERROR"
    "CRITICAL" 
    "FATAL"
    "Exception"
    "Traceback"
    "Failed"
    "sqlite3.OperationalError"
    "no such table"
    "connection refused"
    "timeout"
    "ImportError"
    "ModuleNotFoundError"
    "500 Internal Server Error"
    "404 Not Found"
    "Permission denied"
    "Access denied"
)

echo -e "${BLUE}🔍 Starting Comprehensive Error Monitoring${NC}"
echo -e "${BLUE}Container: ${CONTAINER_NAME}${NC}"
echo -e "${BLUE}Logs Directory: ${LOGS_DIR}${NC}"
echo -e "${BLUE}Monitoring for patterns: ${ERROR_PATTERNS[*]}${NC}"
echo "================================="

# Function to log errors with timestamp
log_error() {
    local source="$1"
    local line="$2"
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR in ${source}:${NC}"
    echo -e "${RED}${line}${NC}"
    echo "---"
    
    # Also save to error log file
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR in ${source}: ${line}" >> "${LOGS_DIR}/errors/monitoring_errors.log"
}

# Function to log warnings
log_warning() {
    local source="$1"
    local line="$2"
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING in ${source}: ${line}${NC}"
    
    # Also save to error log file
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING in ${source}: ${line}" >> "${LOGS_DIR}/errors/monitoring_warnings.log"
}

# Function to check if a line contains error patterns
check_for_errors() {
    local line="$1"
    local source="$2"
    
    for pattern in "${ERROR_PATTERNS[@]}"; do
        if echo "$line" | grep -qi "$pattern"; then
            if echo "$line" | grep -qi "warning\|warn"; then
                log_warning "$source" "$line"
            else
                log_error "$source" "$line"
            fi
            return 0
        fi
    done
    return 1
}

# Function to monitor docker logs
monitor_docker_logs() {
    echo -e "${GREEN}📊 Starting Docker logs monitoring...${NC}"
    
    # Wait for container to exist
    while ! docker ps -a --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"; do
        echo "Waiting for container ${CONTAINER_NAME} to be created..."
        sleep 2
    done
    
    # Monitor container logs
    docker logs -f "${CONTAINER_NAME}" 2>&1 | while IFS= read -r line; do
        check_for_errors "$line" "docker-${CONTAINER_NAME}"
    done &
    
    echo $! > "${MONITOR_PID_FILE}.docker"
}

# Function to monitor log files
monitor_log_files() {
    echo -e "${GREEN}📁 Starting log files monitoring...${NC}"
    
    # Create log files if they don't exist
    mkdir -p "${LOGS_DIR}/app"
    touch "${LOGS_DIR}/app/application.log"
    touch "${LOGS_DIR}/app/api.log"
    touch "${LOGS_DIR}/app/frontend.log"
    
    # Monitor application logs
    tail -F "${LOGS_DIR}/app/"*.log 2>/dev/null | while IFS= read -r line; do
        check_for_errors "$line" "app-logs"
    done &
    
    echo $! > "${MONITOR_PID_FILE}.files"
}

# Function to monitor system resources
monitor_resources() {
    echo -e "${GREEN}💾 Starting resource monitoring...${NC}"
    
    while true; do
        if docker ps --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
            # Get container stats
            stats=$(docker stats "${CONTAINER_NAME}" --no-stream --format "table {{.CPUPerc}}\t{{.MemUsage}}" | tail -n 1)
            cpu=$(echo "$stats" | awk '{print $1}' | sed 's/%//')
            memory=$(echo "$stats" | awk '{print $2}')
            
            # Check for high resource usage
            if (( $(echo "$cpu > 90" | bc -l) )); then
                log_warning "resource-monitor" "High CPU usage: ${cpu}%"
            fi
            
            # Log stats periodically
            echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] Container Stats - CPU: ${cpu}%, Memory: ${memory}${NC}"
        fi
        sleep 30
    done &
    
    echo $! > "${MONITOR_PID_FILE}.resources"
}

# Function to check application health
monitor_health() {
    echo -e "${GREEN}❤️ Starting health monitoring...${NC}"
    
    while true; do
        if docker ps --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
            # Get container port
            port=$(docker port "${CONTAINER_NAME}" 8000 2>/dev/null | cut -d: -f2)
            
            if [ -n "$port" ]; then
                # Check health endpoint
                if ! curl -s "http://localhost:${port}/health" >/dev/null 2>&1; then
                    log_error "health-monitor" "Health check failed on port ${port}"
                else
                    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] Health check passed${NC}"
                fi
            fi
        fi
        sleep 10
    done &
    
    echo $! > "${MONITOR_PID_FILE}.health"
}

# Function to cleanup on exit
cleanup() {
    echo -e "${YELLOW}🛑 Stopping monitoring processes...${NC}"
    
    # Kill all monitoring processes
    for pid_file in "${MONITOR_PID_FILE}".*; do
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid" 2>/dev/null || true
            fi
            rm -f "$pid_file"
        fi
    done
    
    echo -e "${GREEN}✅ Monitoring stopped${NC}"
}

# Trap signals for cleanup
trap cleanup EXIT INT TERM

# Start all monitoring functions
monitor_docker_logs
monitor_log_files  
monitor_resources
monitor_health

echo -e "${GREEN}✅ All monitoring processes started${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop monitoring${NC}"

# Keep script running
wait