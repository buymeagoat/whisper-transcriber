#!/bin/bash

# T031: Production Deployment and Monitoring - Load Testing Runner
# Comprehensive load testing script for Whisper Transcriber

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
RESULTS_DIR="$PROJECT_ROOT/test-results/load-testing"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

# Default configuration
TEST_TYPE="medium"
HOST="http://localhost:8000"
USERS=50
SPAWN_RATE=5
RUN_TIME="10m"
HEADLESS=false
REPORT_FORMAT="html"
SKIP_SETUP=false

# Parse command line arguments
usage() {
    cat << EOF
Load Testing Runner for Whisper Transcriber

Usage: $0 [OPTIONS]

OPTIONS:
    -t, --type TYPE         Test type: light, medium, heavy, stress (default: medium)
    -h, --host HOST         Target host URL (default: http://localhost:8000)
    -u, --users USERS       Number of concurrent users (overrides test type)
    -r, --spawn-rate RATE   User spawn rate per second (overrides test type)
    -d, --duration TIME     Test duration (e.g., 5m, 10s) (overrides test type)
    --headless              Run in headless mode without web UI
    --format FORMAT         Report format: html, json, csv (default: html)
    --skip-setup            Skip environment setup checks
    --help                  Show this help message

TEST TYPES:
    light       10 users, 2/s spawn rate, 5 minutes
    medium      50 users, 5/s spawn rate, 10 minutes (default)
    heavy       100 users, 10/s spawn rate, 15 minutes
    stress      200 users, 20/s spawn rate, 20 minutes
    spike       Gradually increase from 10 to 200 users over 30 minutes

EXAMPLES:
    $0                                    # Medium load test
    $0 -t heavy                          # Heavy load test
    $0 -t stress --headless              # Stress test without UI
    $0 -u 25 -r 3 -d 15m                # Custom configuration
    $0 --host https://prod.example.com   # Test production server

EOF
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            TEST_TYPE="$2"
            shift 2
            ;;
        -h|--host)
            HOST="$2"
            shift 2
            ;;
        -u|--users)
            USERS="$2"
            shift 2
            ;;
        -r|--spawn-rate)
            SPAWN_RATE="$2"
            shift 2
            ;;
        -d|--duration)
            RUN_TIME="$2"
            shift 2
            ;;
        --headless)
            HEADLESS=true
            shift
            ;;
        --format)
            REPORT_FORMAT="$2"
            shift 2
            ;;
        --skip-setup)
            SKIP_SETUP=true
            shift
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

# Configure test parameters based on type
case $TEST_TYPE in
    light)
        [[ $USERS == "50" ]] && USERS=10
        [[ $SPAWN_RATE == "5" ]] && SPAWN_RATE=2
        [[ $RUN_TIME == "10m" ]] && RUN_TIME="5m"
        ;;
    medium)
        # Default values already set
        ;;
    heavy)
        [[ $USERS == "50" ]] && USERS=100
        [[ $SPAWN_RATE == "5" ]] && SPAWN_RATE=10
        [[ $RUN_TIME == "10m" ]] && RUN_TIME="15m"
        ;;
    stress)
        [[ $USERS == "50" ]] && USERS=200
        [[ $SPAWN_RATE == "5" ]] && SPAWN_RATE=20
        [[ $RUN_TIME == "10m" ]] && RUN_TIME="20m"
        ;;
    spike)
        [[ $USERS == "50" ]] && USERS=200
        [[ $SPAWN_RATE == "5" ]] && SPAWN_RATE=5
        [[ $RUN_TIME == "10m" ]] && RUN_TIME="30m"
        ;;
    *)
        log_error "Unknown test type: $TEST_TYPE"
        usage
        exit 1
        ;;
esac

log_info "Load Testing Configuration"
log_info "========================="
log_info "Test Type: $TEST_TYPE"
log_info "Target Host: $HOST"
log_info "Users: $USERS"
log_info "Spawn Rate: $SPAWN_RATE/s"
log_info "Duration: $RUN_TIME"
log_info "Headless: $HEADLESS"
log_info "Report Format: $REPORT_FORMAT"
echo

# Create results directory
mkdir -p "$RESULTS_DIR"

# Step 1: Environment setup and checks
if [ "$SKIP_SETUP" = false ]; then
    log_step "1. Environment Setup and Checks"
    echo "----------------------------------------"
    
    # Check if locust is installed
    if ! command -v locust &> /dev/null; then
        log_error "Locust is not installed. Install with: pip install locust"
        exit 1
    fi
    
    log_success "Locust is available"
    
    # Check if target host is reachable
    log_info "Checking target host connectivity..."
    if curl -f -s --max-time 10 "$HOST/health" >/dev/null; then
        log_success "Target host is reachable"
    else
        log_warning "Target host health check failed or not reachable"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Check system resources
    log_info "Checking system resources..."
    AVAILABLE_MEMORY=$(free -m | awk 'NR==2{printf "%.0f", $7}')
    if [ "$AVAILABLE_MEMORY" -lt 1024 ]; then
        log_warning "Available memory ($AVAILABLE_MEMORY MB) might be low for load testing"
    fi
    
    # Check if test files exist
    if [ ! -f "$SCRIPT_DIR/locustfile.py" ]; then
        log_error "Locustfile not found: $SCRIPT_DIR/locustfile.py"
        exit 1
    fi
    
    log_success "Environment checks completed"
    echo
fi

# Step 2: Pre-test baseline measurement
log_step "2. Pre-test Baseline Measurement"
echo "----------------------------------------"

BASELINE_FILE="$RESULTS_DIR/baseline_${TIMESTAMP}.json"

log_info "Measuring baseline performance..."
if curl -s -w "@-" -o /dev/null "$HOST/health" << 'EOF' > "$BASELINE_FILE" 2>/dev/null; then
{
    "url": "%{url_effective}",
    "http_code": %{http_code},
    "time_namelookup": %{time_namelookup},
    "time_connect": %{time_connect},
    "time_appconnect": %{time_appconnect},
    "time_pretransfer": %{time_pretransfer},
    "time_redirect": %{time_redirect},
    "time_starttransfer": %{time_starttransfer},
    "time_total": %{time_total},
    "size_download": %{size_download},
    "size_upload": %{size_upload},
    "speed_download": %{speed_download},
    "speed_upload": %{speed_upload}
}
EOF
    log_success "Baseline measurement completed"
else
    log_warning "Baseline measurement failed"
fi

echo

# Step 3: Execute load test
log_step "3. Executing Load Test"
echo "----------------------------------------"

# Prepare locust command
LOCUST_CMD=(
    "locust"
    "--locustfile" "$SCRIPT_DIR/locustfile.py"
    "--host" "$HOST"
    "--users" "$USERS"
    "--spawn-rate" "$SPAWN_RATE"
    "--run-time" "$RUN_TIME"
)

# Add output format options
case $REPORT_FORMAT in
    html)
        LOCUST_CMD+=("--html" "$RESULTS_DIR/load_test_report_${TIMESTAMP}.html")
        ;;
    json)
        LOCUST_CMD+=("--csv" "$RESULTS_DIR/load_test_${TIMESTAMP}")
        ;;
    csv)
        LOCUST_CMD+=("--csv" "$RESULTS_DIR/load_test_${TIMESTAMP}")
        ;;
esac

# Add headless mode if specified
if [ "$HEADLESS" = true ]; then
    LOCUST_CMD+=("--headless")
fi

log_info "Starting load test with command:"
log_info "${LOCUST_CMD[*]}"
echo

# Execute the load test
if "${LOCUST_CMD[@]}"; then
    log_success "Load test completed successfully"
else
    log_error "Load test failed"
    exit 1
fi

echo

# Step 4: Post-test analysis
log_step "4. Post-test Analysis"
echo "----------------------------------------"

# Collect system metrics during test (if available)
log_info "Collecting post-test system metrics..."

# Check if prometheus metrics are available
if curl -s "$HOST/metrics" >/dev/null 2>&1; then
    curl -s "$HOST/metrics" > "$RESULTS_DIR/post_test_metrics_${TIMESTAMP}.txt"
    log_success "Post-test metrics collected"
fi

# Generate summary report
SUMMARY_FILE="$RESULTS_DIR/test_summary_${TIMESTAMP}.md"

cat > "$SUMMARY_FILE" << EOF
# Load Test Summary - $TIMESTAMP

## Test Configuration
- **Test Type**: $TEST_TYPE
- **Target Host**: $HOST
- **Users**: $USERS
- **Spawn Rate**: $SPAWN_RATE/s
- **Duration**: $RUN_TIME
- **Headless**: $HEADLESS

## Test Environment
- **Date**: $(date)
- **System**: $(uname -a)
- **Available Memory**: ${AVAILABLE_MEMORY:-Unknown} MB

## Files Generated
- Test Report: load_test_report_${TIMESTAMP}.html
- Baseline: baseline_${TIMESTAMP}.json
- Summary: test_summary_${TIMESTAMP}.md

## Baseline Performance
EOF

if [ -f "$BASELINE_FILE" ]; then
    echo "- **Response Time**: $(jq -r '.time_total' "$BASELINE_FILE" 2>/dev/null || echo "Unknown")s" >> "$SUMMARY_FILE"
    echo "- **HTTP Code**: $(jq -r '.http_code' "$BASELINE_FILE" 2>/dev/null || echo "Unknown")" >> "$SUMMARY_FILE"
fi

cat >> "$SUMMARY_FILE" << EOF

## Next Steps
1. Review the detailed HTML report for performance analysis
2. Compare results with previous test runs
3. Identify performance bottlenecks and optimization opportunities
4. Update monitoring alerts based on observed thresholds
5. Plan capacity scaling based on load test results

## Recommendations
- Monitor CPU, memory, and disk usage during peak load
- Check database connection pool utilization
- Verify cache hit rates and Redis performance
- Review application logs for errors during load test
- Consider horizontal scaling if response times degrade
EOF

log_success "Test summary generated: $SUMMARY_FILE"

# Step 5: Cleanup and recommendations
log_step "5. Test Completion and Recommendations"
echo "----------------------------------------"

log_success "Load test completed successfully! 🚀"
echo
log_info "Results Location: $RESULTS_DIR"
echo
log_info "Generated Files:"
if [ "$REPORT_FORMAT" = "html" ]; then
    log_info "- HTML Report: load_test_report_${TIMESTAMP}.html"
fi
if [ "$REPORT_FORMAT" = "csv" ] || [ "$REPORT_FORMAT" = "json" ]; then
    log_info "- CSV Data: load_test_${TIMESTAMP}_*.csv"
fi
log_info "- Test Summary: test_summary_${TIMESTAMP}.md"
log_info "- Baseline Metrics: baseline_${TIMESTAMP}.json"
echo
log_info "Next Steps:"
log_info "1. Open HTML report in browser for detailed analysis"
log_info "2. Compare response times with SLA requirements"
log_info "3. Check for error rates and investigate failures"
log_info "4. Monitor system resources and identify bottlenecks"
log_info "5. Update capacity planning based on results"
echo
log_info "Performance Analysis Tips:"
log_info "- Response times should remain stable under load"
log_info "- Error rate should be < 1% for production readiness"
log_info "- Monitor 95th and 99th percentile response times"
log_info "- Check database and cache performance metrics"
log_info "- Verify auto-scaling thresholds are appropriate"
echo

# Open HTML report if not headless and desktop environment is available
if [ "$HEADLESS" = false ] && [ "$REPORT_FORMAT" = "html" ] && command -v xdg-open &> /dev/null; then
    log_info "Opening HTML report..."
    xdg-open "$RESULTS_DIR/load_test_report_${TIMESTAMP}.html" &
fi

log_success "Load testing completed! Check the results directory for detailed reports."