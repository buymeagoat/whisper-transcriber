#!/bin/bash

# Real User Testing Script - Login Flow
# Acting as a user who just discovered this application

set -e

BASE_URL="http://localhost:8000"
ADMIN_PASSWORD="0AYw^lpZa!TM*iw0oIKX"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'

echo -e "${BLUE}👤 ACTING AS REAL USER - LOGIN TESTING${NC}"
echo "========================================"
echo ""
echo -e "${MAGENTA}User Story: I'm a new user trying to use this transcription service${NC}"
echo ""

# Step 1: User opens the website
echo -e "${CYAN}🌐 Step 1: Opening the website...${NC}"
echo "User action: Navigate to ${BASE_URL}"

# Check what the user actually sees
homepage_content=$(curl -s "${BASE_URL}/")

echo -n "✓ Page loads: "
if [[ "$homepage_content" == *"<div id=\"root\">"* ]]; then
    echo -e "${GREEN}SUCCESS${NC}"
    echo "  User sees: Whisper Transcriber page"
else
    echo -e "${RED}FAIL - User sees unexpected content${NC}"
    echo "  Content preview: $(echo "$homepage_content" | head -c 200)..."
fi

# Step 2: User tries to understand what they can do
echo ""
echo -e "${CYAN}🔍 Step 2: User explores the interface...${NC}"
echo "User action: Looking for login, navigation, or main features"

# Check for React app indicators
echo -n "✓ React app loaded: "
if [[ "$homepage_content" == *"assets/index-"* ]]; then
    echo -e "${GREEN}SUCCESS${NC}"
    echo "  User sees: JavaScript app is loading"
else
    echo -e "${RED}FAIL - No React app detected${NC}"
fi

# Test if the UI is actually interactive (check for API endpoints user might discover)
echo -n "✓ Login endpoint exists: "
login_test=$(curl -s -X OPTIONS "${BASE_URL}/auth/login" -w "%{http_code}")
login_code=${login_test: -3}
if [[ "$login_code" == "200" ]] || [[ "$login_code" == "405" ]]; then
    echo -e "${GREEN}SUCCESS${NC}"
    echo "  User discovers: Login functionality is available"
else
    echo -e "${YELLOW}UNKNOWN (${login_code})${NC}"
fi

# Step 3: User attempts to log in (they might try common credentials first)
echo ""
echo -e "${CYAN}🔐 Step 3: User attempts login...${NC}"

# First, try common credentials (what real users do)
echo "User action: Trying common credentials..."
echo -n "✓ Try admin/admin: "
common_login=$(curl -s -X POST "${BASE_URL}/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin"}')

if [[ "$common_login" == *"access_token"* ]]; then
    echo -e "${GREEN}SUCCESS${NC}"
    echo "  Result: User logged in with default credentials"
else
    echo -e "${YELLOW}FAILED - User gets: ${common_login:0:50}...${NC}"
fi

echo -n "✓ Try admin/password: "
common_login2=$(curl -s -X POST "${BASE_URL}/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"password"}')

if [[ "$common_login2" == *"access_token"* ]]; then
    echo -e "${GREEN}SUCCESS${NC}"
    echo "  Result: User logged in with default credentials"
else
    echo -e "${YELLOW}FAILED - User gets: ${common_login2:0:50}...${NC}"
fi

# Now try the actual credentials (assuming user found documentation)
echo -n "✓ Try documented credentials: "
real_login=$(curl -s -X POST "${BASE_URL}/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"admin\",\"password\":\"${ADMIN_PASSWORD}\"}")

if [[ "$real_login" == *"access_token"* ]]; then
    echo -e "${GREEN}SUCCESS${NC}"
    echo "  Result: User successfully logged in!"
    
    # Extract token for further testing
    TOKEN=$(echo "$real_login" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    echo "  Token obtained: ${TOKEN:0:30}..."
    
    # Step 4: User explores what they can do after login
    echo ""
    echo -e "${CYAN}🏠 Step 4: User explores authenticated features...${NC}"
    
    echo -n "✓ Check user profile: "
    profile_response=$(curl -s -H "Authorization: Bearer $TOKEN" "${BASE_URL}/auth/me")
    if [[ "$profile_response" == *"username"* ]]; then
        echo -e "${GREEN}SUCCESS${NC}"
        echo "  User sees their profile info"
    else
        echo -e "${RED}FAIL${NC}"
        echo "  Response: ${profile_response:0:100}..."
    fi
    
    echo -n "✓ Explore job list: "
    jobs_response=$(curl -s -H "Authorization: Bearer $TOKEN" "${BASE_URL}/jobs/")
    if [[ "$jobs_response" == *"["* ]]; then
        echo -e "${GREEN}SUCCESS${NC}"
        echo "  User sees job management interface"
    else
        echo -e "${YELLOW}CHECK - Response: ${jobs_response:0:100}...${NC}"
    fi
    
else
    echo -e "${RED}FAILED${NC}"
    echo "  Response: ${real_login:0:100}..."
    echo "  User cannot log in - major blocker!"
fi

echo ""
echo -e "${BLUE}📋 USER EXPERIENCE SUMMARY${NC}"
echo "============================"

if [[ "$real_login" == *"access_token"* ]]; then
    echo -e "${GREEN}✅ User can successfully log in and access the system${NC}"
    echo -e "${GREEN}✅ Authentication flow works as expected${NC}"
    echo -e "${YELLOW}⚠️  Strong password may confuse users without documentation${NC}"
else
    echo -e "${RED}❌ CRITICAL: User cannot log in - application unusable${NC}"
fi

echo ""
echo -e "${MAGENTA}Next: User will try to upload files and test transcription...${NC}"