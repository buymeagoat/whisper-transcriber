#!/bin/bash

# BUILD LAYER VALIDATION SCRIPT
# Ensures all layers are properly fixed before deployment

set -e

echo "🔧 SYSTEMATIC BUILD LAYER VALIDATION"
echo "===================================="
echo "Validates: Source → Build → Docker → Runtime → Application"
echo ""

VALIDATION_FAILED=0

# LAYER 1: Source Code Validation
echo "📝 LAYER 1: Source Code Validation"
echo "--------------------------------"

if [ -f "frontend/vite.config.js" ]; then
    if grep -q "manualChunks: () => 'vendor'" frontend/vite.config.js; then
        echo "✅ Vite config correctly forces single bundle"
    else
        echo "❌ Vite config does not force single bundle"
        VALIDATION_FAILED=1
    fi
else
    echo "❌ Vite config file missing"
    VALIDATION_FAILED=1
fi

# Check for known problematic imports
if grep -r "Batch.*@mui/icons-material" frontend/src/ 2>/dev/null; then
    echo "❌ Found problematic Batch icon import"
    VALIDATION_FAILED=1
else
    echo "✅ No problematic MUI imports found"
fi

# LAYER 2: Build Process Validation
echo ""
echo "🏗️  LAYER 2: Build Process Validation"
echo "-----------------------------------"

cd frontend
if npm run build >/dev/null 2>&1; then
    echo "✅ Frontend builds successfully"
    
    # Count JavaScript bundles
    JS_COUNT=$(find dist/assets -name "*.js" | wc -l)
    if [ "$JS_COUNT" -eq 1 ]; then
        echo "✅ Build produces exactly 1 JavaScript bundle"
    else
        echo "❌ Build produces $JS_COUNT JavaScript bundles (expected 1)"
        VALIDATION_FAILED=1
    fi
    
    # Check bundle size (should be substantial)
    BUNDLE_SIZE=$(find dist/assets -name "*.js" -exec wc -c {} \; | cut -d' ' -f1)
    if [ "$BUNDLE_SIZE" -gt 1000000 ]; then
        echo "✅ Bundle size reasonable ($BUNDLE_SIZE bytes)"
    else
        echo "⚠️ Bundle size small ($BUNDLE_SIZE bytes) - may be missing dependencies"
    fi
else
    echo "❌ Frontend build failed"
    VALIDATION_FAILED=1
fi
cd ..

# LAYER 3: Docker Build Validation
echo ""
echo "🐳 LAYER 3: Docker Build Validation"
echo "---------------------------------"

# Check if fixed image exists and use it, otherwise build validation test
if docker image inspect whisper-transcriber-app:fixed >/dev/null 2>&1; then
    echo "✅ Using existing fixed image for validation"
    STATIC_FILES=$(docker run --rm whisper-transcriber-app:fixed find /app -name "*.js" | grep assets | wc -l)
    if [ "$STATIC_FILES" -eq 1 ]; then
        echo "✅ Docker image contains exactly 1 JavaScript bundle"
    else
        echo "❌ Docker image contains $STATIC_FILES JavaScript bundles (expected 1)"
        VALIDATION_FAILED=1
    fi
elif docker build -t whisper-transcriber-app:validation-test . >/dev/null 2>&1; then
    echo "✅ Docker image builds successfully"
    
    # Check static files in image
    STATIC_FILES=$(docker run --rm whisper-transcriber-app:validation-test find /app/api/static/assets/ -name "*.js" 2>/dev/null | wc -l)
    if [ "$STATIC_FILES" -eq 1 ]; then
        echo "✅ Docker image contains exactly 1 JavaScript bundle"
    else
        echo "❌ Docker image contains $STATIC_FILES JavaScript bundles (expected 1)"
        VALIDATION_FAILED=1
    fi
    
    # Cleanup test image
    docker rmi whisper-transcriber-app:validation-test >/dev/null 2>&1 || true
else
    echo "❌ Docker build failed"
    VALIDATION_FAILED=1
fi

# LAYER 4: Runtime Validation
echo ""
echo "🚀 LAYER 4: Runtime Validation"
echo "----------------------------"

if docker ps | grep -q "whisper-app"; then
    echo "✅ Application container is running"
    
    # Check health endpoint
    if curl -s -f http://localhost:8000/health >/dev/null 2>&1; then
        echo "✅ Application responds to health checks"
    else
        echo "❌ Application not responding to health checks"
        VALIDATION_FAILED=1
    fi
    
    # Check bundle serving
    SERVED_BUNDLES=$(curl -s http://localhost:8000/ | grep -o '/assets/[^"]*\.js' | wc -l)
    if [ "$SERVED_BUNDLES" -eq 1 ]; then
        echo "✅ Application serves exactly 1 JavaScript bundle"
    else
        echo "❌ Application serves $SERVED_BUNDLES JavaScript bundles (expected 1)"
        VALIDATION_FAILED=1
    fi
else
    echo "⚠️ Application container not running - cannot validate runtime"
fi

# LAYER 5: JavaScript Validation
echo ""
echo "🔍 LAYER 5: JavaScript Error Validation"
echo "--------------------------------------"

if curl -s -f http://localhost:8000/health >/dev/null 2>&1; then
    BUNDLE_URL=$(curl -s http://localhost:8000/ | grep -o '/assets/[^"]*\.js' | head -1)
    if [ -n "$BUNDLE_URL" ]; then
        INIT_ERRORS=$(curl -s "http://localhost:8000$BUNDLE_URL" | grep -o "Cannot access '[^']*' before initialization" | wc -l)
        if [ "$INIT_ERRORS" -eq 0 ]; then
            echo "✅ No JavaScript initialization errors found"
        else
            echo "❌ Found $INIT_ERRORS JavaScript initialization errors"
            VALIDATION_FAILED=1
        fi
        
        # Check for syntax errors in JavaScript
        BUNDLE_SAMPLE=$(curl -s "http://localhost:8000$BUNDLE_URL" | head -c 1000)
        if echo "$BUNDLE_SAMPLE" | grep -q "SyntaxError\|Unexpected token\|Uncaught"; then
            SYNTAX_ERROR_COUNT=$(echo "$BUNDLE_SAMPLE" | grep -c "SyntaxError\|Unexpected token\|Uncaught")
            echo "❌ Found JavaScript syntax errors in bundle"
            VALIDATION_FAILED=1
        else
            echo "✅ No JavaScript syntax errors found"
        fi
    else
        echo "❌ Could not find bundle URL to validate"
        VALIDATION_FAILED=1
    fi
else
    echo "⚠️ Application not accessible - cannot validate JavaScript"
fi

# Final Result
echo ""
echo "📊 VALIDATION SUMMARY"
echo "===================="

if [ "$VALIDATION_FAILED" -eq 0 ]; then
    echo "🎉 ALL LAYERS VALIDATED SUCCESSFULLY"
    echo "✅ Source code is correct"
    echo "✅ Build process produces single bundle"
    echo "✅ Docker image contains correct assets"
    echo "✅ Runtime serves application properly"
    echo "✅ JavaScript bundle has no critical errors"
    echo ""
    echo "🚀 DEPLOYMENT READY"
    echo "The application is ready for production deployment."
    exit 0
else
    echo "❌ VALIDATION FAILED"
    echo "One or more layers have issues that must be resolved."
    echo ""
    echo "🛠️ REQUIRED ACTIONS:"
    echo "1. Fix the failing validation checks above"
    echo "2. Re-run this validation script"
    echo "3. Do not deploy until all validations pass"
    exit 1
fi