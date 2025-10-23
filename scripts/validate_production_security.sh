#!/bin/bash
# Production Security Validation
# Ensures no development tools reach production

set -e

echo "🔒 Production Security Validation"
echo "================================"

SECURITY_VIOLATIONS=0

echo "  1. Checking for development bypass tools..."
if find . -name "*bypass*" -o -name "*dev_auth*" | grep -v archive | grep -q .; then
    echo "     ❌ SECURITY VIOLATION: Development bypass tools found"
    find . -name "*bypass*" -o -name "*dev_auth*" | grep -v archive | sed 's/^/       /'
    SECURITY_VIOLATIONS=$((SECURITY_VIOLATIONS + 1))
else
    echo "     ✅ No development bypass tools found"
fi

echo "  2. Validating environment configuration..."
if [ "\$ENVIRONMENT" = "production" ]; then
    if grep -r "DEV_MODE\|DEBUG.*True\|BYPASS_AUTH" . --include="*.py" --include="*.env" | grep -v archive | grep -q .; then
        echo "     ❌ SECURITY VIOLATION: Development flags in production"
        grep -r "DEV_MODE\|DEBUG.*True\|BYPASS_AUTH" . --include="*.py" --include="*.env" | grep -v archive | sed 's/^/       /'
        SECURITY_VIOLATIONS=$((SECURITY_VIOLATIONS + 1))
    else
        echo "     ✅ No development flags in production configuration"
    fi
fi

echo "  3. Checking Docker configuration security..."
if grep -r "auth.*bypass\|disable.*auth" Dockerfile* docker-compose*.yml 2>/dev/null | grep -q .; then
    echo "     ❌ SECURITY VIOLATION: Authentication bypass in Docker configs"
    grep -r "auth.*bypass\|disable.*auth" Dockerfile* docker-compose*.yml | sed 's/^/       /'
    SECURITY_VIOLATIONS=$((SECURITY_VIOLATIONS + 1))
else
    echo "     ✅ Docker configurations secure"
fi

echo ""
if [ \$SECURITY_VIOLATIONS -eq 0 ]; then
    echo "✅ SECURITY VALIDATION PASSED"
    echo "   Production deployment approved"
    exit 0
else
    echo "❌ SECURITY VALIDATION FAILED"
    echo "   Found \$SECURITY_VIOLATIONS security violations"
    echo "   Production deployment BLOCKED"
    exit 1
fi
