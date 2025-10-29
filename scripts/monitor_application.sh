#!/bin/bash

# Real-Time Application Monitoring Script
# Provides comprehensive monitoring with automated issue detection and correction

set -e

MONITORING_LOG="/tmp/whisper_monitoring.log"
ALERT_THRESHOLD_RESPONSE_TIME=2.0
ALERT_THRESHOLD_ERROR_RATE=5
HEALTH_CHECK_INTERVAL=10
CORRECTION_ENABLED=true

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Initialize monitoring log
echo "$(date): Monitoring started" > "$MONITORING_LOG"

# Function to log with timestamp
log_event() {
    echo "$(date): $1" | tee -a "$MONITORING_LOG"
}

# Function to check container health
check_container_health() {
    echo -e "${BLUE}=== Container Health Check ===${NC}"
    
    local unhealthy_containers=()
    
    # Check each container
    while IFS= read -r line; do
        if [[ "$line" =~ "unhealthy" ]] || [[ "$line" =~ "Exited" ]]; then
            container_name=$(echo "$line" | awk '{print $1}')
            unhealthy_containers+=("$container_name")
            echo -e "${RED}❌ Unhealthy: $container_name${NC}"
            log_event "CRITICAL: Container $container_name is unhealthy"
        fi
    done < <(docker compose ps --format "table {{.Name}}\t{{.Status}}")
    
    if [ ${#unhealthy_containers[@]} -eq 0 ]; then
        echo -e "${GREEN}✅ All containers healthy${NC}"
        return 0
    else
        if [ "$CORRECTION_ENABLED" = true ]; then
            echo -e "${YELLOW}🔧 Attempting automatic recovery...${NC}"
            for container in "${unhealthy_containers[@]}"; do
                log_event "CORRECTION: Restarting container $container"
                docker compose restart "$container"
            done
        fi
        return 1
    fi
}

# Function to check API health
check_api_health() {
    echo -e "${BLUE}=== API Health Check ===${NC}"
    
    local start_time=$(date +%s.%N)
    local response=$(curl -s -w "HTTPSTATUS:%{http_code}" http://localhost:8000/health 2>/dev/null || echo "HTTPSTATUS:000")
    local end_time=$(date +%s.%N)
    local response_time=$(echo "$end_time - $start_time" | bc)
    
    local http_code=$(echo "$response" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    local response_body=$(echo "$response" | sed 's/HTTPSTATUS:[0-9]*$//')
    
    if [ "$http_code" = "200" ]; then
        if (( $(echo "$response_time > $ALERT_THRESHOLD_RESPONSE_TIME" | bc -l) )); then
            echo -e "${YELLOW}⚠️  API responding but slow: ${response_time}s${NC}"
            log_event "WARNING: Slow API response time: ${response_time}s"
        else
            echo -e "${GREEN}✅ API healthy: ${response_time}s${NC}"
        fi
        return 0
    else
        echo -e "${RED}❌ API health check failed: HTTP $http_code${NC}"
        log_event "CRITICAL: API health check failed with HTTP $http_code"
        
        if [ "$CORRECTION_ENABLED" = true ]; then
            echo -e "${YELLOW}🔧 Restarting application container...${NC}"
            log_event "CORRECTION: Restarting app container due to health check failure"
            docker compose restart app
        fi
        return 1
    fi
}

# Function to check recent errors
check_error_patterns() {
    echo -e "${BLUE}=== Error Pattern Analysis ===${NC}"
    
    local recent_errors=$(docker compose logs --tail=100 app 2>&1 | grep -i "error\|exception\|critical\|failed" | wc -l)
    
    if [ "$recent_errors" -gt "$ALERT_THRESHOLD_ERROR_RATE" ]; then
        echo -e "${RED}❌ High error rate detected: $recent_errors errors in recent logs${NC}"
        log_event "WARNING: High error rate detected: $recent_errors errors"
        
        echo -e "${YELLOW}Recent errors:${NC}"
        docker compose logs --tail=10 app 2>&1 | grep -i "error\|exception\|critical\|failed" | tail -5
        
        return 1
    else
        echo -e "${GREEN}✅ Error rate normal: $recent_errors recent errors${NC}"
        return 0
    fi
}

# Function to check authentication status
check_authentication() {
    echo -e "${BLUE}=== Authentication Test ===${NC}"
    
    # Test login endpoint
    local login_response=$(curl -s -w "HTTPSTATUS:%{http_code}" \
        -X POST "http://localhost:8000/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"username": "admin", "password": "0AYw^lpZa!TM*iw0oIKX"}' 2>/dev/null || echo "HTTPSTATUS:000")
    
    local http_code=$(echo "$login_response" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    
    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✅ Authentication working${NC}"
        return 0
    else
        echo -e "${RED}❌ Authentication failed: HTTP $http_code${NC}"
        log_event "CRITICAL: Authentication system failure: HTTP $http_code"
        return 1
    fi
}

# Function to check database connectivity
check_database() {
    echo -e "${BLUE}=== Database Connectivity ===${NC}"
    
    local db_check=$(docker compose exec -T app python -c "
from api.orm_bootstrap import get_db
from api.models import User
try:
    db = next(get_db())
    user_count = db.query(User).count()
    print(f'SUCCESS:{user_count}')
except Exception as e:
    print(f'ERROR:{e}')
" 2>/dev/null)
    
    if [[ "$db_check" =~ ^SUCCESS: ]]; then
        local user_count=$(echo "$db_check" | cut -d: -f2)
        echo -e "${GREEN}✅ Database healthy: $user_count users${NC}"
        return 0
    else
        echo -e "${RED}❌ Database connectivity issue: $db_check${NC}"
        log_event "CRITICAL: Database connectivity failure: $db_check"
        return 1
    fi
}

# Function to check resource usage
check_resource_usage() {
    echo -e "${BLUE}=== Resource Usage ===${NC}"
    
    local stats=$(docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep -E "(whisper-app|whisper-redis|whisper-worker)")
    
    echo "$stats" | while IFS= read -r line; do
        if [[ "$line" =~ whisper ]]; then
            local container=$(echo "$line" | awk '{print $1}')
            local cpu=$(echo "$line" | awk '{print $2}' | tr -d '%')
            local memory=$(echo "$line" | awk '{print $3}')
            
            if (( $(echo "$cpu > 80" | bc -l) )); then
                echo -e "${YELLOW}⚠️  High CPU usage in $container: $cpu%${NC}"
                log_event "WARNING: High CPU usage in $container: $cpu%"
            else
                echo -e "${GREEN}✅ $container: CPU $cpu%, Memory $memory${NC}"
            fi
        fi
    done
}

# Function to perform comprehensive monitoring cycle
monitoring_cycle() {
    local cycle_start=$(date)
    echo -e "\n${BLUE}======================================================${NC}"
    echo -e "${BLUE}Monitoring Cycle: $cycle_start${NC}"
    echo -e "${BLUE}======================================================${NC}"
    
    local issues=0
    
    # Run all checks
    check_container_health || ((issues++))
    echo ""
    
    check_api_health || ((issues++))
    echo ""
    
    check_error_patterns || ((issues++))
    echo ""
    
    check_authentication || ((issues++))
    echo ""
    
    check_database || ((issues++))
    echo ""
    
    check_resource_usage || ((issues++))
    echo ""
    
    # Summary
    if [ $issues -eq 0 ]; then
        echo -e "${GREEN}🎉 All systems operational${NC}"
        log_event "INFO: All systems operational"
    else
        echo -e "${RED}⚠️  $issues issues detected${NC}"
        log_event "WARNING: $issues issues detected in monitoring cycle"
    fi
    
    echo -e "${BLUE}Next check in ${HEALTH_CHECK_INTERVAL} seconds...${NC}"
    echo -e "${BLUE}======================================================${NC}\n"
}

# Function to start continuous monitoring
start_monitoring() {
    echo -e "${GREEN}🚀 Starting real-time monitoring...${NC}"
    echo -e "${BLUE}Monitoring Configuration:${NC}"
    echo -e "  Response time threshold: ${ALERT_THRESHOLD_RESPONSE_TIME}s"
    echo -e "  Error rate threshold: ${ALERT_THRESHOLD_ERROR_RATE} errors"
    echo -e "  Check interval: ${HEALTH_CHECK_INTERVAL}s"
    echo -e "  Auto-correction: $CORRECTION_ENABLED"
    echo -e "  Log file: $MONITORING_LOG"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop monitoring${NC}"
    echo ""
    
    # Initial check
    monitoring_cycle
    
    # Continuous monitoring loop
    while true; do
        sleep "$HEALTH_CHECK_INTERVAL"
        monitoring_cycle
    done
}

# Function to display monitoring help
show_help() {
    echo "Real-Time Application Monitoring Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -i, --interval SECONDS  Set health check interval (default: 10)"
    echo "  -t, --threshold SECONDS Set response time threshold (default: 2.0)"
    echo "  -e, --errors COUNT      Set error rate threshold (default: 5)"
    echo "  --no-correction         Disable automatic corrections"
    echo "  --single                Run single monitoring cycle and exit"
    echo ""
    echo "Examples:"
    echo "  $0                      Start continuous monitoring with defaults"
    echo "  $0 -i 5 -t 1.0         Monitor every 5 seconds, alert if response > 1s"
    echo "  $0 --single             Run one monitoring cycle and exit"
    echo "  $0 --no-correction      Monitor only, don't attempt automatic fixes"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -i|--interval)
            HEALTH_CHECK_INTERVAL="$2"
            shift 2
            ;;
        -t|--threshold)
            ALERT_THRESHOLD_RESPONSE_TIME="$2"
            shift 2
            ;;
        -e|--errors)
            ALERT_THRESHOLD_ERROR_RATE="$2"
            shift 2
            ;;
        --no-correction)
            CORRECTION_ENABLED=false
            shift
            ;;
        --single)
            monitoring_cycle
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Main execution
cd /home/buymeagoat/dev/whisper-transcriber

# Check if docker compose is available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker first.${NC}"
    exit 1
fi

# Check if application directory exists
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ docker-compose.yml not found. Please run from application directory.${NC}"
    exit 1
fi

# Start monitoring
start_monitoring