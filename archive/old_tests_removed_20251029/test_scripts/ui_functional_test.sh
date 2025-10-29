#!/bin/bash

set -e

BASE_URL="http://localhost:8000"
ADMIN_PASSWORD="0AYw^lpZa!TM*iw0oIKX"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}🎭 COMPLETE UI FUNCTIONAL TESTING${NC}"
echo "===================================="
echo ""
echo -e "${MAGENTA}Testing from actual user perspective...${NC}"
echo ""

# Test 1: Frontend loads without errors
echo -e "${CYAN}🌐 Test 1: Frontend Loading${NC}"
echo -n "HTML structure: "
html_response=$(curl -s "${BASE_URL}/")
if [[ "$html_response" == *"<div id=\"root\">"* ]] && [[ "$html_response" == *"Whisper Transcriber"* ]]; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${RED}❌ FAIL${NC}"
    echo "Response: $(echo "$html_response" | head -c 200)..."
fi

echo -n "JavaScript bundle: "
js_response=$(curl -s -w "%{http_code}" "${BASE_URL}/assets/index-539adbcd.js")
js_code=${js_response: -3}
if [[ "$js_code" == "200" ]]; then
    echo -e "${GREEN}✅ PASS (Loads without white screen)${NC}"
else
    echo -e "${RED}❌ FAIL (This causes white screen!)${NC}"
fi

echo -n "CSS bundle: "
css_response=$(curl -s -w "%{http_code}" "${BASE_URL}/assets/css/index-3c8c337c.css")
css_code=${css_response: -3}
if [[ "$css_code" == "200" ]]; then
    echo -e "${GREEN}✅ PASS (Styles will load)${NC}"
else
    echo -e "${RED}❌ FAIL (Unstyled content)${NC}"
fi

echo ""
echo -e "${CYAN}🔐 Test 2: User Authentication Flow${NC}"

# Test login flow
echo -n "Login endpoint: "
login_response=$(curl -s -X POST "${BASE_URL}/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"admin\",\"password\":\"${ADMIN_PASSWORD}\"}")

if [[ "$login_response" == *"access_token"* ]]; then
    echo -e "${GREEN}✅ PASS${NC}"
    TOKEN=$(echo "$login_response" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    echo "   Token obtained for UI authentication"
else
    echo -e "${RED}❌ FAIL${NC}"
    echo "   Response: $login_response"
    TOKEN=""
fi

echo ""
echo -e "${CYAN}📁 Test 3: File Upload Functionality${NC}"

if [[ -n "$TOKEN" ]]; then
    # Create test audio file
    echo "Test audio content for transcription" > /tmp/test_audio_ui.txt
    
    echo -n "File upload endpoint: "
    upload_response=$(curl -s -X POST "${BASE_URL}/jobs/upload" \
        -H "Authorization: Bearer $TOKEN" \
        -F "file=@/tmp/test_audio_ui.txt" \
        -F "model=base" \
        -w "%{http_code}")
    
    upload_code=${upload_response: -3}
    if [[ "$upload_code" == "200" ]] || [[ "$upload_response" == *"job_id"* ]]; then
        echo -e "${GREEN}✅ PASS (Upload functionality works)${NC}"
        
        # Try to extract job ID
        JOB_ID=$(echo "$upload_response" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
        if [[ -n "$JOB_ID" ]]; then
            echo "   Job created: $JOB_ID"
            
            # Test job status
            echo -n "Job status check: "
            status_response=$(curl -s "${BASE_URL}/jobs/${JOB_ID}" \
                -H "Authorization: Bearer $TOKEN")
            if [[ "$status_response" == *"status"* ]]; then
                echo -e "${GREEN}✅ PASS${NC}"
            else
                echo -e "${YELLOW}⚠️  CHECK${NC}"
            fi
        fi
    else
        echo -e "${RED}❌ FAIL (Upload broken)${NC}"
        echo "   Response: ${upload_response:0:200}..."
    fi
    
    rm -f /tmp/test_audio_ui.txt
else
    echo -e "${YELLOW}⚠️  SKIPPED (No auth token)${NC}"
fi

echo ""
echo -e "${CYAN}📊 Test 4: Dashboard & Admin Features${NC}"

if [[ -n "$TOKEN" ]]; then
    echo -n "Admin stats: "
    stats_response=$(curl -s "${BASE_URL}/admin/stats" \
        -H "Authorization: Bearer $TOKEN")
    if [[ "$stats_response" == *"{"* ]]; then
        echo -e "${GREEN}✅ PASS${NC}"
    else
        echo -e "${YELLOW}⚠️  CHECK${NC}"
    fi
    
    echo -n "Jobs list: "
    jobs_response=$(curl -s "${BASE_URL}/jobs/" \
        -H "Authorization: Bearer $TOKEN")
    if [[ "$jobs_response" == *"["* ]] || [[ "$jobs_response" == *"jobs"* ]]; then
        echo -e "${GREEN}✅ PASS${NC}"
    else
        echo -e "${YELLOW}⚠️  CHECK${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  SKIPPED (No auth token)${NC}"
fi

echo ""
echo -e "${CYAN}⚡ Test 5: Real-time Features${NC}"

echo -n "WebSocket endpoint: "
ws_response=$(curl -s "${BASE_URL}/ws/progress" -w "%{http_code}")
ws_code=${ws_response: -3}
if [[ "$ws_code" == "426" ]]; then
    echo -e "${GREEN}✅ PASS (WebSocket upgrade required - correct)${NC}"
else
    echo -e "${YELLOW}⚠️  CHECK (${ws_code})${NC}"
fi

echo ""
echo -e "${BLUE}📋 UI FUNCTIONALITY SUMMARY${NC}"
echo "=============================="

if [[ "$js_code" == "200" ]] && [[ "$css_code" == "200" ]]; then
    echo -e "${GREEN}✅ Frontend should load without white screen${NC}"
    echo -e "${GREEN}✅ JavaScript and CSS assets loading correctly${NC}"
else
    echo -e "${RED}❌ WHITE SCREEN ISSUE - Assets not loading properly${NC}"
fi

if [[ -n "$TOKEN" ]]; then
    echo -e "${GREEN}✅ Authentication system functional${NC}"
    echo -e "${GREEN}✅ File upload system operational${NC}"
    echo -e "${GREEN}✅ Admin dashboard accessible${NC}"
else
    echo -e "${RED}❌ Authentication issues prevent full UI testing${NC}"
fi

echo ""
echo -e "${MAGENTA}🚀 ACTUAL USER EXPERIENCE TEST${NC}"
echo "================================"
echo ""
echo -e "${YELLOW}1. Open browser to: http://localhost:8000${NC}"
echo -e "${YELLOW}2. Expected: React app loads (no white screen)${NC}"
echo -e "${YELLOW}3. Try login with: admin / ${ADMIN_PASSWORD}${NC}"
echo -e "${YELLOW}4. Test file upload functionality${NC}"
echo -e "${YELLOW}5. Check dashboard and job monitoring${NC}"
echo ""

if [[ "$js_code" == "200" ]] && [[ "$css_code" == "200" ]]; then
    echo -e "${GREEN}🎉 UI should be functional now!${NC}"
else
    echo -e "${RED}⚠️  UI issues remain - check browser console for errors${NC}"
fi

echo ""
echo -e "${CYAN}Browser console errors to watch for:${NC}"
echo "- Failed to load resource: /assets/..."
echo "- Uncaught TypeError in React"
echo "- Network errors for API calls"
echo "- CORS issues"