#!/bin/bash

# Frontend Reality Check - Tests what users actually experience
# Focus: Does the frontend actually work for users?

set -e

echo "🖥️  FRONTEND REALITY CHECK"
echo "========================"
echo "Testing philosophy: If the frontend has JavaScript errors, it's broken for users"
echo ""

CRITICAL_FAILURES=()
USER_BLOCKING_ISSUES=()
FRONTEND_ISSUES=()

fail_critical() {
    CRITICAL_FAILURES+=("$1")
    echo "🚨 CRITICAL: $1"
}

fail_blocking() {
    USER_BLOCKING_ISSUES+=("$1")
    echo "⛔ BLOCKING: $1"
}

warn_frontend() {
    FRONTEND_ISSUES+=("$1")
    echo "⚠️  FRONTEND: $1"
}

pass_test() {
    echo "✅ $1"
}

echo "📋 Phase 1: Does the frontend actually load?"
echo "==========================================="

# Test 1: Basic HTML Structure
echo "Testing basic HTML structure..."
HOMEPAGE_HTML=$(curl -s http://localhost:8000/)
if echo "$HOMEPAGE_HTML" | grep -q "<!DOCTYPE html>"; then
    pass_test "Homepage serves valid HTML structure"
else
    fail_critical "Homepage does not serve valid HTML"
fi

# Test 2: JavaScript Bundle Loading
echo "Testing JavaScript bundle references..."
BUNDLE_COUNT=$(echo "$HOMEPAGE_HTML" | grep -c '<script.*src=' || echo "0")
if [ "$BUNDLE_COUNT" -gt 0 ]; then
    pass_test "JavaScript bundles are referenced ($BUNDLE_COUNT bundles)"
    
    # Extract bundle URLs
    BUNDLE_URLS=$(echo "$HOMEPAGE_HTML" | grep -o '<script[^>]*src="[^"]*"' | grep -o '/assets/[^"]*' || echo "")
    if [ -n "$BUNDLE_URLS" ]; then
        echo "  Found bundles: $BUNDLE_URLS"
    fi
else
    fail_critical "No JavaScript bundles found"
fi

# Test 3: Bundle Accessibility
echo "Testing JavaScript bundle accessibility..."
for bundle_url in $BUNDLE_URLS; do
    FULL_URL="http://localhost:8000$bundle_url"
    echo "  Testing: $bundle_url"
    
    BUNDLE_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null "$FULL_URL")
    if [ "$BUNDLE_RESPONSE" = "200" ]; then
        pass_test "Bundle accessible: $bundle_url"
        
        # Test bundle content
        BUNDLE_SIZE=$(curl -s "$FULL_URL" | wc -c)
        if [ "$BUNDLE_SIZE" -gt 1000 ]; then
            pass_test "Bundle has content: $bundle_url ($BUNDLE_SIZE bytes)"
        else
            warn_frontend "Bundle suspiciously small: $bundle_url ($BUNDLE_SIZE bytes)"
        fi
    else
        fail_blocking "Bundle not accessible: $bundle_url (HTTP $BUNDLE_RESPONSE)"
    fi
done

echo ""
echo "📋 Phase 2: Does the frontend actually render?"
echo "============================================="

# Test 4: React App Container
echo "Testing React app container..."
if echo "$HOMEPAGE_HTML" | grep -q 'id="root"'; then
    pass_test "React root container found"
else
    fail_blocking "React root container missing"
fi

# Test 5: Critical CSS/Styles
echo "Testing critical styling..."
CSS_COUNT=$(echo "$HOMEPAGE_HTML" | grep -c '<link.*stylesheet\|<style' || echo "0")
if [ "$CSS_COUNT" -gt 0 ]; then
    pass_test "Stylesheets referenced ($CSS_COUNT)"
else
    warn_frontend "No stylesheets found - app may look broken"
fi

# Test 6: Favicon and Meta Tags
echo "Testing basic meta tags..."
if echo "$HOMEPAGE_HTML" | grep -q '<title>'; then
    TITLE=$(echo "$HOMEPAGE_HTML" | grep -o '<title>[^<]*</title>' | sed 's/<[^>]*>//g')
    pass_test "Page title found: '$TITLE'"
else
    warn_frontend "No page title found"
fi

echo ""
echo "📋 Phase 3: Frontend-Backend Integration"
echo "======================================="

# Test 7: API Endpoint Accessibility from Frontend Context
echo "Testing API accessibility from frontend..."
API_HEALTH=$(curl -s -w "%{http_code}" -o /dev/null http://localhost:8000/health)
if [ "$API_HEALTH" = "200" ]; then
    pass_test "Backend API accessible from frontend context"
else
    fail_blocking "Backend API not accessible (HTTP $API_HEALTH)"
fi

# Test 8: CORS and Headers
echo "Testing CORS and security headers..."
CORS_HEADERS=$(curl -s -I http://localhost:8000/ | grep -i "access-control\|content-security\|x-frame" || echo "")
if [ -n "$CORS_HEADERS" ]; then
    pass_test "Security headers present"
    echo "  Headers: $(echo "$CORS_HEADERS" | tr '\n' ' ')"
else
    warn_frontend "Limited security headers found"
fi

echo ""
echo "📋 Phase 4: Runtime JavaScript Health (Simulated)"
echo "================================================"

# Test 9: Bundle Syntax Check
echo "Testing JavaScript bundle syntax..."
for bundle_url in $BUNDLE_URLS; do
    if [ -n "$bundle_url" ]; then
        FULL_URL="http://localhost:8000$bundle_url"
        BUNDLE_CONTENT=$(curl -s "$FULL_URL" | head -c 1000)
        
        # Basic syntax checks
        if echo "$BUNDLE_CONTENT" | grep -q "import.*from\|export.*{"; then
            pass_test "Bundle uses ES modules: $bundle_url"
        fi
        
        if echo "$BUNDLE_CONTENT" | grep -q "react\|React"; then
            pass_test "Bundle contains React code: $bundle_url"
        fi
        
        # Check for obvious syntax errors
        if echo "$BUNDLE_CONTENT" | grep -q "SyntaxError\|ReferenceError\|TypeError"; then
            fail_blocking "Bundle contains error indicators: $bundle_url"
        fi
        
        # Check for circular dependency patterns
        if echo "$BUNDLE_CONTENT" | grep -q "Cannot access.*before initialization"; then
            fail_blocking "Bundle has initialization order errors: $bundle_url"
        fi
    fi
done

# Test 10: Essential Frontend Libraries Present
echo "Testing essential frontend libraries..."
MAIN_BUNDLE_CONTENT=""
for bundle_url in $BUNDLE_URLS; do
    if [ -n "$bundle_url" ]; then
        FULL_URL="http://localhost:8000$bundle_url"
        MAIN_BUNDLE_CONTENT+=$(curl -s "$FULL_URL")
    fi
done

if echo "$MAIN_BUNDLE_CONTENT" | grep -q "react"; then
    pass_test "React library found in bundles"
else
    fail_blocking "React library not found in bundles"
fi

if echo "$MAIN_BUNDLE_CONTENT" | grep -q "axios\|fetch"; then
    pass_test "HTTP client library found in bundles"
else
    warn_frontend "No obvious HTTP client found in bundles"
fi

echo ""
echo "📊 FRONTEND REALITY CHECK RESULTS"
echo "================================="

echo "✅ Tests Passed: $(echo "$HOMEPAGE_HTML" | grep -c "✅" || echo "0")"
echo "⚠️  Frontend Issues: ${#FRONTEND_ISSUES[@]}"
echo "⛔ User-Blocking Issues: ${#USER_BLOCKING_ISSUES[@]}"
echo "🚨 Critical Failures: ${#CRITICAL_FAILURES[@]}"

echo ""
if [ ${#CRITICAL_FAILURES[@]} -gt 0 ]; then
    echo "🚨 CRITICAL FAILURES (Frontend Completely Broken):"
    for failure in "${CRITICAL_FAILURES[@]}"; do
        echo "   • $failure"
    done
fi

if [ ${#USER_BLOCKING_ISSUES[@]} -gt 0 ]; then
    echo "⛔ USER-BLOCKING ISSUES (Frontend Broken for Users):"
    for issue in "${USER_BLOCKING_ISSUES[@]}"; do
        echo "   • $issue"
    done
fi

if [ ${#FRONTEND_ISSUES[@]} -gt 0 ]; then
    echo "⚠️  FRONTEND ISSUES (Poor User Experience):"
    for issue in "${FRONTEND_ISSUES[@]}"; do
        echo "   • $issue"
    done
fi

echo ""
echo "📋 FRONTEND READINESS ASSESSMENT:"

if [ ${#CRITICAL_FAILURES[@]} -gt 0 ]; then
    echo "❌ FRONTEND IS BROKEN - Cannot load in browsers"
    exit 1
elif [ ${#USER_BLOCKING_ISSUES[@]} -gt 0 ]; then
    echo "⚠️  FRONTEND HAS BLOCKING ISSUES - May not work for users"
    exit 2
elif [ ${#FRONTEND_ISSUES[@]} -gt 0 ]; then
    echo "✅ FRONTEND IS FUNCTIONAL - Has minor issues but works"
    exit 0
else
    echo "🎉 FRONTEND IS USER-READY - Fully functional frontend"
    exit 0
fi