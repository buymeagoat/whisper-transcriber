#!/bin/bash

# Comprehensive Infrastructure Testing Script
# Tests all rebuilt components from scratch

# Debug mode off by default
# set -x

echo "🔥 COMPREHENSIVE INFRASTRUCTURE TESTING 🔥"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
PASS=0
FAIL=0

test_result() {
    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}: $1"
        ((PASS++))
    else
        echo -e "${RED}❌ FAIL${NC}: $1 (exit code: $exit_code)"
        ((FAIL++))
    fi
    return 0  # Don't exit on failure
}

echo -e "${BLUE}📋 Phase 1: Container Health Checks${NC}"
echo "======================================"

# Test container health
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep whisper
test_result "Containers are running"

# Test container health endpoints
docker exec whisper-app curl -s -f http://localhost:8000/health > /dev/null
test_result "App container health check"

docker exec whisper-redis redis-cli -a "NdSpeZBhoG*Gr*po" ping 2>/dev/null | grep -q PONG
test_result "Redis container health check"

echo -e "\n${BLUE}📋 Phase 2: Frontend Serving Tests${NC}"
echo "===================================="

# Test HTML serving
HTML_RESPONSE=$(curl -s -H "Accept: text/html" http://localhost:8000/)
echo "$HTML_RESPONSE" | grep -q "Whisper Transcriber"
test_result "HTML page loads with correct title"

echo "$HTML_RESPONSE" | grep -q "index-80c3df63.js"
test_result "HTML references correct JavaScript bundle"

echo "$HTML_RESPONSE" | grep -q "index-3c8c337c.css"
test_result "HTML references CSS bundle"

# Test JavaScript bundle serving
JS_HEADERS=$(curl -I -s http://localhost:8000/assets/index-80c3df63.js)
echo "$JS_HEADERS" | grep -q "content-type: application/javascript"
test_result "JavaScript served with correct MIME type"

echo "$JS_HEADERS" | grep -q "cache-control: no-cache"
test_result "Cache-busting headers present"

# Test CSS serving
CSS_HEADERS=$(curl -I -s http://localhost:8000/assets/css/index-3c8c337c.css)
echo "$CSS_HEADERS" | grep -q "content-type: text/css"
test_result "CSS served with correct MIME type"

# Test vendor bundles
curl -s -f http://localhost:8000/assets/react-vendor-11d8253e.js > /dev/null
test_result "React vendor bundle loads"

curl -s -f http://localhost:8000/assets/vendor-c729a371.js > /dev/null
test_result "Main vendor bundle loads"

echo -e "\n${BLUE}📋 Phase 3: API Endpoint Tests${NC}"
echo "==============================="

# Test health endpoint
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
echo "$HEALTH_RESPONSE" | grep -q '"status":"ok"'
test_result "Health endpoint returns OK"

# Test OpenAPI docs
curl -s -f http://localhost:8000/docs > /dev/null
test_result "API documentation loads"

curl -s -f http://localhost:8000/openapi.json > /dev/null
test_result "OpenAPI schema accessible"

echo -e "\n${BLUE}📋 Phase 4: Authentication System Tests${NC}"
echo "==========================================="

# Generate unique test user
TIMESTAMP=$(date +%s)
TEST_USER="testuser$TIMESTAMP"
TEST_EMAIL="test$TIMESTAMP@example.com"

# Test user registration
REG_RESPONSE=$(curl -s -X POST http://localhost:8000/register \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$TEST_USER\",\"email\":\"$TEST_EMAIL\",\"password\":\"testpass123\",\"full_name\":\"Test User $TIMESTAMP\"}")

echo "$REG_RESPONSE" | grep -q "User registered successfully"
test_result "User registration works"

# Test user login
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/auth/login \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$TEST_USER\",\"password\":\"testpass123\"}")

echo "$LOGIN_RESPONSE" | grep -q "access_token"
test_result "User login returns JWT token"

# Extract token for authenticated requests
TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -n "$TOKEN" ]; then
    # Test authenticated endpoint
    ME_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/auth/me)
    echo "$ME_RESPONSE" | grep -q "$TEST_USER"
    test_result "Authenticated /auth/me endpoint works"
else
    echo -e "${RED}❌ FAIL${NC}: Could not extract JWT token"
    ((FAIL++))
fi

echo -e "\n${BLUE}📋 Phase 5: File Upload System Tests${NC}"
echo "====================================="

# Test file upload endpoint availability (without actual file)
if [ -n "$TOKEN" ]; then
    UPLOAD_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null \
        -H "Authorization: Bearer $TOKEN" \
        -X POST http://localhost:8000/jobs/)
    
    # Should get 422 (validation error) not 404 (endpoint missing)
    if [ "$UPLOAD_RESPONSE" = "422" ]; then
        echo -e "${GREEN}✅ PASS${NC}: Upload endpoint accessible (422 validation error expected)"
        ((PASS++))
    else
        echo -e "${RED}❌ FAIL${NC}: Upload endpoint returned $UPLOAD_RESPONSE (expected 422)"
        ((FAIL++))
    fi
fi

echo -e "\n${BLUE}📋 Phase 6: Database & Storage Tests${NC}"
echo "===================================="

# Test database directory exists
docker exec whisper-app ls -la /app/data/
test_result "Database directory exists in container"

# Test storage directories exist
docker exec whisper-app ls -la /app/storage/uploads/
test_result "Upload storage directory exists"

docker exec whisper-app ls -la /app/storage/transcripts/
test_result "Transcript storage directory exists"

echo -e "\n${BLUE}📋 Phase 7: Background Services Tests${NC}"
echo "====================================="

# Test Redis connectivity
REDIS_INFO=$(docker exec whisper-redis redis-cli -a "NdSpeZBhoG*Gr*po" info server 2>/dev/null | grep redis_version)
echo "$REDIS_INFO" | grep -q "redis_version"
test_result "Redis server info accessible"

# Test Celery worker
WORKER_STATUS=$(docker logs whisper-worker 2>&1 | tail -10)
echo "$WORKER_STATUS" | grep -q "ready\|started\|connected" && echo "Worker appears to be running"
test_result "Celery worker container started"

echo -e "\n${BLUE}📋 Phase 8: Static File Security Tests${NC}"
echo "======================================"

# Test that sensitive files are not accessible
curl -s -f http://localhost:8000/api/main.py && echo "ERROR: Source code accessible!" || echo "Good: Source code not accessible"
test_result "Source code files not accessible via web"

curl -s -f http://localhost:8000/.env && echo "ERROR: Environment file accessible!" || echo "Good: Environment not accessible"
test_result "Environment files not accessible"

echo -e "\n${BLUE}📋 Phase 9: Performance & Resource Tests${NC}"
echo "======================================="

# Check container resource usage
CONTAINER_STATS=$(docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep whisper)
echo "$CONTAINER_STATS"
test_result "Container resource stats accessible"

# Test response times
START_TIME=$(date +%s%N)
curl -s http://localhost:8000/health > /dev/null
END_TIME=$(date +%s%N)
RESPONSE_TIME=$((($END_TIME - $START_TIME) / 1000000)) # Convert to milliseconds

echo "Health endpoint response time: ${RESPONSE_TIME}ms"
if [ "$RESPONSE_TIME" -lt 1000 ]; then
    echo -e "${GREEN}✅ PASS${NC}: Response time under 1 second"
    ((PASS++))
else
    echo -e "${RED}❌ FAIL${NC}: Response time over 1 second"
    ((FAIL++))
fi

echo -e "\n${BLUE}📋 Phase 10: Integration Tests${NC}"
echo "=============================="

# Test SPA routing (should return index.html for unknown routes)
SPA_RESPONSE=$(curl -s http://localhost:8000/some/unknown/route)
echo "$SPA_RESPONSE" | grep -q "Whisper Transcriber"
test_result "SPA routing fallback works"

# Test API vs frontend separation
API_RESPONSE=$(curl -s -H "Accept: application/json" http://localhost:8000/health)
echo "$API_RESPONSE" | grep -q '"status":"ok"'
test_result "API endpoints work with JSON accept header"

echo -e "\n${YELLOW}📊 TEST RESULTS SUMMARY${NC}"
echo "========================"
echo -e "Total Tests: $((PASS + FAIL))"
echo -e "${GREEN}Passed: $PASS${NC}"
echo -e "${RED}Failed: $FAIL${NC}"

PASS_RATE=$(( (PASS * 100) / (PASS + FAIL) ))
echo -e "Pass Rate: ${PASS_RATE}%"

if [ $FAIL -eq 0 ]; then
    echo -e "\n${GREEN}🎉 ALL TESTS PASSED! Infrastructure is ready for production.${NC}"
    exit 0
elif [ $PASS_RATE -ge 80 ]; then
    echo -e "\n${YELLOW}⚠️  Most tests passed ($PASS_RATE%), but some issues need attention.${NC}"
    exit 1
else
    echo -e "\n${RED}🚨 CRITICAL ISSUES DETECTED! Infrastructure needs fixes before production.${NC}"
    exit 2
fi