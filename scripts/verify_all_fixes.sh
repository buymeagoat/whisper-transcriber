#!/bin/bash

# Comprehensive Fix Verification Script
# Tests all implemented fixes after container rebuild

BASE_URL="http://localhost:8000"
PASSED=0
FAILED=0
TOTAL=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔍 Comprehensive Fix Verification${NC}"
echo "================================="

test_fix() {
    local name="$1"
    local test_command="$2"
    local expected_result="$3"
    
    ((TOTAL++))
    echo -e "${YELLOW}Testing: $name${NC}"
    
    result=$(eval "$test_command" 2>/dev/null)
    
    if [[ "$result" == *"$expected_result"* ]]; then
        echo -e "${GREEN}✅ PASS: $name${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL: $name${NC}"
        echo -e "${RED}   Expected: $expected_result${NC}"
        echo -e "${RED}   Got: $result${NC}"
        ((FAILED++))
    fi
    echo ""
}

echo -e "${BLUE}Fix 1: Database Performance Monitoring Threshold${NC}"
test_fix "Database threshold is 1.0 QPS" \
    "grep 'low_throughput_ops_per_sec: float = 1.0' /home/buymeagoat/dev/whisper-transcriber/api/database_performance_monitor.py" \
    "low_throughput_ops_per_sec: float = 1.0"

echo -e "${BLUE}Fix 2: Redis Environment Variables${NC}"
test_fix "Redis rate limiter uses env vars" \
    "grep 'field(default_factory=lambda: os.getenv(\"REDIS_URL\"' /home/buymeagoat/dev/whisper-transcriber/api/middlewares/enhanced_rate_limiter.py" \
    "field(default_factory=lambda: os.getenv(\"REDIS_URL\""

test_fix "Redis cache service uses env vars" \
    "grep 'field(default_factory=lambda: os.getenv(\"REDIS_URL\"' /home/buymeagoat/dev/whisper-transcriber/api/services/redis_cache.py" \
    "field(default_factory=lambda: os.getenv(\"REDIS_URL\""

echo -e "${BLUE}Fix 3: Authentication Endpoints${NC}"
test_fix "API router login endpoint exists" \
    "grep '@api_router.post(\"/login\"' /home/buymeagoat/dev/whisper-transcriber/api/routes/auth.py" \
    "@api_router.post(\"/login\""

test_fix "API router register endpoint exists" \
    "grep '@api_router.post(\"/register\"' /home/buymeagoat/dev/whisper-transcriber/api/routes/auth.py" \
    "@api_router.post(\"/register\""

test_fix "API router is registered" \
    "grep 'auth.api_router' /home/buymeagoat/dev/whisper-transcriber/api/router_setup.py" \
    "auth.api_router"

echo -e "${BLUE}Fix 4: FFmpeg Dependency${NC}"
test_fix "FFmpeg in Dockerfile" \
    "grep 'ffmpeg' /home/buymeagoat/dev/whisper-transcriber/Dockerfile" \
    "ffmpeg"

echo -e "${BLUE}Container Health Check${NC}"
if docker ps | grep -q whisper-app; then
    echo -e "${GREEN}✅ Container is running${NC}"
    ((TOTAL++))
    ((PASSED++))
else
    echo -e "${RED}❌ Container is not running${NC}"
    ((TOTAL++))
    ((FAILED++))
fi
echo ""

echo -e "${BLUE}API Endpoint Tests (if container is running)${NC}"
if docker ps | grep -q whisper-app; then
    # Wait a moment for container to be ready
    sleep 2
    
    # Test health endpoint
    ((TOTAL++))
    health_status=$(curl -s -w "%{http_code}" -o /dev/null "$BASE_URL/health")
    if [ "$health_status" = "200" ]; then
        echo -e "${GREEN}✅ Health endpoint working${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ Health endpoint failed (status: $health_status)${NC}"
        ((FAILED++))
    fi
    
    # Test login endpoint
    ((TOTAL++))
    login_status=$(curl -s -w "%{http_code}" -o /dev/null -X POST -H "Content-Type: application/json" -d '{"username":"test","password":"test"}' "$BASE_URL/api/auth/login")
    if [ "$login_status" = "401" ] || [ "$login_status" = "422" ]; then
        echo -e "${GREEN}✅ Login endpoint accessible (status: $login_status)${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ Login endpoint issue (status: $login_status)${NC}"
        ((FAILED++))
    fi
    
    # Test register endpoint
    ((TOTAL++))
    register_status=$(curl -s -w "%{http_code}" -o /dev/null -X POST -H "Content-Type: application/json" -d '{"username":"test","password":"test"}' "$BASE_URL/api/register")
    if [ "$register_status" = "409" ] || [ "$register_status" = "422" ] || [ "$register_status" = "201" ]; then
        echo -e "${GREEN}✅ Register endpoint accessible (status: $register_status)${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ Register endpoint issue (status: $register_status)${NC}"
        ((FAILED++))
    fi
    
    echo ""
else
    echo -e "${YELLOW}⚠️  Skipping API tests - container not running${NC}"
    echo ""
fi

# Summary
echo -e "${BLUE}📊 Verification Summary${NC}"
echo "======================"
echo "Total Tests: $TOTAL"
echo "Passed: $PASSED"
echo "Failed: $FAILED"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL FIXES VERIFIED SUCCESSFULLY!${NC}"
    exit 0
else
    echo -e "${RED}⚠️  $FAILED ISSUES FOUND - NEED ATTENTION${NC}"
    exit 1
fi