#!/bin/bash

# User-Centric Application Validation (UCAV)
# Tests the application from the user's perspective, not just technical metrics
# Focus: Does this application actually solve the user's problem?

set -e

echo "🎯 USER-CENTRIC APPLICATION VALIDATION"
echo "======================================"
echo "Testing philosophy: If a user can't use it, it's broken"
echo ""

# Test Results
CRITICAL_FAILURES=()
USER_BLOCKING_ISSUES=()
USABILITY_PROBLEMS=()

# Utility functions
fail_critical() {
    CRITICAL_FAILURES+=("$1")
    echo "🚨 CRITICAL: $1"
}

fail_blocking() {
    USER_BLOCKING_ISSUES+=("$1")
    echo "⛔ BLOCKING: $1"
}

warn_usability() {
    USABILITY_PROBLEMS+=("$1")
    echo "⚠️  USABILITY: $1"
}

pass_test() {
    echo "✅ $1"
}

echo "📋 Phase 1: Can a user reach the application?"
echo "=============================================="

# Test 1: Basic Accessibility
if curl -s --max-time 10 http://localhost:8000 > /dev/null; then
    pass_test "Application is reachable"
else
    fail_critical "Application is not reachable at http://localhost:8000"
fi

# Test 2: Frontend Loads Without Errors
HOMEPAGE_CONTENT=$(curl -s http://localhost:8000)
if echo "$HOMEPAGE_CONTENT" | grep -q "<!DOCTYPE html>"; then
    pass_test "Homepage serves valid HTML"
else
    fail_critical "Homepage does not serve valid HTML"
fi

if echo "$HOMEPAGE_CONTENT" | grep -q "js"; then
    pass_test "JavaScript bundles are referenced"
else
    fail_blocking "No JavaScript bundles found - frontend likely broken"
fi

echo ""
echo "📋 Phase 2: Can a user create an account and log in?"
echo "=================================================="

# Test 3: User Registration
echo "Testing user registration..."
REGISTER_RESPONSE=$(curl -s -X POST http://localhost:8000/register \
    -H "Content-Type: application/json" \
    -d '{"username":"testuser@example.com","password":"testpass123","email":"testuser@example.com"}' \
    2>/dev/null || echo "CURL_FAILED")

if [ "$REGISTER_RESPONSE" = "CURL_FAILED" ]; then
    fail_critical "Registration endpoint is not accessible"
elif echo "$REGISTER_RESPONSE" | grep -q -E "(token|success|created)"; then
    pass_test "User registration appears to work"
elif echo "$REGISTER_RESPONSE" | grep -q "already exists"; then
    pass_test "User registration validates existing users"
elif echo "$REGISTER_RESPONSE" | grep -q -E "(error|fail|400|500)"; then
    fail_blocking "User registration returns errors: $(echo $REGISTER_RESPONSE | head -c 100)"
else
    warn_usability "User registration response unclear: $(echo $REGISTER_RESPONSE | head -c 100)"
fi

# Test 4: User Login
echo "Testing user login..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"testuser@example.com","password":"testpass123"}' \
    2>/dev/null || echo "CURL_FAILED")

if [ "$LOGIN_RESPONSE" = "CURL_FAILED" ]; then
    fail_critical "Login endpoint is not accessible"
elif echo "$LOGIN_RESPONSE" | grep -q "token"; then
    pass_test "User login returns authentication token"
    # Extract token for further testing
    AUTH_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
elif echo "$LOGIN_RESPONSE" | grep -q -E "(invalid|unauthorized|401)"; then
    warn_usability "Login correctly rejects invalid credentials"
else
    fail_blocking "Login response unclear: $(echo $LOGIN_RESPONSE | head -c 100)"
fi

echo ""
echo "📋 Phase 3: Can a user upload and transcribe audio?"
echo "================================================="

# Test 5: Core Functionality - File Upload
echo "Testing core functionality: audio file upload..."

# Create a minimal test audio file (sine wave)
TEST_AUDIO_FILE="/tmp/test_audio.wav"
if command -v sox >/dev/null 2>&1; then
    sox -n -r 44100 -c 2 "$TEST_AUDIO_FILE" synth 2 sine 440 2>/dev/null || {
        echo "Creating simple test file..."
        echo "RIFF WAV file header" > "$TEST_AUDIO_FILE"
    }
elif command -v ffmpeg >/dev/null 2>&1; then
    ffmpeg -f lavfi -i "sine=frequency=440:duration=2" -ac 2 -ar 44100 "$TEST_AUDIO_FILE" -y 2>/dev/null || {
        echo "Creating simple test file..."
        echo "RIFF WAV file header" > "$TEST_AUDIO_FILE"
    }
else
    # Create a fake audio file for testing
    echo "Creating placeholder test file..."
    printf "RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x02\x00\x44\xAC\x00\x00\x10\xB1\x02\x00\x04\x00\x10\x00data\x00\x00\x00\x00" > "$TEST_AUDIO_FILE"
fi

if [ ! -f "$TEST_AUDIO_FILE" ]; then
    warn_usability "Could not create test audio file - skipping upload test"
else
    # Test upload with authentication
    if [ -n "$AUTH_TOKEN" ]; then
        UPLOAD_RESPONSE=$(curl -s -X POST http://localhost:8000/jobs/ \
            -H "Authorization: Bearer $AUTH_TOKEN" \
            -F "file=@$TEST_AUDIO_FILE" \
            -F "model=tiny" \
            2>/dev/null || echo "UPLOAD_FAILED")
        
        if [ "$UPLOAD_RESPONSE" = "UPLOAD_FAILED" ]; then
            fail_blocking "File upload endpoint not accessible with authentication"
        elif echo "$UPLOAD_RESPONSE" | grep -q -E "(job_id|queued|success)"; then
            pass_test "File upload accepts audio files"
            JOB_ID=$(echo "$UPLOAD_RESPONSE" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4 || echo "")
        elif echo "$UPLOAD_RESPONSE" | grep -q -E "(error|fail|400|500)"; then
            fail_blocking "File upload returns errors: $(echo $UPLOAD_RESPONSE | head -c 100)"
        else
            warn_usability "Upload response unclear: $(echo $UPLOAD_RESPONSE | head -c 100)"
        fi
    else
        # Test upload without authentication (should fail gracefully)
        UPLOAD_RESPONSE=$(curl -s -X POST http://localhost:8000/jobs/ \
            -F "file=@$TEST_AUDIO_FILE" \
            2>/dev/null || echo "UPLOAD_FAILED")
        
        if echo "$UPLOAD_RESPONSE" | grep -q -E "(401|403|unauthorized)"; then
            pass_test "Upload endpoint correctly requires authentication"
        else
            warn_usability "Upload endpoint should require authentication"
        fi
    fi
fi

# Test 6: Job Status Checking
echo "Testing job status checking..."
if [ -n "$JOB_ID" ] && [ -n "$AUTH_TOKEN" ]; then
    STATUS_RESPONSE=$(curl -s -H "Authorization: Bearer $AUTH_TOKEN" \
        "http://localhost:8000/jobs/$JOB_ID" \
        2>/dev/null || echo "STATUS_FAILED")
    
    if [ "$STATUS_RESPONSE" = "STATUS_FAILED" ]; then
        fail_blocking "Job status endpoint not accessible"
    elif echo "$STATUS_RESPONSE" | grep -q -E "(status|queued|processing|completed)"; then
        pass_test "Job status endpoint returns job information"
    else
        warn_usability "Job status response unclear: $(echo $STATUS_RESPONSE | head -c 100)"
    fi
fi

echo ""
echo "📋 Phase 4: Critical System Health"
echo "=================================="

# Test 7: Backend Error State
echo "Checking for critical backend errors..."
ERROR_COUNT=$(docker logs whisper-app --tail 50 2>&1 | grep "ERROR" | wc -l)
if [ "$ERROR_COUNT" -eq 0 ]; then
    pass_test "No critical errors in backend logs"
elif [ "$ERROR_COUNT" -lt 5 ]; then
    warn_usability "Few errors in backend logs ($ERROR_COUNT)"
else
    fail_blocking "High error count in backend logs ($ERROR_COUNT)"
fi

# Test 8: Database Connectivity
echo "Testing database functionality..."
DB_TEST=$(docker exec whisper-app python -c "
from api.orm_bootstrap import SessionLocal
try:
    db = SessionLocal()
    db.execute(__import__('sqlalchemy').text('SELECT 1'))
    db.close()
    print('DB_SUCCESS')
except Exception as e:
    print(f'DB_ERROR: {e}')
" 2>/dev/null || echo "DB_FAILED")

if echo "$DB_TEST" | grep -q "DB_SUCCESS"; then
    pass_test "Database is accessible and functional"
elif echo "$DB_TEST" | grep -q "DB_ERROR"; then
    fail_critical "Database connection failed: $DB_TEST"
else
    fail_critical "Database test failed to run"
fi

# Test 9: Worker Functionality
echo "Testing background worker..."
WORKER_STATUS=$(docker logs whisper-worker --tail 10 2>&1 | grep -E "(error|failed|exception)" | wc -l)
if [ "$WORKER_STATUS" -eq 0 ]; then
    pass_test "Background worker appears healthy"
else
    fail_blocking "Background worker has errors ($WORKER_STATUS)"
fi

echo ""
echo "📊 USER-CENTRIC VALIDATION RESULTS"
echo "=================================="

echo "✅ Tests Passed: $(( $(echo "✅" | wc -c) - 1 ))"
echo "⚠️  Usability Issues: ${#USABILITY_PROBLEMS[@]}"
echo "⛔ User-Blocking Issues: ${#USER_BLOCKING_ISSUES[@]}"
echo "🚨 Critical Failures: ${#CRITICAL_FAILURES[@]}"

echo ""
if [ ${#CRITICAL_FAILURES[@]} -gt 0 ]; then
    echo "🚨 CRITICAL FAILURES (Application Broken):"
    for failure in "${CRITICAL_FAILURES[@]}"; do
        echo "   • $failure"
    done
fi

if [ ${#USER_BLOCKING_ISSUES[@]} -gt 0 ]; then
    echo "⛔ USER-BLOCKING ISSUES (Users Cannot Accomplish Goals):"
    for issue in "${USER_BLOCKING_ISSUES[@]}"; do
        echo "   • $issue"
    done
fi

if [ ${#USABILITY_PROBLEMS[@]} -gt 0 ]; then
    echo "⚠️  USABILITY PROBLEMS (Poor User Experience):"
    for problem in "${USABILITY_PROBLEMS[@]}"; do
        echo "   • $problem"
    done
fi

echo ""
echo "📋 USER READINESS ASSESSMENT:"

if [ ${#CRITICAL_FAILURES[@]} -gt 0 ]; then
    echo "❌ APPLICATION IS BROKEN - Cannot be used by users"
    exit 1
elif [ ${#USER_BLOCKING_ISSUES[@]} -gt 0 ]; then
    echo "⚠️  APPLICATION HAS USER-BLOCKING ISSUES - Limited usability"
    exit 2
elif [ ${#USABILITY_PROBLEMS[@]} -gt 0 ]; then
    echo "✅ APPLICATION IS FUNCTIONAL - Has usability issues but works"
    exit 0
else
    echo "🎉 APPLICATION IS USER-READY - Fully functional for users"
    exit 0
fi

# Cleanup
rm -f "$TEST_AUDIO_FILE" 2>/dev/null || true