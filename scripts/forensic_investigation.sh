#!/bin/bash

# FORENSIC APPLICATION INVESTIGATION
# Deep analysis to find systematic issues preventing basic functionality

set -e

echo "🔍 FORENSIC APPLICATION INVESTIGATION"
echo "====================================="
echo "Objective: Identify fundamental architectural issues preventing basic web app access"
echo ""

# Create forensic report
FORENSIC_REPORT="/tmp/forensic_investigation_$(date +%Y%m%d_%H%M%S).md"
exec 1> >(tee -a "$FORENSIC_REPORT")
exec 2> >(tee -a "$FORENSIC_REPORT" >&2)

echo "# FORENSIC INVESTIGATION REPORT"
echo "## $(date)"
echo ""

echo "## 🚨 INVESTIGATION SCOPE"
echo "- User reports JavaScript errors preventing web app access"
echo "- Previous 'fixes' have not resolved core issues"
echo "- Need systematic analysis of fundamental problems"
echo ""

echo "## 📊 PHASE 1: CURRENT APPLICATION STATE"
echo ""

# Test basic accessibility
echo "### Application Accessibility Test"
HEALTH_CHECK=$(curl -s -w "%{http_code}" http://localhost:8000/health -o /dev/null)
echo "- Health endpoint: HTTP $HEALTH_CHECK"

HOMEPAGE_CHECK=$(curl -s -w "%{http_code}" http://localhost:8000/ -o /dev/null)  
echo "- Homepage endpoint: HTTP $HOMEPAGE_CHECK"

if [ "$HOMEPAGE_CHECK" != "200" ]; then
    echo "🚨 CRITICAL: Homepage not accessible - fundamental failure"
fi

echo ""
echo "### Frontend Bundle Analysis"
HOMEPAGE_CONTENT=$(curl -s http://localhost:8000/)

# Extract all script tags
SCRIPT_TAGS=$(echo "$HOMEPAGE_CONTENT" | grep -o '<script[^>]*>' || echo "No script tags found")
echo "Script tags found:"
echo "$SCRIPT_TAGS"
echo ""

# Extract all CSS links
CSS_LINKS=$(echo "$HOMEPAGE_CONTENT" | grep -o '<link[^>]*stylesheet[^>]*>' || echo "No CSS links found")
echo "CSS links found:"
echo "$CSS_LINKS"
echo ""

# Check for JavaScript bundles
JS_BUNDLES=$(echo "$HOMEPAGE_CONTENT" | grep -o '/assets/[^"]*\.js' | sort -u)
echo "JavaScript bundles referenced:"
for bundle in $JS_BUNDLES; do
    echo "- $bundle"
    BUNDLE_STATUS=$(curl -s -w "%{http_code}" "http://localhost:8000$bundle" -o /dev/null)
    BUNDLE_SIZE=$(curl -s "http://localhost:8000$bundle" | wc -c)
    echo "  Status: HTTP $BUNDLE_STATUS, Size: $BUNDLE_SIZE bytes"
    
    if [ "$BUNDLE_STATUS" != "200" ]; then
        echo "  🚨 BUNDLE NOT ACCESSIBLE"
    elif [ "$BUNDLE_SIZE" -lt 1000 ]; then
        echo "  ⚠️ BUNDLE SUSPICIOUSLY SMALL"
    fi
done

echo ""
echo "## 📊 PHASE 2: JAVASCRIPT RUNTIME ANALYSIS"
echo ""

echo "### Bundle Content Analysis"
for bundle in $JS_BUNDLES; do
    if [ -n "$bundle" ]; then
        echo "#### Bundle: $bundle"
        BUNDLE_CONTENT=$(curl -s "http://localhost:8000$bundle")
        
        # Check for syntax errors
        if echo "$BUNDLE_CONTENT" | grep -q "SyntaxError\|ReferenceError\|TypeError"; then
            echo "🚨 SYNTAX ERRORS DETECTED in $bundle"
            echo "$BUNDLE_CONTENT" | grep -o "SyntaxError[^;]*\|ReferenceError[^;]*\|TypeError[^;]*" | head -3
        fi
        
        # Check for initialization issues
        if echo "$BUNDLE_CONTENT" | grep -q "Cannot access.*before initialization"; then
            echo "🚨 INITIALIZATION ORDER ERRORS in $bundle"
            echo "$BUNDLE_CONTENT" | grep -o "Cannot access[^;]*" | head -3
        fi
        
        # Check for circular dependencies
        if echo "$BUNDLE_CONTENT" | grep -q "Circular dependency\|circular import"; then
            echo "🚨 CIRCULAR DEPENDENCY DETECTED in $bundle"
        fi
        
        # Check for missing imports/exports
        IMPORT_COUNT=$(echo "$BUNDLE_CONTENT" | grep -c "import.*from" || echo "0")
        EXPORT_COUNT=$(echo "$BUNDLE_CONTENT" | grep -c "export" || echo "0")
        echo "- Import statements: $IMPORT_COUNT"
        echo "- Export statements: $EXPORT_COUNT"
        
        # Check for React presence
        if echo "$BUNDLE_CONTENT" | grep -q "react\|React"; then
            echo "- React library: PRESENT"
        else
            echo "- React library: MISSING"
        fi
        
        # Look for error patterns in first 2000 characters
        BUNDLE_HEAD=$(echo "$BUNDLE_CONTENT" | head -c 2000)
        if echo "$BUNDLE_HEAD" | grep -q "undefined.*is not a function\|null.*is not a function"; then
            echo "⚠️ POTENTIAL RUNTIME ERRORS detected"
        fi
        
        echo ""
    fi
done

echo ""
echo "## 📊 PHASE 3: BUILD SYSTEM ANALYSIS"
echo ""

echo "### Vite Configuration Analysis"
if [ -f "frontend/vite.config.js" ]; then
    echo "Vite config exists - analyzing..."
    
    # Check for problematic chunk splitting
    if grep -q "manualChunks" frontend/vite.config.js; then
        echo "🚨 MANUAL CHUNK SPLITTING DETECTED"
        echo "Current chunk configuration:"
        grep -A 10 "manualChunks" frontend/vite.config.js
    else
        echo "✅ No manual chunk splitting (good)"
    fi
    
    # Check build target
    BUILD_TARGET=$(grep -o "target.*es[0-9]*" frontend/vite.config.js || echo "not specified")
    echo "- Build target: $BUILD_TARGET"
    
    # Check minification
    MINIFY_SETTING=$(grep -o "minify.*['\"][^'\"]*['\"]" frontend/vite.config.js || echo "not specified")
    echo "- Minification: $MINIFY_SETTING"
    
else
    echo "🚨 VITE CONFIG MISSING"
fi

echo ""
echo "### Package.json Analysis"
if [ -f "frontend/package.json" ]; then
    echo "Frontend package.json exists - analyzing dependencies..."
    
    # Check for React version
    REACT_VERSION=$(grep -o '"react": "[^"]*"' frontend/package.json | cut -d'"' -f4 || echo "not found")
    echo "- React version: $REACT_VERSION"
    
    # Check for Vite version
    VITE_VERSION=$(grep -o '"vite": "[^"]*"' frontend/package.json | cut -d'"' -f4 || echo "not found")
    echo "- Vite version: $VITE_VERSION"
    
    # Check for conflicting dependencies
    if grep -q "@vitejs/plugin-react" frontend/package.json && grep -q "@vitejs/plugin-react-swc" frontend/package.json; then
        echo "🚨 CONFLICTING REACT PLUGINS DETECTED"
    fi
    
else
    echo "🚨 FRONTEND PACKAGE.JSON MISSING"
fi

echo ""
echo "## 📊 PHASE 4: DOCKER CONTAINER ANALYSIS"
echo ""

echo "### Container State Analysis"
CONTAINER_STATUS=$(docker ps --filter "name=whisper-app" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}")
echo "Container status:"
echo "$CONTAINER_STATUS"

# Check container logs for errors
echo ""
echo "### Container Error Analysis"
CONTAINER_ERRORS=$(docker logs whisper-app --tail 50 2>&1 | grep -i "error\|exception\|failed" | head -10)
if [ -n "$CONTAINER_ERRORS" ]; then
    echo "Recent container errors:"
    echo "$CONTAINER_ERRORS"
else
    echo "No obvious container errors found"
fi

# Check if frontend build exists in container
echo ""
echo "### Frontend Build Verification"
STATIC_FILES=$(docker exec whisper-app find /app/api/static -name "*.js" -o -name "*.css" 2>/dev/null | head -10)
if [ -n "$STATIC_FILES" ]; then
    echo "Static files in container:"
    echo "$STATIC_FILES"
else
    echo "🚨 NO STATIC FILES FOUND IN CONTAINER"
fi

echo ""
echo "## 📊 PHASE 5: NETWORK AND PROXY ANALYSIS"
echo ""

echo "### Port and Service Analysis"
# Check what's actually listening on port 8000
PORT_8000_PROCESS=$(netstat -tlnp 2>/dev/null | grep ":8000 " || echo "No process found on port 8000")
echo "Port 8000 status: $PORT_8000_PROCESS"

# Check if there are any proxy issues
echo ""
echo "### HTTP Response Header Analysis"
RESPONSE_HEADERS=$(curl -s -I http://localhost:8000/ | head -10)
echo "Response headers:"
echo "$RESPONSE_HEADERS"

# Check for CORS issues
if echo "$RESPONSE_HEADERS" | grep -q "Access-Control"; then
    echo "✅ CORS headers present"
else
    echo "⚠️ No CORS headers detected"
fi

echo ""
echo "## 📊 PHASE 6: FRONTEND SOURCE CODE ANALYSIS"
echo ""

echo "### React App Structure Analysis"
if [ -f "frontend/src/App.jsx" ] || [ -f "frontend/src/App.js" ]; then
    echo "Main App component exists"
    
    # Check for syntax issues in main App file
    APP_FILE=$(find frontend/src -name "App.*" | head -1)
    if [ -n "$APP_FILE" ]; then
        echo "Analyzing $APP_FILE..."
        
        # Check for obvious syntax issues
        if grep -q "import.*from ['\"][^'\"]*['\"]" "$APP_FILE"; then
            echo "✅ Import statements look normal"
        else
            echo "⚠️ Unusual import patterns detected"
        fi
        
        # Check for export
        if grep -q "export.*App\|export default" "$APP_FILE"; then
            echo "✅ App component is exported"
        else
            echo "🚨 App component export missing"
        fi
    fi
else
    echo "🚨 MAIN APP COMPONENT MISSING"
fi

echo ""
echo "### Service and API Integration Analysis"
if [ -d "frontend/src/services" ]; then
    echo "Services directory exists"
    SERVICE_FILES=$(find frontend/src/services -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" | wc -l)
    echo "- Service files found: $SERVICE_FILES"
else
    echo "⚠️ Services directory missing"
fi

echo ""
echo "## 🎯 FORENSIC SUMMARY AND CRITICAL FINDINGS"
echo ""

# Collect all critical issues found
CRITICAL_ISSUES=()

if [ "$HOMEPAGE_CHECK" != "200" ]; then
    CRITICAL_ISSUES+=("Homepage not accessible")
fi

if [ -z "$JS_BUNDLES" ]; then
    CRITICAL_ISSUES+=("No JavaScript bundles found")
fi

if ! echo "$HOMEPAGE_CONTENT" | grep -q 'id="root"'; then
    CRITICAL_ISSUES+=("React root container missing")
fi

if [ ${#CRITICAL_ISSUES[@]} -eq 0 ]; then
    echo "### ✅ No Critical Infrastructure Issues Found"
    echo "The application appears to have basic infrastructure in place."
    echo ""
    echo "### 🔍 Need Browser Console Investigation"
    echo "Since infrastructure looks OK but user reports JS errors, the issue may be:"
    echo "1. Runtime JavaScript errors not visible in static analysis"
    echo "2. Browser-specific compatibility issues"
    echo "3. Timing/race conditions during page load"
    echo "4. Network/caching issues"
    echo ""
    echo "### 📝 RECOMMENDED NEXT STEPS"
    echo "1. Check browser console for actual JavaScript errors"
    echo "2. Test in different browsers"
    echo "3. Clear browser cache completely"
    echo "4. Test in incognito/private mode"
    echo "5. Check network tab for failed resource loads"
else
    echo "### 🚨 CRITICAL ISSUES IDENTIFIED"
    for issue in "${CRITICAL_ISSUES[@]}"; do
        echo "- $issue"
    done
    echo ""
    echo "These issues must be resolved before the application can function."
fi

echo ""
echo "## 📋 DETAILED DIAGNOSTICS FOR USER"
echo ""
echo "To help debug the JavaScript errors you're experiencing:"
echo ""
echo "1. **Open Browser Developer Tools** (F12)"
echo "2. **Go to Console tab**"
echo "3. **Visit http://localhost:8000**"
echo "4. **Copy any error messages** (especially red errors)"
echo ""
echo "5. **Check Network tab** for failed resource loads"
echo "6. **Look for 404, 500, or other HTTP errors**"
echo ""
echo "This forensic report has been saved to: $FORENSIC_REPORT"
echo ""
echo "📊 **Forensic Investigation Complete**"
echo "Please share the specific JavaScript error messages from your browser console."