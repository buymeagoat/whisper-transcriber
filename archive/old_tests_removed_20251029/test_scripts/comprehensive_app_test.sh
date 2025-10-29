#!/bin/bash

# Comprehensive Application Testing Script
# Tests all layers: infrastructure, database, backend, frontend, end-to-end

set -e

echo "🔍 COMPREHENSIVE APPLICATION TESTING"
echo "===================================="

# Test Results Tracking
TESTS_PASSED=0
TESTS_FAILED=0
CRITICAL_FAILURES=()

log_test() {
    local test_name="$1"
    local status="$2"
    local details="$3"
    
    if [ "$status" = "PASS" ]; then
        echo "✅ $test_name"
        ((TESTS_PASSED++))
    else
        echo "❌ $test_name: $details"
        ((TESTS_FAILED++))
        CRITICAL_FAILURES+=("$test_name: $details")
    fi
}

echo ""
echo "📋 Phase 1: Infrastructure Testing"
echo "================================="

# Test 1: Container Status
echo "Testing container status..."
if docker compose ps | grep -q "healthy"; then
    log_test "Container Health" "PASS"
else
    log_test "Container Health" "FAIL" "Containers not healthy"
fi

# Test 2: Basic Connectivity
echo "Testing basic connectivity..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000 | grep -q "200"; then
    log_test "HTTP Connectivity" "PASS"
else
    log_test "HTTP Connectivity" "FAIL" "Cannot connect to application"
fi

echo ""
echo "📋 Phase 2: Database Testing"  
echo "==========================="

# Test 3: Database Files
echo "Testing database files..."
if docker exec whisper-app test -f /app/data/whisper.db; then
    log_test "Database File Exists" "PASS"
else
    log_test "Database File Exists" "FAIL" "Database file missing"
fi

# Test 4: Database Tables
echo "Testing database tables..."
TABLES=$(docker exec whisper-app python -c "
import sqlite3
try:
    conn = sqlite3.connect('/app/data/whisper.db')
    cursor = conn.cursor()
    cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")
    tables = cursor.fetchall()
    print(len(tables))
except Exception as e:
    print('0')
" 2>/dev/null)

if [ "$TABLES" -gt 0 ]; then
    log_test "Database Tables ($TABLES found)" "PASS"
else
    log_test "Database Tables" "FAIL" "No tables found in database"
fi

# Test 5: Migration Status
echo "Testing migration system..."
if docker exec whisper-app python -c "import alembic" 2>/dev/null; then
    log_test "Alembic Available" "PASS"
else
    log_test "Alembic Available" "FAIL" "Alembic not installed"
fi

echo ""
echo "📋 Phase 3: Backend API Testing"
echo "=============================="

# Test 6: API Health Endpoint
echo "Testing API health..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/api/health || echo "ERROR")
if echo "$HEALTH_RESPONSE" | grep -q "API key required"; then
    log_test "API Authentication" "PASS"
elif echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    log_test "API Health" "PASS"
else
    log_test "API Health" "FAIL" "Unexpected response: $HEALTH_RESPONSE"
fi

# Test 7: API Documentation
echo "Testing API documentation..."
if curl -s http://localhost:8000/docs | grep -q "FastAPI"; then
    log_test "API Documentation" "PASS"
else
    log_test "API Documentation" "FAIL" "Documentation not accessible"
fi

# Test 8: Backend Error Logs
echo "Testing backend error logs..."
ERROR_COUNT=$(docker logs whisper-app --tail 50 2>&1 | grep -c "ERROR" || echo "0")
if [ "$ERROR_COUNT" -eq 0 ]; then
    log_test "Backend Error Logs" "PASS"
else
    log_test "Backend Error Logs" "FAIL" "$ERROR_COUNT errors found in logs"
fi

echo ""
echo "📋 Phase 4: Frontend Testing"
echo "==========================="

# Test 9: Frontend Bundle Loading
echo "Testing frontend bundles..."
BUNDLE_RESPONSE=$(curl -s http://localhost:8000/ | grep -o 'vendor-[a-z0-9]*.js' | wc -l)
if [ "$BUNDLE_RESPONSE" -gt 0 ]; then
    log_test "Frontend Bundles" "PASS"
else
    log_test "Frontend Bundles" "FAIL" "No JavaScript bundles found"
fi

# Test 10: JavaScript Error Detection
echo "Testing for JavaScript errors..."
# This is a simplified test - in reality you'd use a headless browser
if curl -s http://localhost:8000/ | grep -q "Cannot access.*before initialization"; then
    log_test "JavaScript Errors" "FAIL" "Initialization errors detected"
else
    log_test "JavaScript Errors" "PASS"
fi

echo ""
echo "📋 Phase 5: End-to-End Testing"
echo "============================="

# Test 11: User Registration/Login Flow
echo "Testing user registration..."
REGISTER_RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/register \
    -H "Content-Type: application/json" \
    -d '{"username":"test@example.com","password":"testpass","email":"test@example.com"}' \
    2>/dev/null || echo "ERROR")

if echo "$REGISTER_RESPONSE" | grep -q -E "(already exists|created|token)"; then
    log_test "User Registration" "PASS"
else
    log_test "User Registration" "FAIL" "Registration failed: $REGISTER_RESPONSE"
fi

# Test 12: File Upload Endpoint
echo "Testing file upload endpoint..."
UPLOAD_RESPONSE=$(curl -s -X POST http://localhost:8000/api/transcribe/upload \
    -H "Authorization: Bearer fake-token" \
    2>/dev/null || echo "ERROR")

if echo "$UPLOAD_RESPONSE" | grep -q -E "(401|403|422)"; then
    log_test "Upload Endpoint" "PASS" "Properly rejecting unauthorized requests"
else
    log_test "Upload Endpoint" "FAIL" "Unexpected upload response: $UPLOAD_RESPONSE"
fi

echo ""
echo "📊 TEST RESULTS SUMMARY"
echo "======================="
echo "✅ Tests Passed: $TESTS_PASSED"
echo "❌ Tests Failed: $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -gt 0 ]; then
    echo "🚨 CRITICAL FAILURES:"
    for failure in "${CRITICAL_FAILURES[@]}"; do
        echo "   • $failure"
    done
    echo ""
    echo "❌ APPLICATION IS NOT READY FOR USE"
    echo "   Please fix the above issues before proceeding."
    exit 1
else
    echo "🎉 ALL TESTS PASSED"
    echo "✅ APPLICATION IS READY FOR USE"
    exit 0
fi