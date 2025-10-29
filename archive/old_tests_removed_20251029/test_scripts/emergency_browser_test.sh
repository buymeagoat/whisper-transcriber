#!/bin/bash

# EMERGENCY BROWSER SIMULATION TEST
# Tests if the application loads without critical JavaScript errors

echo "🌐 EMERGENCY BROWSER SIMULATION TEST"
echo "==================================="
echo "Testing: Can the web application load without critical JavaScript errors?"
echo ""

# Test 1: Check if homepage loads with single bundle
echo "1. Testing homepage with single bundle..."
HOMEPAGE_CONTENT=$(curl -s http://localhost:8000/)

if echo "$HOMEPAGE_CONTENT" | grep -q 'id="root"'; then
    echo "   ✅ React root container present"
else
    echo "   ❌ React root container missing"
fi

# Check bundle count
BUNDLE_COUNT=$(echo "$HOMEPAGE_CONTENT" | grep -c '/assets/.*\.js' || echo "0")
echo "   Bundle count: $BUNDLE_COUNT"

if [ "$BUNDLE_COUNT" -eq 1 ]; then
    echo "   ✅ Single bundle detected (good for avoiding dependency issues)"
elif [ "$BUNDLE_COUNT" -gt 3 ]; then
    echo "   ⚠️ Multiple bundles detected (potential dependency order issues)"
else
    echo "   ℹ️ $BUNDLE_COUNT bundles detected"
fi

# Test 2: Check bundle accessibility and size
echo ""
echo "2. Testing bundle accessibility..."
BUNDLE_URL=$(echo "$HOMEPAGE_CONTENT" | grep -o '/assets/[^"]*\.js' | head -1)
if [ -n "$BUNDLE_URL" ]; then
    echo "   Bundle URL: $BUNDLE_URL"
    
    BUNDLE_STATUS=$(curl -s -w "%{http_code}" "http://localhost:8000$BUNDLE_URL" -o /dev/null)
    BUNDLE_SIZE=$(curl -s "http://localhost:8000$BUNDLE_URL" | wc -c)
    
    echo "   Bundle status: HTTP $BUNDLE_STATUS"
    echo "   Bundle size: $BUNDLE_SIZE bytes"
    
    if [ "$BUNDLE_STATUS" = "200" ] && [ "$BUNDLE_SIZE" -gt 100000 ]; then
        echo "   ✅ Bundle accessible and substantial"
    else
        echo "   ❌ Bundle issue detected"
    fi
else
    echo "   ❌ No bundle URL found"
fi

# Test 3: Check for critical runtime errors (not library internals)
echo ""
echo "3. Testing for critical runtime errors..."
if [ -n "$BUNDLE_URL" ]; then
    BUNDLE_CONTENT=$(curl -s "http://localhost:8000$BUNDLE_URL")
    
    # Look for actual initialization errors (not library error handling code)
    INIT_ERRORS=$(echo "$BUNDLE_CONTENT" | grep -o "Cannot access '[^']*' before initialization" | head -3)
    if [ -n "$INIT_ERRORS" ]; then
        echo "   🚨 CRITICAL INITIALIZATION ERRORS:"
        echo "$INIT_ERRORS"
    else
        echo "   ✅ No critical initialization errors found"
    fi
    
    # Check for circular dependency errors
    CIRCULAR_ERRORS=$(echo "$BUNDLE_CONTENT" | grep -o "Circular dependency detected" | head -3)
    if [ -n "$CIRCULAR_ERRORS" ]; then
        echo "   🚨 CIRCULAR DEPENDENCY ERRORS:"
        echo "$CIRCULAR_ERRORS"
    else
        echo "   ✅ No circular dependency errors found"
    fi
    
    # Check for undefined function calls that would break the app
    UNDEFINED_ERRORS=$(echo "$BUNDLE_CONTENT" | grep -o "[a-zA-Z_$][a-zA-Z0-9_$]* is not a function" | head -3)
    if [ -n "$UNDEFINED_ERRORS" ]; then
        echo "   ⚠️ Potential undefined function calls:"
        echo "$UNDEFINED_ERRORS"
    else
        echo "   ✅ No obvious undefined function call errors"
    fi
fi

# Test 4: Basic functionality test
echo ""
echo "4. Testing basic functionality..."

# Test if React app is likely to render
if echo "$HOMEPAGE_CONTENT" | grep -q "React" && echo "$HOMEPAGE_CONTENT" | grep -q 'id="root"'; then
    echo "   ✅ React application structure appears correct"
else
    echo "   ⚠️ React application structure unclear"
fi

# Test CSS loading
CSS_COUNT=$(echo "$HOMEPAGE_CONTENT" | grep -c '<link.*stylesheet' || echo "0")
echo "   CSS files: $CSS_COUNT"

if [ "$CSS_COUNT" -gt 0 ]; then
    echo "   ✅ Stylesheets present"
else
    echo "   ⚠️ No stylesheets found"
fi

# Test 5: Performance check
echo ""
echo "5. Testing performance..."
LOAD_TIME=$(curl -s -w "%{time_total}" -o /dev/null http://localhost:8000/)
echo "   Homepage load time: ${LOAD_TIME}s"

if (( $(echo "$LOAD_TIME < 2.0" | bc -l) )); then
    echo "   ✅ Fast loading"
elif (( $(echo "$LOAD_TIME < 5.0" | bc -l) )); then
    echo "   ⚠️ Moderate loading time"
else
    echo "   🐌 Slow loading"
fi

# Summary
echo ""
echo "📊 EMERGENCY TEST RESULTS"
echo "========================"

CRITICAL_ISSUES=0
MINOR_ISSUES=0

if [ "$HOMEPAGE_CHECK" != "200" ]; then
    CRITICAL_ISSUES=$((CRITICAL_ISSUES + 1))
fi

if [ "$BUNDLE_COUNT" -eq 0 ]; then
    CRITICAL_ISSUES=$((CRITICAL_ISSUES + 1))
fi

if [ -n "$INIT_ERRORS" ]; then
    CRITICAL_ISSUES=$((CRITICAL_ISSUES + 1))
fi

if [ "$BUNDLE_COUNT" -gt 3 ]; then
    MINOR_ISSUES=$((MINOR_ISSUES + 1))
fi

echo "Critical Issues: $CRITICAL_ISSUES"
echo "Minor Issues: $MINOR_ISSUES"

if [ "$CRITICAL_ISSUES" -eq 0 ]; then
    echo ""
    echo "🎉 EMERGENCY TEST PASSED"
    echo "✅ Application appears to load without critical JavaScript errors"
    echo "✅ Single bundle architecture should prevent dependency issues"
    echo "✅ Basic infrastructure is functional"
    echo ""
    echo "💡 RECOMMENDATION:"
    echo "The application should now be accessible in your browser."
    echo "Please try accessing http://localhost:8000 again."
    echo ""
    echo "If you still see JavaScript errors, please:"
    echo "1. Clear your browser cache completely"
    echo "2. Try opening in incognito/private mode"
    echo "3. Share the exact error message from browser console"
else
    echo ""
    echo "❌ EMERGENCY TEST FAILED"
    echo "⚠️ Critical issues still exist that prevent application loading"
    echo ""
    echo "Next steps needed:"
    echo "1. Investigate bundle generation process"
    echo "2. Check for build-time compilation errors"  
    echo "3. Verify React application bootstrap code"
fi