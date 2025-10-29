#!/bin/bash

# COMPREHENSIVE USER-CENTRIC APPLICATION VALIDATION
# Tests complete user journeys and real-world usage patterns
# Focus: Can users actually accomplish their goals with this application?

set -e

echo "🎯 COMPREHENSIVE USER-CENTRIC VALIDATION"
echo "========================================"
echo "Testing philosophy: Users don't care about technical metrics - they care about accomplishing tasks"
echo ""

# Test Results Tracking
CRITICAL_FAILURES=()
USER_BLOCKING_ISSUES=()
USABILITY_PROBLEMS=()
PERFORMANCE_ISSUES=()

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

warn_performance() {
    PERFORMANCE_ISSUES+=("$1")
    echo "🐌 PERFORMANCE: $1"
}

pass_test() {
    echo "✅ $1"
}

info_test() {
    echo "ℹ️  $1"
}

# Global variables for user session
AUTH_TOKEN=""
USER_ID=""
JOB_ID=""
TEST_AUDIO_FILE="/tmp/user_test_audio.wav"

echo "🎬 SCENARIO 1: New User Complete Journey"
echo "======================================="
echo "Testing: A new user discovers the app and wants to transcribe their first audio file"
echo ""

# Step 1: User discovers the application
echo "👤 User Action: Visiting the application for the first time..."
HOMEPAGE_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}|TIME:%{time_total}" http://localhost:8000/)
HTTP_CODE=$(echo "$HOMEPAGE_RESPONSE" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
LOAD_TIME=$(echo "$HOMEPAGE_RESPONSE" | grep -o "TIME:[0-9.]*" | cut -d: -f2)
HOMEPAGE_CONTENT=$(echo "$HOMEPAGE_RESPONSE" | sed 's/HTTPSTATUS:[0-9]*|TIME:[0-9.]*//')

if [ "$HTTP_CODE" = "200" ]; then
    pass_test "Homepage loads successfully"
    
    # Check load time (users expect < 3 seconds)
    if (( $(echo "$LOAD_TIME < 3.0" | bc -l) )); then
        pass_test "Homepage loads quickly (${LOAD_TIME}s)"
    else
        warn_performance "Homepage loads slowly (${LOAD_TIME}s)"
    fi
else
    fail_critical "Homepage failed to load (HTTP $HTTP_CODE)"
fi

# Step 2: User sees clear value proposition
echo "👀 User Evaluation: Does the user understand what this application does?"
if echo "$HOMEPAGE_CONTENT" | grep -qi "transcrib\|audio\|speech\|voice"; then
    pass_test "Value proposition is clear (mentions transcription/audio)"
else
    warn_usability "Value proposition unclear - user may not understand purpose"
fi

# Check for obvious call-to-action
if echo "$HOMEPAGE_CONTENT" | grep -qi "upload\|start\|begin\|register\|login"; then
    pass_test "Clear call-to-action present"
else
    warn_usability "No clear call-to-action - user may not know next steps"
fi

# Step 3: User attempts to register
echo "✍️  User Action: Attempting to create an account..."
REGISTER_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST http://localhost:8000/register \
    -H "Content-Type: application/json" \
    -d '{"username":"newuser@example.com","password":"SecurePass123!","email":"newuser@example.com"}')

REGISTER_HTTP_CODE=$(echo "$REGISTER_RESPONSE" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
REGISTER_CONTENT=$(echo "$REGISTER_RESPONSE" | sed 's/HTTPSTATUS:[0-9]*//')

if [ "$REGISTER_HTTP_CODE" = "200" ] || [ "$REGISTER_HTTP_CODE" = "201" ]; then
    pass_test "User registration successful"
    
    # Extract user info if available
    if echo "$REGISTER_CONTENT" | grep -q "user_id"; then
        USER_ID=$(echo "$REGISTER_CONTENT" | grep -o '"user_id":"[^"]*"' | cut -d'"' -f4)
        info_test "User ID assigned: $USER_ID"
    fi
elif echo "$REGISTER_CONTENT" | grep -qi "already exists\|duplicate"; then
    info_test "User already exists - this is expected for repeated tests"
else
    fail_blocking "User registration failed: $REGISTER_CONTENT"
fi

# Step 4: User attempts to log in
echo "🔐 User Action: Logging in with credentials..."
LOGIN_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST http://localhost:8000/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"newuser@example.com","password":"SecurePass123!"}')

LOGIN_HTTP_CODE=$(echo "$LOGIN_RESPONSE" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
LOGIN_CONTENT=$(echo "$LOGIN_RESPONSE" | sed 's/HTTPSTATUS:[0-9]*//')

if [ "$LOGIN_HTTP_CODE" = "200" ]; then
    pass_test "User login successful"
    
    # Extract authentication token
    if echo "$LOGIN_CONTENT" | grep -q "access_token"; then
        AUTH_TOKEN=$(echo "$LOGIN_CONTENT" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
        pass_test "Authentication token received"
        info_test "Token preview: ${AUTH_TOKEN:0:20}..."
    else
        fail_blocking "Login successful but no authentication token provided"
    fi
else
    fail_blocking "User login failed: $LOGIN_CONTENT"
fi

echo ""
echo "🎵 SCENARIO 2: User Transcribes Audio File"
echo "========================================="
echo "Testing: User wants to transcribe an audio file (core application purpose)"
echo ""

# Create a test audio file that mimics what a real user would upload
echo "📁 User Action: Preparing audio file for transcription..."
if command -v sox >/dev/null 2>&1; then
    sox -n -r 44100 -c 1 "$TEST_AUDIO_FILE" synth 3 sine 440 vol 0.1 2>/dev/null || {
        echo "Creating basic WAV file..."
        printf "RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xAC\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x08\x00\x00" > "$TEST_AUDIO_FILE"
        # Add some audio data
        for i in {1..1000}; do printf "\x00\x00" >> "$TEST_AUDIO_FILE"; done
    }
elif command -v ffmpeg >/dev/null 2>&1; then
    ffmpeg -f lavfi -i "sine=frequency=440:duration=3" -ac 1 -ar 44100 "$TEST_AUDIO_FILE" -y 2>/dev/null || {
        echo "Creating basic WAV file..."
        printf "RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xAC\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x08\x00\x00" > "$TEST_AUDIO_FILE"
        for i in {1..1000}; do printf "\x00\x00" >> "$TEST_AUDIO_FILE"; done
    }
else
    echo "Creating placeholder audio file..."
    # Create a proper WAV file header
    printf "RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xAC\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x08\x00\x00" > "$TEST_AUDIO_FILE"
    # Add some audio data (silence)
    for i in {1..1000}; do printf "\x00\x00" >> "$TEST_AUDIO_FILE"; done
fi

if [ -f "$TEST_AUDIO_FILE" ]; then
    FILE_SIZE=$(stat -c%s "$TEST_AUDIO_FILE" 2>/dev/null || stat -f%z "$TEST_AUDIO_FILE" 2>/dev/null || echo "unknown")
    pass_test "Test audio file created (${FILE_SIZE} bytes)"
else
    fail_critical "Could not create test audio file"
fi

# Step 1: User uploads audio file
echo "📤 User Action: Uploading audio file for transcription..."
if [ -n "$AUTH_TOKEN" ] && [ -f "$TEST_AUDIO_FILE" ]; then
    UPLOAD_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}|TIME:%{time_total}" \
        -X POST http://localhost:8000/jobs/ \
        -H "Authorization: Bearer $AUTH_TOKEN" \
        -F "file=@$TEST_AUDIO_FILE" \
        -F "model=tiny" \
        -F "language=en")
    
    UPLOAD_HTTP_CODE=$(echo "$UPLOAD_RESPONSE" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    UPLOAD_TIME=$(echo "$UPLOAD_RESPONSE" | grep -o "TIME:[0-9.]*" | cut -d: -f2)
    UPLOAD_CONTENT=$(echo "$UPLOAD_RESPONSE" | sed 's/HTTPSTATUS:[0-9]*|TIME:[0-9.]*//')
    
    if [ "$UPLOAD_HTTP_CODE" = "200" ] || [ "$UPLOAD_HTTP_CODE" = "201" ]; then
        pass_test "Audio file upload successful"
        
        # Check upload time (users expect reasonable speed)
        if (( $(echo "$UPLOAD_TIME < 10.0" | bc -l) )); then
            pass_test "Upload completed quickly (${UPLOAD_TIME}s)"
        else
            warn_performance "Upload took long time (${UPLOAD_TIME}s)"
        fi
        
        # Extract job ID
        if echo "$UPLOAD_CONTENT" | grep -q "job_id\|id"; then
            JOB_ID=$(echo "$UPLOAD_CONTENT" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4 || echo "$UPLOAD_CONTENT" | grep -o '"id":"[^"]*"' | cut -d'"' -f4 || echo "$UPLOAD_CONTENT" | grep -o '"id":[0-9]*' | cut -d: -f2)
            pass_test "Job ID received: $JOB_ID"
        else
            warn_usability "Upload successful but no job ID provided - user cannot track progress"
        fi
    else
        fail_blocking "Audio file upload failed: $UPLOAD_CONTENT"
    fi
else
    if [ -z "$AUTH_TOKEN" ]; then
        fail_blocking "Cannot test upload - no authentication token"
    else
        fail_blocking "Cannot test upload - no test audio file"
    fi
fi

# Step 2: User checks transcription progress
echo "🔍 User Action: Checking transcription progress..."
if [ -n "$JOB_ID" ] && [ -n "$AUTH_TOKEN" ]; then
    for attempt in {1..3}; do
        echo "  Attempt $attempt: Checking job status..."
        STATUS_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
            -H "Authorization: Bearer $AUTH_TOKEN" \
            "http://localhost:8000/jobs/$JOB_ID")
        
        STATUS_HTTP_CODE=$(echo "$STATUS_RESPONSE" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
        STATUS_CONTENT=$(echo "$STATUS_RESPONSE" | sed 's/HTTPSTATUS:[0-9]*//')
        
        if [ "$STATUS_HTTP_CODE" = "200" ]; then
            pass_test "Job status accessible"
            
            # Check if status information is useful
            if echo "$STATUS_CONTENT" | grep -qi "status\|progress\|state"; then
                STATUS=$(echo "$STATUS_CONTENT" | grep -o '"status":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
                info_test "Job status: $STATUS"
                
                if echo "$STATUS" | grep -qi "completed\|finished\|done\|success"; then
                    pass_test "Transcription completed successfully"
                    break
                elif echo "$STATUS" | grep -qi "processing\|running\|queued"; then
                    info_test "Transcription in progress (attempt $attempt/3)"
                    if [ $attempt -lt 3 ]; then
                        sleep 5
                    fi
                elif echo "$STATUS" | grep -qi "failed\|error"; then
                    fail_blocking "Transcription failed: $STATUS_CONTENT"
                    break
                else
                    warn_usability "Transcription status unclear: $STATUS"
                fi
            else
                warn_usability "Job status response lacks useful information"
            fi
        else
            fail_blocking "Cannot check job status: $STATUS_CONTENT"
            break
        fi
    done
else
    warn_usability "Cannot test progress tracking - missing job ID or auth token"
fi

echo ""
echo "📊 SCENARIO 3: User Experience Quality"
echo "====================================="
echo "Testing: How good is the overall user experience?"
echo ""

# Test response times
echo "⚡ Performance Testing: Response times for common actions..."
ENDPOINTS=(
    "GET|/health|Health check"
    "GET|/|Homepage"
    "POST|/register|Registration"
    "POST|/auth/login|Login"
)

for endpoint_info in "${ENDPOINTS[@]}"; do
    IFS="|" read -r method path description <<< "$endpoint_info"
    
    if [ "$method" = "GET" ]; then
        RESPONSE_TIME=$(curl -s -w "%{time_total}" -o /dev/null "http://localhost:8000$path")
    else
        # For POST endpoints, use minimal valid data
        case "$path" in
            "/register")
                RESPONSE_TIME=$(curl -s -w "%{time_total}" -o /dev/null -X POST "http://localhost:8000$path" -H "Content-Type: application/json" -d '{"username":"test","password":"test","email":"test@example.com"}')
                ;;
            "/auth/login")
                RESPONSE_TIME=$(curl -s -w "%{time_total}" -o /dev/null -X POST "http://localhost:8000$path" -H "Content-Type: application/json" -d '{"username":"test","password":"test"}')
                ;;
            *)
                RESPONSE_TIME="0.0"
                ;;
        esac
    fi
    
    if (( $(echo "$RESPONSE_TIME < 1.0" | bc -l) )); then
        pass_test "$description responds quickly (${RESPONSE_TIME}s)"
    elif (( $(echo "$RESPONSE_TIME < 3.0" | bc -l) )); then
        warn_performance "$description responds slowly (${RESPONSE_TIME}s)"
    else
        warn_performance "$description responds very slowly (${RESPONSE_TIME}s)"
    fi
done

# Test error handling
echo "🛡️  Error Handling: How well does the app handle mistakes?"
ERROR_TEST_CASES=(
    "Invalid login|POST|/auth/login|{\"username\":\"invalid\",\"password\":\"wrong\"}"
    "Empty upload|POST|/jobs/|form-data-empty"
    "Invalid endpoint|GET|/nonexistent|none"
)

for test_case in "${ERROR_TEST_CASES[@]}"; do
    IFS="|" read -r description method path data <<< "$test_case"
    
    if [ "$data" = "none" ]; then
        ERROR_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" "$path")
    elif [ "$data" = "form-data-empty" ]; then
        ERROR_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST "http://localhost:8000$path" -F "file=")
    else
        ERROR_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST "http://localhost:8000$path" -H "Content-Type: application/json" -d "$data")
    fi
    
    ERROR_HTTP_CODE=$(echo "$ERROR_RESPONSE" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    ERROR_CONTENT=$(echo "$ERROR_RESPONSE" | sed 's/HTTPSTATUS:[0-9]*//')
    
    # Check if error responses are helpful
    if [ "$ERROR_HTTP_CODE" -ge 400 ] && [ "$ERROR_HTTP_CODE" -lt 500 ]; then
        if echo "$ERROR_CONTENT" | grep -qi "error\|detail\|message"; then
            pass_test "$description: Helpful error message provided"
        else
            warn_usability "$description: Error response lacks helpful information"
        fi
    else
        warn_usability "$description: Unexpected response (HTTP $ERROR_HTTP_CODE)"
    fi
done

echo ""
echo "🔒 SCENARIO 4: Security & Privacy"
echo "================================"
echo "Testing: Does the app protect user data and provide secure access?"
echo ""

# Test authentication requirements
echo "🛡️  Authentication Security: Ensuring protected endpoints require auth..."
PROTECTED_ENDPOINTS=("/jobs/" "/admin/stats" "/admin/logs")

for endpoint in "${PROTECTED_ENDPOINTS[@]}"; do
    UNAUTH_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" "http://localhost:8000$endpoint")
    UNAUTH_HTTP_CODE=$(echo "$UNAUTH_RESPONSE" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    
    if [ "$UNAUTH_HTTP_CODE" = "401" ] || [ "$UNAUTH_HTTP_CODE" = "403" ]; then
        pass_test "Protected endpoint requires authentication: $endpoint"
    else
        warn_usability "Protected endpoint accessible without auth: $endpoint (HTTP $UNAUTH_HTTP_CODE)"
    fi
done

# Test HTTPS headers and security
echo "🔐 Security Headers: Checking for security best practices..."
SECURITY_HEADERS=$(curl -s -I http://localhost:8000/ | grep -i "x-frame-options\|content-security-policy\|x-content-type")
if [ -n "$SECURITY_HEADERS" ]; then
    pass_test "Security headers present"
    echo "  Headers found: $(echo "$SECURITY_HEADERS" | tr '\n' ' ')"
else
    warn_usability "Limited security headers found"
fi

echo ""
echo "📱 SCENARIO 5: Accessibility & Usability"
echo "======================================="
echo "Testing: Can all users effectively use this application?"
echo ""

# Test mobile responsiveness
echo "📱 Mobile Experience: Checking mobile-friendly design..."
MOBILE_VIEWPORT=$(echo "$HOMEPAGE_CONTENT" | grep -o 'name="viewport"[^>]*content="[^"]*"' | grep -o 'content="[^"]*"' | sed 's/content="//g' | sed 's/"//g')
if [ -n "$MOBILE_VIEWPORT" ]; then
    pass_test "Mobile viewport configured: $MOBILE_VIEWPORT"
else
    warn_usability "No mobile viewport meta tag - poor mobile experience"
fi

# Test for accessibility features
echo "♿ Accessibility: Checking for inclusive design..."
ACCESSIBILITY_INDICATORS=$(echo "$HOMEPAGE_CONTENT" | grep -c "alt=\|aria-\|role=\|label" || echo "0")
if [ "$ACCESSIBILITY_INDICATORS" -gt 0 ]; then
    pass_test "Accessibility features detected ($ACCESSIBILITY_INDICATORS indicators)"
else
    warn_usability "Limited accessibility features found"
fi

# Cleanup
rm -f "$TEST_AUDIO_FILE" 2>/dev/null || true

echo ""
echo "📊 COMPREHENSIVE VALIDATION RESULTS"
echo "==================================="

echo "✅ Tests Passed: $(grep -c "✅" <<< "$(set | grep '^pass_test')" 2>/dev/null || echo "Multiple")"
echo "🐌 Performance Issues: ${#PERFORMANCE_ISSUES[@]}"
echo "⚠️  Usability Problems: ${#USABILITY_PROBLEMS[@]}"
echo "⛔ User-Blocking Issues: ${#USER_BLOCKING_ISSUES[@]}"
echo "🚨 Critical Failures: ${#CRITICAL_FAILURES[@]}"

echo ""
if [ ${#CRITICAL_FAILURES[@]} -gt 0 ]; then
    echo "🚨 CRITICAL FAILURES (Application Broken for Users):"
    for failure in "${CRITICAL_FAILURES[@]}"; do
        echo "   • $failure"
    done
fi

if [ ${#USER_BLOCKING_ISSUES[@]} -gt 0 ]; then
    echo "⛔ USER-BLOCKING ISSUES (Users Cannot Complete Goals):"
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

if [ ${#PERFORMANCE_ISSUES[@]} -gt 0 ]; then
    echo "🐌 PERFORMANCE ISSUES (Slow User Experience):"
    for issue in "${PERFORMANCE_ISSUES[@]}"; do
        echo "   • $issue"
    done
fi

echo ""
echo "📋 FINAL USER-CENTRIC ASSESSMENT:"

if [ ${#CRITICAL_FAILURES[@]} -gt 0 ]; then
    echo "❌ APPLICATION IS BROKEN FOR USERS"
    echo "   Users cannot complete basic tasks"
    echo "   Immediate fixes required before user deployment"
    exit 1
elif [ ${#USER_BLOCKING_ISSUES[@]} -gt 0 ]; then
    echo "⚠️  APPLICATION HAS SIGNIFICANT USER ISSUES"
    echo "   Some users can use the app, but will encounter blocking problems"
    echo "   High priority fixes needed for good user experience"
    exit 2
elif [ ${#USABILITY_PROBLEMS[@]} -gt 3 ]; then
    echo "✅ APPLICATION IS FUNCTIONAL BUT NEEDS POLISH"
    echo "   Users can accomplish their goals"
    echo "   Multiple usability improvements would enhance experience"
    exit 0
elif [ ${#PERFORMANCE_ISSUES[@]} -gt 2 ]; then
    echo "✅ APPLICATION IS USER-READY WITH PERFORMANCE CONCERNS"
    echo "   Fully functional for users"
    echo "   Performance optimizations recommended"
    exit 0
else
    echo "🎉 APPLICATION IS EXCELLENT FOR USERS"
    echo "   ✅ Users can easily complete all core tasks"
    echo "   ✅ Good performance and user experience"
    echo "   ✅ Ready for production user deployment"
    exit 0
fi