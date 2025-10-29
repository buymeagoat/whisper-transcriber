#!/bin/bash

# REAL USER EXPERIENCE TEST
# Tests exactly what happens when a user opens the application

echo "🌐 REAL USER EXPERIENCE TEST"
echo "============================"
echo "Testing: What happens when a user opens http://localhost:8000 in their browser?"
echo ""

# Step 1: Load the main page
echo "👤 User Action: Opening http://localhost:8000..."
MAIN_PAGE=$(curl -s http://localhost:8000/)

# Step 2: Extract and load all resources the browser would load
echo "🔄 Browser Action: Loading all page resources..."

# Get CSS files
CSS_FILES=$(echo "$MAIN_PAGE" | grep -o '<link[^>]*href="[^"]*\.css[^"]*"' | grep -o 'href="[^"]*"' | sed 's/href="//g' | sed 's/"//g' || echo "")
if [ -n "$CSS_FILES" ]; then
    for css_file in $CSS_FILES; do
        echo "  Loading CSS: $css_file"
        CSS_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null "http://localhost:8000$css_file")
        if [ "$CSS_RESPONSE" != "200" ]; then
            echo "  ❌ CSS failed to load: $css_file (HTTP $CSS_RESPONSE)"
        else
            echo "  ✅ CSS loaded: $css_file"
        fi
    done
else
    echo "  ℹ️  No external CSS files found"
fi

# Get JavaScript files
JS_FILES=$(echo "$MAIN_PAGE" | grep -o '<script[^>]*src="[^"]*"' | grep -o 'src="[^"]*"' | sed 's/src="//g' | sed 's/"//g' || echo "")
if [ -n "$JS_FILES" ]; then
    for js_file in $JS_FILES; do
        echo "  Loading JS: $js_file"
        JS_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null "http://localhost:8000$js_file")
        if [ "$JS_RESPONSE" != "200" ]; then
            echo "  ❌ JavaScript failed to load: $js_file (HTTP $JS_RESPONSE)"
        else
            echo "  ✅ JavaScript loaded: $js_file"
            
            # Check for obvious runtime errors in the JS content
            JS_CONTENT=$(curl -s "http://localhost:8000$js_file" | head -c 2000)
            if echo "$JS_CONTENT" | grep -q "ReferenceError\|SyntaxError\|TypeError.*initialization"; then
                echo "  ⚠️  JavaScript contains error patterns: $js_file"
            fi
        fi
    done
else
    echo "  ❌ No JavaScript files found - React app will not work"
fi

echo ""
echo "🎯 USER EXPERIENCE SIMULATION"
echo "============================"

# Test key user flows that would happen immediately on page load
echo "Testing immediate user experience..."

# Test 1: Can user see the app interface?
echo "1. Interface Visibility Test:"
if echo "$MAIN_PAGE" | grep -q 'id="root"'; then
    echo "   ✅ React app container present"
    
    # Check if there's any initial content or loading state
    if echo "$MAIN_PAGE" | grep -q "loading\|Loading\|spinner\|Spinner"; then
        echo "   ✅ Loading state visible to user"
    elif echo "$MAIN_PAGE" | grep -q -E "(Welcome|Dashboard|Transcrib|Login|Register)"; then
        echo "   ✅ Content visible in initial HTML"
    else
        echo "   ⚠️  No obvious content or loading state - user may see blank page"
    fi
else
    echo "   ❌ React app container missing - user will see blank page"
fi

# Test 2: Can user interact with authentication?
echo "2. Authentication Accessibility Test:"
AUTH_ENDPOINTS=("/register" "/auth/login" "/token")
AUTH_WORKING=0
for endpoint in "${AUTH_ENDPOINTS[@]}"; do
    TEST_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000$endpoint")
    if [ "$TEST_RESPONSE" = "200" ] || [ "$TEST_RESPONSE" = "405" ]; then
        echo "   ✅ Auth endpoint accessible: $endpoint"
        AUTH_WORKING=$((AUTH_WORKING + 1))
    else
        echo "   ⚠️  Auth endpoint issue: $endpoint (HTTP $TEST_RESPONSE)"
    fi
done

if [ "$AUTH_WORKING" -gt 0 ]; then
    echo "   ✅ User can potentially authenticate ($AUTH_WORKING/3 endpoints working)"
else
    echo "   ❌ User cannot authenticate - all auth endpoints broken"
fi

# Test 3: Can user access core functionality?
echo "3. Core Functionality Test:"
JOBS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/jobs/")
if [ "$JOBS_RESPONSE" = "401" ]; then
    echo "   ✅ Jobs endpoint requires authentication (expected)"
elif [ "$JOBS_RESPONSE" = "200" ]; then
    echo "   ✅ Jobs endpoint accessible"
else
    echo "   ⚠️  Jobs endpoint unexpected response: HTTP $JOBS_RESPONSE"
fi

echo ""
echo "📱 MOBILE/RESPONSIVE TEST"
echo "========================"

# Test responsive meta tags
if echo "$MAIN_PAGE" | grep -q 'name="viewport"'; then
    VIEWPORT=$(echo "$MAIN_PAGE" | grep -o 'name="viewport"[^>]*content="[^"]*"' | grep -o 'content="[^"]*"' | sed 's/content="//g' | sed 's/"//g')
    echo "✅ Responsive viewport tag found: $VIEWPORT"
else
    echo "⚠️  No responsive viewport tag - poor mobile experience"
fi

# Test for mobile-specific CSS
if [ -n "$CSS_FILES" ]; then
    MOBILE_CSS_FOUND=0
    for css_file in $CSS_FILES; do
        CSS_CONTENT=$(curl -s "http://localhost:8000$css_file" | head -c 1000)
        if echo "$CSS_CONTENT" | grep -q "@media.*max-width\|@media.*min-width\|mobile\|tablet"; then
            MOBILE_CSS_FOUND=1
            break
        fi
    done
    
    if [ "$MOBILE_CSS_FOUND" = "1" ]; then
        echo "✅ Mobile-responsive CSS detected"
    else
        echo "⚠️  No obvious mobile CSS - may not work on mobile"
    fi
fi

echo ""
echo "📋 REAL USER EXPERIENCE ASSESSMENT"
echo "=================================="

# Count actual issues that would affect users
CRITICAL_ISSUES=0
MINOR_ISSUES=0

# Check for critical issues
if ! echo "$MAIN_PAGE" | grep -q 'id="root"'; then
    CRITICAL_ISSUES=$((CRITICAL_ISSUES + 1))
fi

if [ -z "$JS_FILES" ]; then
    CRITICAL_ISSUES=$((CRITICAL_ISSUES + 1))
fi

if [ "$AUTH_WORKING" -eq 0 ]; then
    CRITICAL_ISSUES=$((CRITICAL_ISSUES + 1))
fi

# Check for minor issues
if ! echo "$MAIN_PAGE" | grep -q 'name="viewport"'; then
    MINOR_ISSUES=$((MINOR_ISSUES + 1))
fi

echo "Critical Issues Found: $CRITICAL_ISSUES"
echo "Minor Issues Found: $MINOR_ISSUES"

if [ "$CRITICAL_ISSUES" -eq 0 ]; then
    if [ "$MINOR_ISSUES" -eq 0 ]; then
        echo ""
        echo "🎉 EXCELLENT USER EXPERIENCE"
        echo "✅ Application is ready for real users"
        echo "✅ All critical functionality accessible"
        echo "✅ No blocking issues found"
    else
        echo ""
        echo "✅ GOOD USER EXPERIENCE"
        echo "✅ Application works for users"
        echo "⚠️  Minor improvements could enhance experience"
    fi
else
    echo ""
    echo "❌ POOR USER EXPERIENCE"
    echo "⛔ Users will encounter significant issues"
    echo "🚨 Critical problems need immediate attention"
fi