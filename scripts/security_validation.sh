#!/bin/bash

# Security Validation Script
# Comprehensive security checks for development and production

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    local level=$1
    shift
    echo -e "${GREEN}[$(date '+%H:%M:%S')] $level: $*${NC}"
}

error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ERROR: $*${NC}" >&2
}

warn() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] WARN: $*${NC}" >&2
}

# Security validation functions
validate_secrets() {
    log "INFO" "🔐 Validating secrets management"
    
    local issues=0
    
    # Check for hardcoded secrets
    if grep -r "SECRET_KEY.*=" "$PROJECT_ROOT/api/" | grep -v ".example" | grep -E "(admin123|password|secret)" >/dev/null 2>&1; then
        error "Hardcoded secrets found in codebase"
        ((issues++))
    fi
    
    # Check for committed secrets
    if git log --all --full-history -- "$PROJECT_ROOT/.env" >/dev/null 2>&1; then
        warn "Environment file may have been committed to git history"
        ((issues++))
    fi
    
    # Check environment templates exist
    if [[ ! -f "$PROJECT_ROOT/.env.example" ]]; then
        error "Missing .env.example template"
        ((issues++))
    fi
    
    if [[ $issues -eq 0 ]]; then
        log "INFO" "✅ Secrets management validation passed"
        return 0
    else
        error "❌ Secrets management validation failed ($issues issues)"
        return 1
    fi
}

validate_authentication() {
    log "INFO" "🔒 Validating authentication security"
    
    local issues=0
    
    # Check for in-memory user stores
    if grep -r "USERS_DB.*=" "$PROJECT_ROOT/api/" | grep -v test >/dev/null 2>&1; then
        error "In-memory user database found - use persistent storage"
        ((issues++))
    fi
    
    # Check for weak password hashing
    if grep -r "hashlib.sha256\|md5\|sha1" "$PROJECT_ROOT/api/" >/dev/null 2>&1; then
        error "Weak password hashing algorithms detected"
        ((issues++))
    fi
    
    # Check JWT secret key validation
    if ! grep -r "SECRET_KEY.*validation" "$PROJECT_ROOT/api/" >/dev/null 2>&1; then
        warn "JWT secret key validation may be missing"
        ((issues++))
    fi
    
    if [[ $issues -eq 0 ]]; then
        log "INFO" "✅ Authentication security validation passed"
        return 0
    else
        error "❌ Authentication security validation failed ($issues issues)"
        return 1
    fi
}

validate_session_security() {
    log "INFO" "🍪 Validating session security"
    
    local issues=0
    
    # Check for localStorage token storage
    if grep -r "localStorage.*token\|sessionStorage.*token" "$PROJECT_ROOT/frontend/src/" >/dev/null 2>&1; then
        error "Tokens stored in localStorage/sessionStorage - use httpOnly cookies"
        ((issues++))
    fi
    
    # Check CSP configuration
    if grep -r "unsafe-inline\|unsafe-eval" "$PROJECT_ROOT/api/" >/dev/null 2>&1; then
        error "Unsafe CSP directives found"
        ((issues++))
    fi
    
    if [[ $issues -eq 0 ]]; then
        log "INFO" "✅ Session security validation passed"
        return 0
    else
        error "❌ Session security validation failed ($issues issues)"
        return 1
    fi
}

validate_infrastructure() {
    log "INFO" "🏗️ Validating infrastructure security"
    
    local issues=0
    
    # Check Docker security
    if grep -r "seccomp:unconfined" "$PROJECT_ROOT/docker-compose.yml" >/dev/null 2>&1; then
        warn "Docker seccomp disabled - security risk"
        ((issues++))
    fi
    
    # Check for committed passwords
    if grep -r "password.*=" "$PROJECT_ROOT/docker-compose.yml" | grep -v "CHANGE_ME" >/dev/null 2>&1; then
        error "Passwords committed in docker-compose.yml"
        ((issues++))
    fi
    
    if [[ $issues -eq 0 ]]; then
        log "INFO" "✅ Infrastructure security validation passed"
        return 0
    else
        error "❌ Infrastructure security validation failed ($issues issues)"
        return 1
    fi
}

validate_dependencies() {
    log "INFO" "📦 Validating dependency security"
    
    local issues=0
    
    # Check Python dependencies
    if command -v safety >/dev/null 2>&1; then
        if ! safety check -r "$PROJECT_ROOT/requirements.txt" >/dev/null 2>&1; then
            warn "Python dependency vulnerabilities detected"
            ((issues++))
        fi
    else
        warn "Safety not installed - cannot check Python dependencies"
    fi
    
    # Check Node.js dependencies if frontend exists
    if [[ -f "$PROJECT_ROOT/frontend/package.json" ]]; then
        cd "$PROJECT_ROOT/frontend"
        if command -v npm >/dev/null 2>&1; then
            if ! npm audit --audit-level=high >/dev/null 2>&1; then
                warn "Node.js dependency vulnerabilities detected"
                ((issues++))
            fi
        fi
        cd "$PROJECT_ROOT"
    fi
    
    if [[ $issues -eq 0 ]]; then
        log "INFO" "✅ Dependency security validation passed"
        return 0
    else
        warn "⚠️ Dependency security validation completed with warnings ($issues issues)"
        return 0  # Don't fail on dependency warnings
    fi
}

# Main validation function
run_security_validation() {
    log "INFO" "🔍 Starting comprehensive security validation"
    
    local total_issues=0
    
    # Run all validation checks
    validate_secrets || ((total_issues++))
    validate_authentication || ((total_issues++))
    validate_session_security || ((total_issues++))
    validate_infrastructure || ((total_issues++))
    validate_dependencies || true  # Don't count warnings as failures
    
    echo ""
    if [[ $total_issues -eq 0 ]]; then
        log "INFO" "✅ All security validations passed"
        return 0
    else
        error "❌ Security validation failed with $total_issues critical issues"
        error "Fix these issues before proceeding with deployment"
        return 1
    fi
}

# Generate security report
generate_security_report() {
    local report_file="$PROJECT_ROOT/reports/security_validation_$(date '+%Y%m%d_%H%M%S').md"
    mkdir -p "$(dirname "$report_file")"
    
    log "INFO" "📄 Generating security report: $report_file"
    
    cat > "$report_file" << EOF
# Security Validation Report

**Date**: $(date '+%Y-%m-%d %H:%M:%S')
**Generated by**: Security Validation Script

## Summary

This report contains the results of comprehensive security validation checks.

## Validation Results

### Secrets Management
$(validate_secrets 2>&1 | sed 's/\x1b\[[0-9;]*m//g' || echo "FAILED")

### Authentication Security  
$(validate_authentication 2>&1 | sed 's/\x1b\[[0-9;]*m//g' || echo "FAILED")

### Session Security
$(validate_session_security 2>&1 | sed 's/\x1b\[[0-9;]*m//g' || echo "FAILED")

### Infrastructure Security
$(validate_infrastructure 2>&1 | sed 's/\x1b\[[0-9;]*m//g' || echo "FAILED")

### Dependency Security
$(validate_dependencies 2>&1 | sed 's/\x1b\[[0-9;]*m//g' || echo "COMPLETED")

## Recommendations

1. Address all critical security issues before production deployment
2. Implement regular security audits
3. Keep dependencies updated
4. Monitor security advisories

---
*Generated by Change Management System*
EOF

    echo "$report_file"
}

main() {
    local action="${1:-validate}"
    
    case "$action" in
        "validate")
            run_security_validation
            ;;
        "report")
            generate_security_report
            ;;
        "help"|*)
            echo "Security Validation Script"
            echo ""
            echo "Usage: $0 <action>"
            echo ""
            echo "Actions:"
            echo "  validate - Run security validation checks"
            echo "  report   - Generate security validation report"
            echo "  help     - Show this help"
            ;;
    esac
}

main "$@"