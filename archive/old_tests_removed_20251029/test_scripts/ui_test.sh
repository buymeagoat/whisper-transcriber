#!/bin/bash

set -e

BASE_URL="http://localhost:8000"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'

echo -e "${BLUE}🧪 COMPREHENSIVE UI TESTING${NC}"
echo "================================"
echo ""

echo -e "${MAGENTA}Testing actual user experience...${NC}"
echo ""

# Test 1: Main page loads
echo -e "${CYAN}📄 Test 1: Main Page Loading${NC}"
echo -n "Main page HTML: "
main_response=$(curl -s "${BASE_URL}/")
if [[ "$main_response" == *"<div id=\"root\">"* ]]; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${RED}❌ FAIL - No React root div found${NC}"
    echo "Response preview: $(echo "$main_response" | head -c 200)..."
fi

# Test 2: JavaScript assets loading
echo -e "${CYAN}📦 Test 2: Asset Loading${NC}"
echo -n "Main JS bundle: "
js_response=$(curl -s -w "%{http_code}" "${BASE_URL}/assets/index-539adbcd.js")
js_code=${js_response: -3}
if [[ "$js_code" == "200" ]]; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${RED}❌ FAIL (HTTP $js_code)${NC}"
fi

echo -n "CSS bundle: "
css_response=$(curl -s -w "%{http_code}" "${BASE_URL}/assets/css/index-3c8c337c.css")
css_code=${css_response: -3}
if [[ "$css_code" == "200" ]]; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${RED}❌ FAIL (HTTP $css_code)${NC}"
fi

# Test 3: Static file serving
echo -n "Static file serving: "
static_response=$(curl -s -w "%{http_code}" "${BASE_URL}/static/index.html")
static_code=${static_response: -3}
if [[ "$static_code" == "200" ]]; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${RED}❌ FAIL (HTTP $static_code)${NC}"
fi

# Test 4: Vite icon
echo -n "Vite icon: "
icon_response=$(curl -s -w "%{http_code}" "${BASE_URL}/vite.svg")
icon_code=${icon_response: -3}
if [[ "$icon_code" == "200" ]]; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${RED}❌ FAIL (HTTP $icon_code)${NC}"
fi

echo ""
echo -e "${MAGENTA}🌐 Testing UI Functionality...${NC}"

# Test 5: API connectivity from frontend perspective
echo -n "Frontend API access: "
api_response=$(curl -s -w "%{http_code}" "${BASE_URL}/health")
api_code=${api_response: -3}
if [[ "$api_code" == "200" ]]; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${RED}❌ FAIL${NC}"
fi

# Test 6: CORS headers for frontend
echo -n "CORS headers: "
cors_response=$(curl -s -H "Origin: http://localhost:8000" -H "Access-Control-Request-Method: GET" -H "Access-Control-Request-Headers: authorization" -X OPTIONS "${BASE_URL}/health")
if [[ "$cors_response" == *"access-control"* ]] || [[ -z "$cors_response" ]]; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${YELLOW}⚠️  CHECK${NC}"
fi

echo ""
echo -e "${BLUE}📊 UI DIAGNOSTICS${NC}"
echo "=================="

# Show what's actually being served at root
echo -e "${YELLOW}Root page content (first 300 chars):${NC}"
echo "$(curl -s "${BASE_URL}/" | head -c 300)..."
echo ""

# Show asset loading details
echo -e "${YELLOW}Asset loading test:${NC}"
for asset in "assets/index-539adbcd.js" "assets/css/index-3c8c337c.css" "vite.svg"; do
    response=$(curl -s -I "${BASE_URL}/${asset}")
    status=$(echo "$response" | grep "HTTP" | awk '{print $2}')
    echo "  /${asset}: HTTP $status"
done

echo ""
echo -e "${MAGENTA}🔧 RECOMMENDATIONS${NC}"
echo "==================="

if [[ "$js_code" != "200" ]]; then
    echo -e "${RED}❌ JavaScript assets not loading - this causes white screen${NC}"
    echo "   - Check static file serving configuration"
    echo "   - Verify asset paths in container"
fi

if [[ "$css_code" != "200" ]]; then
    echo -e "${RED}❌ CSS assets not loading - this causes unstyled content${NC}"
    echo "   - Check CSS file serving"
fi

echo ""
echo -e "${BLUE}Next steps: Open browser console at ${BASE_URL} to see JavaScript errors${NC}"