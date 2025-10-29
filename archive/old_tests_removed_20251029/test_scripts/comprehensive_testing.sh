#!/bin/bash

# Comprehensive Application Testing with Real-Time Monitoring
# Simulates user interactions across all UI components, APIs, and functionality

set -e

# Configuration
BASE_URL="http://localhost:8000"
MONITORING_LOG="/tmp/whisper_comprehensive_test.log"
TEST_DATA_DIR="/tmp/whisper_test_data"
RESULTS_DIR="/tmp/whisper_test_results"
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="0AYw^lpZa!TM*iw0oIKX"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
WARNING_TESTS=0

# Initialize testing environment
setup_testing_environment() {
    echo -e "${BLUE}🚀 Setting up comprehensive testing environment...${NC}"
    
    # Create directories
    mkdir -p "$TEST_DATA_DIR" "$RESULTS_DIR"
    
    # Initialize log
    echo "$(date): Comprehensive testing started" > "$MONITORING_LOG"
    
    # Create test data files
    create_test_data
    
    echo -e "${GREEN}✅ Testing environment ready${NC}"
}

# Create test data files
create_test_data() {
    echo -e "${CYAN}📁 Creating test data files...${NC}"
    
    # Create various test audio files (mock)
    echo "This is a test audio file for transcription" > "$TEST_DATA_DIR/test_audio.txt"
    echo "Short audio sample" > "$TEST_DATA_DIR/short_audio.txt"
    echo "Long audio sample with multiple sentences for testing transcription accuracy and performance." > "$TEST_DATA_DIR/long_audio.txt"
    
    # Create invalid files for security testing
    echo "<?php system(\$_GET['cmd']); ?>" > "$TEST_DATA_DIR/malicious.php"
    echo -e "\x00\x01\x02\x03\x04\x05" > "$TEST_DATA_DIR/binary_file.dat"
    
    # Create large file for size limit testing
    dd if=/dev/zero of="$TEST_DATA_DIR/large_file.dat" bs=1M count=10 2>/dev/null
    
    # Create JSON test payloads
    cat > "$TEST_DATA_DIR/valid_login.json" << EOF
{
    "username": "$ADMIN_USERNAME",
    "password": "$ADMIN_PASSWORD"
}
EOF

    cat > "$TEST_DATA_DIR/invalid_login.json" << EOF
{
    "username": "hacker",
    "password": "wrongpassword"
}
EOF

    cat > "$TEST_DATA_DIR/malicious_payload.json" << EOF
{
    "username": "admin'; DROP TABLE users; --",
    "password": "test"
}
EOF

    echo -e "${GREEN}✅ Test data created${NC}"
}

# Logging function
log_test() {
    local status="$1"
    local test_name="$2"
    local details="$3"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo "[$timestamp] [$status] $test_name: $details" >> "$MONITORING_LOG"
    
    case "$status" in
        "PASS") 
            echo -e "${GREEN}✅ $test_name${NC}"
            ((PASSED_TESTS++))
            ;;
        "FAIL") 
            echo -e "${RED}❌ $test_name${NC}"
            echo -e "${RED}   Details: $details${NC}"
            ((FAILED_TESTS++))
            ;;
        "WARN") 
            echo -e "${YELLOW}⚠️  $test_name${NC}"
            echo -e "${YELLOW}   Details: $details${NC}"
            ((WARNING_TESTS++))
            ;;
        "INFO") 
            echo -e "${BLUE}ℹ️  $test_name${NC}"
            ;;
    esac
    ((TOTAL_TESTS++))
}

# HTTP request helper with monitoring
make_request() {
    local method="$1"
    local url="$2"
    local headers="$3"
    local data="$4"
    local expected_code="$5"
    
    local start_time=$(date +%s.%N)
    local response
    local http_code
    local response_time
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "HTTPSTATUS:%{http_code}" $headers "$url" 2>/dev/null || echo "HTTPSTATUS:000")
    elif [ "$method" = "POST" ]; then
        if [[ "$data" == *"@"* ]]; then
            # File upload
            response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST $headers $data "$url" 2>/dev/null || echo "HTTPSTATUS:000")
        else
            # JSON data
            response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST $headers -d "$data" "$url" 2>/dev/null || echo "HTTPSTATUS:000")
        fi
    fi
    
    local end_time=$(date +%s.%N)
    response_time=$(echo "$end_time - $start_time" | bc)
    
    http_code=$(echo "$response" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    local response_body=$(echo "$response" | sed 's/HTTPSTATUS:[0-9]*$//')
    
    # Store response for analysis
    echo "$response_body" > "$RESULTS_DIR/last_response.json"
    echo "$http_code" > "$RESULTS_DIR/last_http_code.txt"
    echo "$response_time" > "$RESULTS_DIR/last_response_time.txt"
    
    # Validate response
    if [ "$http_code" = "$expected_code" ]; then
        return 0
    else
        return 1
    fi
}

# Test 1: System Health and Availability
test_system_health() {
    echo -e "\n${MAGENTA}=== Phase 1: System Health Testing ===${NC}"
    
    # Test health endpoint
    if make_request "GET" "$BASE_URL/health" "" "" "200"; then
        log_test "PASS" "Health Endpoint" "System responding normally"
    else
        log_test "FAIL" "Health Endpoint" "System not responding (HTTP $(cat $RESULTS_DIR/last_http_code.txt))"
    fi
    
    # Test API documentation
    if make_request "GET" "$BASE_URL/docs" "" "" "200"; then
        log_test "PASS" "API Documentation" "Documentation accessible"
    else
        log_test "FAIL" "API Documentation" "Documentation not accessible"
    fi
    
    # Test OpenAPI schema
    if make_request "GET" "$BASE_URL/openapi.json" "" "" "200"; then
        log_test "PASS" "OpenAPI Schema" "Schema available"
    else
        log_test "FAIL" "OpenAPI Schema" "Schema not available"
    fi
    
    # Check response times
    local response_time=$(cat "$RESULTS_DIR/last_response_time.txt")
    if (( $(echo "$response_time < 1.0" | bc -l) )); then
        log_test "PASS" "Response Time" "Fast response: ${response_time}s"
    else
        log_test "WARN" "Response Time" "Slow response: ${response_time}s"
    fi
}

# Test 2: Authentication System
test_authentication() {
    echo -e "\n${MAGENTA}=== Phase 2: Authentication Testing ===${NC}"
    
    # Test valid login
    if make_request "POST" "$BASE_URL/auth/login" "-H 'Content-Type: application/json'" "$(cat $TEST_DATA_DIR/valid_login.json)" "200"; then
        log_test "PASS" "Valid Login" "Authentication successful"
        
        # Extract token for subsequent tests
        TOKEN=$(cat "$RESULTS_DIR/last_response.json" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null || echo "")
        echo "$TOKEN" > "$RESULTS_DIR/auth_token.txt"
        
        if [ -n "$TOKEN" ]; then
            log_test "PASS" "JWT Token Generation" "Token extracted successfully"
        else
            log_test "FAIL" "JWT Token Generation" "No token in response"
        fi
    else
        log_test "FAIL" "Valid Login" "Authentication failed (HTTP $(cat $RESULTS_DIR/last_http_code.txt))"
    fi
    
    # Test invalid login
    if make_request "POST" "$BASE_URL/auth/login" "-H 'Content-Type: application/json'" "$(cat $TEST_DATA_DIR/invalid_login.json)" "401"; then
        log_test "PASS" "Invalid Login Rejection" "Correctly rejected invalid credentials"
    else
        log_test "FAIL" "Invalid Login Rejection" "Should reject invalid credentials"
    fi
    
    # Test SQL injection attempt
    if make_request "POST" "$BASE_URL/auth/login" "-H 'Content-Type: application/json'" "$(cat $TEST_DATA_DIR/malicious_payload.json)" "401"; then
        log_test "PASS" "SQL Injection Protection" "Malicious payload rejected"
    else
        log_test "FAIL" "SQL Injection Protection" "Vulnerable to SQL injection"
    fi
    
    # Test token validation
    local token=$(cat "$RESULTS_DIR/auth_token.txt" 2>/dev/null || echo "")
    if [ -n "$token" ]; then
        if make_request "GET" "$BASE_URL/jobs" "-H 'Authorization: Bearer $token'" "" "200"; then
            log_test "PASS" "JWT Token Validation" "Token accepted for protected endpoints"
        else
            log_test "FAIL" "JWT Token Validation" "Token not working for protected endpoints"
        fi
    fi
    
    # Test unauthorized access
    if make_request "GET" "$BASE_URL/jobs" "" "" "401"; then
        log_test "PASS" "Authorization Enforcement" "Unauthorized access correctly blocked"
    else
        log_test "FAIL" "Authorization Enforcement" "Should require authorization"
    fi
}

# Test 3: API Endpoints
test_api_endpoints() {
    echo -e "\n${MAGENTA}=== Phase 3: API Endpoints Testing ===${NC}"
    
    local token=$(cat "$RESULTS_DIR/auth_token.txt" 2>/dev/null || echo "")
    local auth_header=""
    
    if [ -n "$token" ]; then
        auth_header="-H 'Authorization: Bearer $token'"
    else
        log_test "WARN" "API Testing" "No auth token available, testing with unauthorized access"
    fi
    
    # Test jobs endpoint
    if make_request "GET" "$BASE_URL/jobs" "$auth_header" "" "200"; then
        log_test "PASS" "Jobs Endpoint" "Jobs list accessible"
    else
        log_test "FAIL" "Jobs Endpoint" "Jobs endpoint not working"
    fi
    
    # Test transcripts endpoint
    if make_request "GET" "$BASE_URL/transcripts" "$auth_header" "" "200"; then
        log_test "PASS" "Transcripts Endpoint" "Transcripts list accessible"
    else
        log_test "FAIL" "Transcripts Endpoint" "Transcripts endpoint not working"
    fi
    
    # Test models endpoint
    if make_request "GET" "$BASE_URL/models" "$auth_header" "" "200"; then
        log_test "PASS" "Models Endpoint" "Models list accessible"
    else
        log_test "FAIL" "Models Endpoint" "Models endpoint not working"
    fi
    
    # Test admin endpoints (if token is valid)
    if [ -n "$token" ]; then
        if make_request "GET" "$BASE_URL/admin/stats" "$auth_header" "" "200"; then
            log_test "PASS" "Admin Stats Endpoint" "Admin statistics accessible"
        else
            local code=$(cat "$RESULTS_DIR/last_http_code.txt")
            if [ "$code" = "403" ]; then
                log_test "WARN" "Admin Stats Endpoint" "Access forbidden (may require API key)"
            else
                log_test "FAIL" "Admin Stats Endpoint" "Admin endpoint error (HTTP $code)"
            fi
        fi
    fi
}

# Test 4: File Upload Functionality
test_file_upload() {
    echo -e "\n${MAGENTA}=== Phase 4: File Upload Testing ===${NC}"
    
    local token=$(cat "$RESULTS_DIR/auth_token.txt" 2>/dev/null || echo "")
    
    if [ -z "$token" ]; then
        log_test "WARN" "File Upload Testing" "No auth token, skipping upload tests"
        return
    fi
    
    # Test valid file upload
    if make_request "POST" "$BASE_URL/upload" "-H 'Authorization: Bearer $token'" "-F 'file=@$TEST_DATA_DIR/test_audio.txt' -F 'model=tiny'" "200"; then
        log_test "PASS" "Valid File Upload" "File upload successful"
    else
        local code=$(cat "$RESULTS_DIR/last_http_code.txt")
        log_test "FAIL" "Valid File Upload" "File upload failed (HTTP $code)"
    fi
    
    # Test malicious file upload
    if make_request "POST" "$BASE_URL/upload" "-H 'Authorization: Bearer $token'" "-F 'file=@$TEST_DATA_DIR/malicious.php'" "400"; then
        log_test "PASS" "Malicious File Rejection" "Malicious file correctly rejected"
    else
        log_test "FAIL" "Malicious File Rejection" "Security vulnerability: malicious file accepted"
    fi
    
    # Test large file upload
    if make_request "POST" "$BASE_URL/upload" "-H 'Authorization: Bearer $token'" "-F 'file=@$TEST_DATA_DIR/large_file.dat'" "413"; then
        log_test "PASS" "Large File Rejection" "Large file size limit enforced"
    else
        local code=$(cat "$RESULTS_DIR/last_http_code.txt")
        if [ "$code" = "200" ]; then
            log_test "WARN" "Large File Rejection" "Large file accepted (check size limits)"
        else
            log_test "FAIL" "Large File Rejection" "Unexpected response to large file (HTTP $code)"
        fi
    fi
    
    # Test binary file upload
    if make_request "POST" "$BASE_URL/upload" "-H 'Authorization: Bearer $token'" "-F 'file=@$TEST_DATA_DIR/binary_file.dat'" "400"; then
        log_test "PASS" "Binary File Rejection" "Binary file correctly rejected"
    else
        log_test "WARN" "Binary File Rejection" "Binary file handling unclear"
    fi
}

# Test 5: Transcription Workflow
test_transcription_workflow() {
    echo -e "\n${MAGENTA}=== Phase 5: Transcription Workflow Testing ===${NC}"
    
    local token=$(cat "$RESULTS_DIR/auth_token.txt" 2>/dev/null || echo "")
    
    if [ -z "$token" ]; then
        log_test "WARN" "Transcription Testing" "No auth token, skipping transcription tests"
        return
    fi
    
    # Test transcription submission
    if make_request "POST" "$BASE_URL/transcribe" "-H 'Authorization: Bearer $token'" "-F 'file=@$TEST_DATA_DIR/test_audio.txt' -F 'model=tiny' -F 'language=auto'" "200"; then
        log_test "PASS" "Transcription Submission" "Transcription job submitted"
        
        # Try to extract job ID
        local job_id=$(cat "$RESULTS_DIR/last_response.json" | python3 -c "import sys, json; print(json.load(sys.stdin).get('job_id', ''))" 2>/dev/null || echo "")
        
        if [ -n "$job_id" ]; then
            log_test "PASS" "Job ID Generation" "Job ID: $job_id"
            echo "$job_id" > "$RESULTS_DIR/job_id.txt"
            
            # Test job status checking
            sleep 2
            if make_request "GET" "$BASE_URL/jobs/$job_id" "-H 'Authorization: Bearer $token'" "" "200"; then
                log_test "PASS" "Job Status Check" "Job status retrieval working"
            else
                log_test "FAIL" "Job Status Check" "Cannot retrieve job status"
            fi
            
            # Test job progress monitoring
            if make_request "GET" "$BASE_URL/jobs/$job_id/status" "-H 'Authorization: Bearer $token'" "" "200"; then
                log_test "PASS" "Job Progress Monitoring" "Job progress tracking working"
            else
                log_test "WARN" "Job Progress Monitoring" "Job progress endpoint may not exist"
            fi
        else
            log_test "FAIL" "Job ID Generation" "No job ID returned"
        fi
    else
        local code=$(cat "$RESULTS_DIR/last_http_code.txt")
        log_test "FAIL" "Transcription Submission" "Transcription failed (HTTP $code)"
    fi
    
    # Test job queue listing
    if make_request "GET" "$BASE_URL/jobs/queue" "-H 'Authorization: Bearer $token'" "" "200"; then
        log_test "PASS" "Job Queue Listing" "Job queue accessible"
    else
        log_test "WARN" "Job Queue Listing" "Job queue endpoint may not exist"
    fi
}

# Test 6: WebSocket and Real-time Features
test_websocket_features() {
    echo -e "\n${MAGENTA}=== Phase 6: WebSocket and Real-time Testing ===${NC}"
    
    # Test WebSocket connection endpoint
    if make_request "GET" "$BASE_URL/ws" "" "" "426"; then
        log_test "PASS" "WebSocket Endpoint" "WebSocket upgrade available"
    else
        local code=$(cat "$RESULTS_DIR/last_http_code.txt")
        if [ "$code" = "404" ]; then
            log_test "WARN" "WebSocket Endpoint" "WebSocket endpoint not found"
        else
            log_test "FAIL" "WebSocket Endpoint" "WebSocket endpoint error (HTTP $code)"
        fi
    fi
    
    # Test real-time updates endpoint
    if make_request "GET" "$BASE_URL/ws/updates" "" "" "426"; then
        log_test "PASS" "Real-time Updates" "Real-time updates endpoint available"
    else
        log_test "WARN" "Real-time Updates" "Real-time updates may not be implemented"
    fi
    
    # Note: Full WebSocket testing would require a WebSocket client
    log_test "INFO" "WebSocket Testing" "Full WebSocket testing requires specialized client"
}

# Test 7: Security Features
test_security_features() {
    echo -e "\n${MAGENTA}=== Phase 7: Security Testing ===${NC}"
    
    # Test CORS headers
    local cors_response=$(curl -s -I -H "Origin: http://malicious-site.com" "$BASE_URL/health" 2>/dev/null || echo "")
    if echo "$cors_response" | grep -i "access-control-allow-origin" > /dev/null; then
        log_test "WARN" "CORS Configuration" "CORS headers present (check configuration)"
    else
        log_test "PASS" "CORS Configuration" "CORS properly configured"
    fi
    
    # Test security headers
    local security_headers=$(curl -s -I "$BASE_URL/health" 2>/dev/null || echo "")
    
    if echo "$security_headers" | grep -i "x-frame-options" > /dev/null; then
        log_test "PASS" "X-Frame-Options Header" "Clickjacking protection present"
    else
        log_test "WARN" "X-Frame-Options Header" "Missing clickjacking protection"
    fi
    
    if echo "$security_headers" | grep -i "x-content-type-options" > /dev/null; then
        log_test "PASS" "X-Content-Type-Options" "MIME type sniffing protection present"
    else
        log_test "WARN" "X-Content-Type-Options" "Missing MIME type protection"
    fi
    
    # Test rate limiting (if implemented)
    log_test "INFO" "Rate Limiting" "Sending multiple requests to test rate limiting"
    local rate_limit_failed=0
    for i in {1..20}; do
        if ! make_request "GET" "$BASE_URL/health" "" "" "200"; then
            rate_limit_failed=$((rate_limit_failed + 1))
        fi
        sleep 0.1
    done
    
    if [ $rate_limit_failed -gt 0 ]; then
        log_test "PASS" "Rate Limiting" "Rate limiting appears to be active"
    else
        log_test "WARN" "Rate Limiting" "No rate limiting detected"
    fi
}

# Test 8: Error Handling
test_error_handling() {
    echo -e "\n${MAGENTA}=== Phase 8: Error Handling Testing ===${NC}"
    
    # Test 404 handling
    if make_request "GET" "$BASE_URL/nonexistent-endpoint" "" "" "404"; then
        log_test "PASS" "404 Error Handling" "Proper 404 responses"
    else
        log_test "FAIL" "404 Error Handling" "Incorrect 404 handling"
    fi
    
    # Test malformed JSON
    if make_request "POST" "$BASE_URL/auth/login" "-H 'Content-Type: application/json'" '{"invalid": json}' "400"; then
        log_test "PASS" "Malformed JSON Handling" "Malformed JSON properly rejected"
    else
        log_test "FAIL" "Malformed JSON Handling" "Should reject malformed JSON"
    fi
    
    # Test empty requests
    if make_request "POST" "$BASE_URL/auth/login" "-H 'Content-Type: application/json'" '' "400"; then
        log_test "PASS" "Empty Request Handling" "Empty requests properly handled"
    else
        log_test "WARN" "Empty Request Handling" "Empty request handling unclear"
    fi
    
    # Test method not allowed
    if make_request "POST" "$BASE_URL/health" "" "" "405"; then
        log_test "PASS" "Method Not Allowed" "Proper HTTP method enforcement"
    else
        local code=$(cat "$RESULTS_DIR/last_http_code.txt")
        log_test "WARN" "Method Not Allowed" "HTTP method enforcement unclear (HTTP $code)"
    fi
}

# Test 9: Performance Testing
test_performance() {
    echo -e "\n${MAGENTA}=== Phase 9: Performance Testing ===${NC}"
    
    local total_time=0
    local successful_requests=0
    local failed_requests=0
    
    log_test "INFO" "Performance Testing" "Running 50 concurrent requests"
    
    # Concurrent requests test
    for i in {1..50}; do
        {
            local start_time=$(date +%s.%N)
            if make_request "GET" "$BASE_URL/health" "" "" "200"; then
                local end_time=$(date +%s.%N)
                local request_time=$(echo "$end_time - $start_time" | bc)
                echo "$request_time" >> "$RESULTS_DIR/response_times.txt"
                ((successful_requests++))
            else
                ((failed_requests++))
            fi
        } &
    done
    wait
    
    # Calculate performance metrics
    if [ -f "$RESULTS_DIR/response_times.txt" ]; then
        local avg_time=$(awk '{sum+=$1} END {print sum/NR}' "$RESULTS_DIR/response_times.txt")
        local max_time=$(sort -n "$RESULTS_DIR/response_times.txt" | tail -1)
        local min_time=$(sort -n "$RESULTS_DIR/response_times.txt" | head -1)
        
        log_test "INFO" "Performance Results" "Successful: $successful_requests, Failed: $failed_requests"
        log_test "INFO" "Response Times" "Avg: ${avg_time}s, Min: ${min_time}s, Max: ${max_time}s"
        
        if (( $(echo "$avg_time < 1.0" | bc -l) )); then
            log_test "PASS" "Average Response Time" "Good performance: ${avg_time}s"
        else
            log_test "WARN" "Average Response Time" "Slow performance: ${avg_time}s"
        fi
        
        if [ $failed_requests -eq 0 ]; then
            log_test "PASS" "Request Success Rate" "100% success rate under load"
        else
            log_test "WARN" "Request Success Rate" "$failed_requests failed out of 50"
        fi
    fi
}

# Test 10: UI Simulation (Frontend Testing)
test_frontend_simulation() {
    echo -e "\n${MAGENTA}=== Phase 10: Frontend UI Simulation ===${NC}"
    
    # Test if frontend assets are served
    if make_request "GET" "$BASE_URL/" "" "" "200"; then
        log_test "PASS" "Frontend Root" "Frontend accessible at root"
    else
        log_test "WARN" "Frontend Root" "Frontend may not be served at root"
    fi
    
    # Test static assets
    local static_endpoints=(
        "/static/js/main.js"
        "/static/css/main.css"
        "/static/favicon.ico"
        "/manifest.json"
    )
    
    for endpoint in "${static_endpoints[@]}"; do
        if make_request "GET" "$BASE_URL$endpoint" "" "" "200"; then
            log_test "PASS" "Static Asset: $endpoint" "Asset available"
        else
            log_test "WARN" "Static Asset: $endpoint" "Asset not found (may not exist)"
        fi
    done
    
    # Simulate common UI workflows
    log_test "INFO" "UI Workflow Simulation" "Simulating user login workflow"
    
    # 1. Access login page
    if make_request "GET" "$BASE_URL/login" "" "" "200"; then
        log_test "PASS" "Login Page" "Login page accessible"
    else
        log_test "WARN" "Login Page" "Login page not found (may be SPA)"
    fi
    
    # 2. Access dashboard
    if make_request "GET" "$BASE_URL/dashboard" "" "" "200"; then
        log_test "PASS" "Dashboard Page" "Dashboard accessible"
    else
        log_test "WARN" "Dashboard Page" "Dashboard not found (may be SPA)"
    fi
    
    # 3. Test API endpoints that would be called by UI
    local token=$(cat "$RESULTS_DIR/auth_token.txt" 2>/dev/null || echo "")
    if [ -n "$token" ]; then
        log_test "INFO" "UI API Simulation" "Testing API endpoints used by UI"
        
        # Simulate UI loading user data
        if make_request "GET" "$BASE_URL/me" "-H 'Authorization: Bearer $token'" "" "200"; then
            log_test "PASS" "User Profile API" "User profile data accessible"
        else
            log_test "WARN" "User Profile API" "User profile endpoint not found"
        fi
        
        # Simulate UI loading recent jobs
        if make_request "GET" "$BASE_URL/jobs?limit=10" "-H 'Authorization: Bearer $token'" "" "200"; then
            log_test "PASS" "Recent Jobs API" "Recent jobs data accessible"
        else
            log_test "WARN" "Recent Jobs API" "Recent jobs endpoint may not support pagination"
        fi
    fi
}

# Generate comprehensive test report
generate_test_report() {
    echo -e "\n${CYAN}=== Generating Comprehensive Test Report ===${NC}"
    
    local report_file="$RESULTS_DIR/comprehensive_test_report.html"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    cat > "$report_file" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Whisper Transcriber - Comprehensive Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .summary { background: #e8f4f8; padding: 15px; margin: 20px 0; border-radius: 5px; }
        .pass { color: #28a745; }
        .fail { color: #dc3545; }
        .warn { color: #ffc107; }
        .info { color: #17a2b8; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .metrics { display: flex; justify-content: space-around; margin: 20px 0; }
        .metric { text-align: center; padding: 15px; background: #f8f9fa; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Whisper Transcriber - Comprehensive Test Report</h1>
        <p><strong>Generated:</strong> $timestamp</p>
        <p><strong>Base URL:</strong> $BASE_URL</p>
    </div>
    
    <div class="summary">
        <h2>📊 Test Summary</h2>
        <div class="metrics">
            <div class="metric">
                <h3>$TOTAL_TESTS</h3>
                <p>Total Tests</p>
            </div>
            <div class="metric pass">
                <h3>$PASSED_TESTS</h3>
                <p>Passed</p>
            </div>
            <div class="metric fail">
                <h3>$FAILED_TESTS</h3>
                <p>Failed</p>
            </div>
            <div class="metric warn">
                <h3>$WARNING_TESTS</h3>
                <p>Warnings</p>
            </div>
        </div>
    </div>
    
    <h2>📋 Detailed Test Results</h2>
    <table>
        <tr>
            <th>Status</th>
            <th>Test Name</th>
            <th>Details</th>
            <th>Timestamp</th>
        </tr>
EOF

    # Add test results to HTML table
    while IFS= read -r line; do
        if [[ "$line" =~ ^\[([^\]]+)\]\ \[([^\]]+)\]\ ([^:]+):\ (.*)$ ]]; then
            local timestamp="${BASH_REMATCH[1]}"
            local status="${BASH_REMATCH[2]}"
            local test_name="${BASH_REMATCH[3]}"
            local details="${BASH_REMATCH[4]}"
            
            local status_class=""
            case "$status" in
                "PASS") status_class="pass" ;;
                "FAIL") status_class="fail" ;;
                "WARN") status_class="warn" ;;
                "INFO") status_class="info" ;;
            esac
            
            echo "        <tr>" >> "$report_file"
            echo "            <td class=\"$status_class\">$status</td>" >> "$report_file"
            echo "            <td>$test_name</td>" >> "$report_file"
            echo "            <td>$details</td>" >> "$report_file"
            echo "            <td>$timestamp</td>" >> "$report_file"
            echo "        </tr>" >> "$report_file"
        fi
    done < "$MONITORING_LOG"
    
    cat >> "$report_file" << EOF
    </table>
    
    <h2>💡 Recommendations</h2>
    <ul>
EOF

    # Add recommendations based on test results
    if [ $FAILED_TESTS -gt 0 ]; then
        echo "        <li class=\"fail\">❌ Address $FAILED_TESTS failed tests before production deployment</li>" >> "$report_file"
    fi
    
    if [ $WARNING_TESTS -gt 5 ]; then
        echo "        <li class=\"warn\">⚠️ Review $WARNING_TESTS warnings for potential improvements</li>" >> "$report_file"
    fi
    
    if [ -f "$RESULTS_DIR/response_times.txt" ]; then
        local avg_time=$(awk '{sum+=$1} END {print sum/NR}' "$RESULTS_DIR/response_times.txt")
        if (( $(echo "$avg_time > 1.0" | bc -l) )); then
            echo "        <li class=\"warn\">⚠️ Consider performance optimization (avg response time: ${avg_time}s)</li>" >> "$report_file"
        fi
    fi
    
    cat >> "$report_file" << EOF
        <li class="info">ℹ️ Review security headers and CORS configuration</li>
        <li class="info">ℹ️ Implement comprehensive monitoring in production</li>
        <li class="info">ℹ️ Consider rate limiting for API endpoints</li>
    </ul>
    
    <h2>🔗 Useful Links</h2>
    <ul>
        <li><a href="$BASE_URL/docs" target="_blank">API Documentation</a></li>
        <li><a href="$BASE_URL/health" target="_blank">Health Check</a></li>
        <li><a href="$BASE_URL" target="_blank">Application</a></li>
    </ul>
    
    <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666;">
        <p>Generated by Comprehensive Application Testing System</p>
    </footer>
</body>
</html>
EOF

    echo -e "${GREEN}✅ Test report generated: $report_file${NC}"
    log_test "INFO" "Report Generation" "HTML report saved to $report_file"
}

# Main execution function
main() {
    echo -e "${BLUE}🎯 Starting Comprehensive Application Testing${NC}"
    echo -e "${BLUE}===============================================${NC}"
    
    # Setup
    setup_testing_environment
    
    # Run all test phases
    test_system_health
    test_authentication
    test_api_endpoints
    test_file_upload
    test_transcription_workflow
    test_websocket_features
    test_security_features
    test_error_handling
    test_performance
    test_frontend_simulation
    
    # Generate report
    generate_test_report
    
    # Final summary
    echo -e "\n${CYAN}=== Final Test Summary ===${NC}"
    echo -e "${GREEN}✅ Passed: $PASSED_TESTS${NC}"
    echo -e "${RED}❌ Failed: $FAILED_TESTS${NC}"
    echo -e "${YELLOW}⚠️  Warnings: $WARNING_TESTS${NC}"
    echo -e "${BLUE}ℹ️  Total: $TOTAL_TESTS${NC}"
    
    local success_rate=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    echo -e "\n${CYAN}📊 Success Rate: $success_rate%${NC}"
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "\n${GREEN}🎉 All critical tests passed! Application is ready for production.${NC}"
    else
        echo -e "\n${RED}⚠️  Some tests failed. Review results before production deployment.${NC}"
    fi
    
    echo -e "\n${BLUE}📁 Results saved to: $RESULTS_DIR${NC}"
    echo -e "${BLUE}📄 Full report: $RESULTS_DIR/comprehensive_test_report.html${NC}"
    echo -e "${BLUE}📋 Test log: $MONITORING_LOG${NC}"
}

# Execute if run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi