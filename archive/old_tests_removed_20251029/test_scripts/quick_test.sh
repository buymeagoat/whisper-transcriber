#!/bin/bash

set -e

BASE_URL="http://localhost:8000"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🧪 Quick Application Test${NC}"
echo "=================================="

# Test 1: Health Check
echo -n "1. Health Check: "
response=$(curl -s "${BASE_URL}/health")
if [[ "$response" == *"ok"* ]]; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${RED}❌ FAIL${NC}"
fi

# Test 2: OpenAPI Documentation
echo -n "2. API Documentation: "
if curl -s "${BASE_URL}/docs" | grep -q "OpenAPI"; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${RED}❌ FAIL${NC}"
fi

# Test 3: Frontend Availability
echo -n "3. Frontend Access: "
if curl -s "${BASE_URL}/" | grep -q -i "html\|doctype"; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${RED}❌ FAIL${NC}"
fi

# Test 4: Authentication Endpoint
echo -n "4. Auth Endpoint: "
auth_response=$(curl -s -X POST "${BASE_URL}/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin123"}' \
    -w "%{http_code}")

if [[ "$auth_response" == *"200" ]] || [[ "$auth_response" == *"token"* ]]; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${YELLOW}⚠️  PARTIAL (${auth_response})${NC}"
fi

# Test 5: File Upload Endpoint (without auth)
echo -n "5. Upload Endpoint Structure: "
upload_response=$(curl -s "${BASE_URL}/transcribe/upload" -w "%{http_code}")
if [[ "$upload_response" == *"401"* ]] || [[ "$upload_response" == *"405"* ]]; then
    echo -e "${GREEN}✅ PASS (Protected)${NC}"
else
    echo -e "${YELLOW}⚠️  UNEXPECTED (${upload_response})${NC}"
fi

# Test 6: WebSocket endpoint existence
echo -n "6. WebSocket Endpoint: "
ws_response=$(curl -s "${BASE_URL}/ws/progress" -w "%{http_code}")
if [[ "$ws_response" == *"426"* ]] || [[ "$ws_response" == *"400"* ]]; then
    echo -e "${GREEN}✅ PASS (WebSocket Available)${NC}"
else
    echo -e "${YELLOW}⚠️  CHECK (${ws_response})${NC}"
fi

# Test 7: Container Status
echo -n "7. Docker Containers: "
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${RED}❌ FAIL${NC}"
fi

# Test 8: Redis Connection
echo -n "8. Redis Service: "
if docker-compose exec -T redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${RED}❌ FAIL${NC}"
fi

echo ""
echo -e "${BLUE}🎯 Quick Test Complete!${NC}"
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. Visit http://localhost:8000 to test the web interface"
echo "2. Visit http://localhost:8000/docs for API documentation" 
echo "3. Use credentials: admin / admin123 to login"
echo "4. Try uploading an audio file for transcription"
echo ""
echo -e "${BLUE}🌐 Network Access:${NC}"
echo "Application is available at: http://192.168.235.47:8000"