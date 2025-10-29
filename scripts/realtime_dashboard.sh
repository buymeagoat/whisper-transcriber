#!/bin/bash

# Real-Time Application Monitoring Dashboard
# Monitors application during comprehensive testing

set -e

# Configuration
MONITORING_INTERVAL=2
LOG_FILE="/tmp/whisper_realtime_monitoring.log"
DASHBOARD_WIDTH=120

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# Initialize monitoring
echo "$(date): Real-time monitoring started" > "$LOG_FILE"

# Function to get container stats
get_container_stats() {
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" | grep whisper || echo "No containers running"
}

# Function to check API health
check_api_health() {
    local response=$(curl -s -w "%{http_code}" -o /dev/null http://localhost:8000/health 2>/dev/null || echo "000")
    echo "$response"
}

# Function to get recent logs
get_recent_logs() {
    docker compose logs --tail=5 app 2>/dev/null | tail -5 || echo "No recent logs"
}

# Function to count errors in logs
count_recent_errors() {
    docker compose logs --tail=50 app 2>/dev/null | grep -i "error\|exception\|critical\|failed" | wc -l || echo "0"
}

# Function to check test progress
check_test_progress() {
    if [ -f "/tmp/whisper_comprehensive_test.log" ]; then
        local total_tests=$(grep -c "^\[" "/tmp/whisper_comprehensive_test.log" 2>/dev/null || echo "0")
        local passed_tests=$(grep -c "\[PASS\]" "/tmp/whisper_comprehensive_test.log" 2>/dev/null || echo "0")
        local failed_tests=$(grep -c "\[FAIL\]" "/tmp/whisper_comprehensive_test.log" 2>/dev/null || echo "0")
        echo "$total_tests|$passed_tests|$failed_tests"
    else
        echo "0|0|0"
    fi
}

# Function to get system resources
get_system_resources() {
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1 || echo "0")
    local memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}' || echo "0")
    local disk_usage=$(df / | tail -1 | awk '{print $5}' | cut -d'%' -f1 || echo "0")
    echo "$cpu_usage|$memory_usage|$disk_usage"
}

# Function to draw horizontal line
draw_line() {
    printf "%*s\n" $DASHBOARD_WIDTH | tr ' ' '='
}

# Function to center text
center_text() {
    local text="$1"
    local width=$DASHBOARD_WIDTH
    local padding=$(( (width - ${#text}) / 2 ))
    printf "%*s%s%*s\n" $padding "" "$text" $padding ""
}

# Main monitoring dashboard
show_dashboard() {
    clear
    
    # Header
    echo -e "${CYAN}"
    draw_line
    center_text "🚀 WHISPER TRANSCRIBER - REAL-TIME MONITORING DASHBOARD"
    center_text "$(date '+%Y-%m-%d %H:%M:%S')"
    draw_line
    echo -e "${NC}"
    
    # System Health Section
    echo -e "${WHITE}📊 SYSTEM HEALTH${NC}"
    echo "─────────────────────────────────────────────────────────────"
    
    # API Health
    local api_status=$(check_api_health)
    if [ "$api_status" = "200" ]; then
        echo -e "API Status:          ${GREEN}✅ HEALTHY (HTTP 200)${NC}"
    else
        echo -e "API Status:          ${RED}❌ UNHEALTHY (HTTP $api_status)${NC}"
    fi
    
    # Container Stats
    echo -e "\n${WHITE}🐳 CONTAINER STATISTICS${NC}"
    echo "─────────────────────────────────────────────────────────────"
    get_container_stats
    
    # System Resources
    local resources=$(get_system_resources)
    local sys_cpu=$(echo "$resources" | cut -d'|' -f1)
    local sys_mem=$(echo "$resources" | cut -d'|' -f2)
    local sys_disk=$(echo "$resources" | cut -d'|' -f3)
    
    echo -e "\n${WHITE}💻 SYSTEM RESOURCES${NC}"
    echo "─────────────────────────────────────────────────────────────"
    printf "%-20s " "System CPU:"
    if (( $(echo "$sys_cpu < 70" | bc -l) )); then
        echo -e "${GREEN}$sys_cpu%${NC}"
    else
        echo -e "${YELLOW}$sys_cpu%${NC}"
    fi
    
    printf "%-20s " "System Memory:"
    if (( $(echo "$sys_mem < 80" | bc -l) )); then
        echo -e "${GREEN}$sys_mem%${NC}"
    else
        echo -e "${YELLOW}$sys_mem%${NC}"
    fi
    
    printf "%-20s " "Disk Usage:"
    if (( $sys_disk < 80 )); then
        echo -e "${GREEN}$sys_disk%${NC}"
    else
        echo -e "${YELLOW}$sys_disk%${NC}"
    fi
    
    # Test Progress
    local test_progress=$(check_test_progress)
    local total=$(echo "$test_progress" | cut -d'|' -f1)
    local passed=$(echo "$test_progress" | cut -d'|' -f2)
    local failed=$(echo "$test_progress" | cut -d'|' -f3)
    
    echo -e "\n${WHITE}🧪 TEST PROGRESS${NC}"
    echo "─────────────────────────────────────────────────────────────"
    if [ "$total" -gt 0 ]; then
        local success_rate=$((passed * 100 / total))
        echo -e "Total Tests:         ${BLUE}$total${NC}"
        echo -e "Passed:              ${GREEN}$passed${NC}"
        echo -e "Failed:              ${RED}$failed${NC}"
        echo -e "Success Rate:        ${CYAN}$success_rate%${NC}"
        
        # Progress bar
        local bar_width=50
        local filled=$((passed * bar_width / total))
        local empty=$((bar_width - filled))
        
        printf "Progress:            ["
        printf "%*s" $filled | tr ' ' '█'
        printf "%*s" $empty | tr ' ' '░'
        printf "] %d%%\n" $success_rate
    else
        echo -e "Status:              ${YELLOW}Waiting for tests to start...${NC}"
    fi
    
    # Error Monitoring
    local error_count=$(count_recent_errors)
    echo -e "\n${WHITE}🚨 ERROR MONITORING${NC}"
    echo "─────────────────────────────────────────────────────────────"
    if [ "$error_count" -eq 0 ]; then
        echo -e "Recent Errors:       ${GREEN}None detected${NC}"
    elif [ "$error_count" -lt 5 ]; then
        echo -e "Recent Errors:       ${YELLOW}$error_count errors${NC}"
    else
        echo -e "Recent Errors:       ${RED}$error_count errors${NC}"
    fi
    
    # Recent Activity
    echo -e "\n${WHITE}📋 RECENT ACTIVITY${NC}"
    echo "─────────────────────────────────────────────────────────────"
    get_recent_logs | while read -r line; do
        if [[ "$line" =~ error|Error|ERROR|exception|Exception|EXCEPTION ]]; then
            echo -e "${RED}$line${NC}"
        elif [[ "$line" =~ warn|Warn|WARN ]]; then
            echo -e "${YELLOW}$line${NC}"
        elif [[ "$line" =~ info|Info|INFO ]]; then
            echo -e "${BLUE}$line${NC}"
        else
            echo "$line"
        fi
    done
    
    # Latest Test Results
    if [ -f "/tmp/whisper_comprehensive_test.log" ]; then
        echo -e "\n${WHITE}🔬 LATEST TEST RESULTS${NC}"
        echo "─────────────────────────────────────────────────────────────"
        tail -3 "/tmp/whisper_comprehensive_test.log" | while read -r line; do
            if [[ "$line" =~ \[PASS\] ]]; then
                echo -e "${GREEN}$line${NC}"
            elif [[ "$line" =~ \[FAIL\] ]]; then
                echo -e "${RED}$line${NC}"
            elif [[ "$line" =~ \[WARN\] ]]; then
                echo -e "${YELLOW}$line${NC}"
            else
                echo -e "${BLUE}$line${NC}"
            fi
        done
    fi
    
    # Footer
    echo -e "\n${CYAN}"
    draw_line
    center_text "Press Ctrl+C to stop monitoring | Refreshing every ${MONITORING_INTERVAL}s"
    draw_line
    echo -e "${NC}"
    
    # Log this monitoring cycle
    echo "$(date): Dashboard updated - API: $api_status, Errors: $error_count, Tests: $total/$passed/$failed" >> "$LOG_FILE"
}

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Monitoring stopped.${NC}"
    echo "Monitoring log saved to: $LOG_FILE"
    exit 0
}

# Set up signal handling
trap cleanup SIGINT SIGTERM

# Main monitoring loop
main() {
    echo -e "${GREEN}🚀 Starting real-time monitoring...${NC}"
    echo -e "${BLUE}Monitoring log: $LOG_FILE${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    sleep 2
    
    while true; do
        show_dashboard
        sleep $MONITORING_INTERVAL
    done
}

# Run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi