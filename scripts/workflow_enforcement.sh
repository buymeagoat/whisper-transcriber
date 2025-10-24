#!/bin/bash

# Comprehensive Development-Production Parity Workflow
# Enforces mandatory quality standards and change management

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

log() {
    echo -e "${GREEN}🔄 Workflow: $*${NC}"
}

error() {
    echo -e "${RED}❌ Error: $*${NC}" >&2
}

warn() {
    echo -e "${YELLOW}⚠️  Warning: $*${NC}"
}

info() {
    echo -e "${BLUE}ℹ️  Info: $*${NC}"
}

header() {
    echo -e "${BOLD}${BLUE}$*${NC}"
}

# Function: Display workflow requirements
show_workflow_requirements() {
    header "🔐 MANDATORY DEVELOPMENT-PRODUCTION PARITY WORKFLOW"
    echo ""
    echo "This system enforces the following MANDATORY behaviors:"
    echo ""
    echo "1. 🧪 TESTING REQUIREMENT:"
    echo "   - All changes MUST be tested in development first"
    echo "   - Viability confirmation required before production"
    echo "   - Automated test suite execution mandatory"
    echo ""
    echo "2. 📚 DOCUMENTATION REQUIREMENT:"
    echo "   - CHANGELOG.md MUST be updated for all changes"
    echo "   - TASKS.md MUST be updated with completion status"
    echo "   - Technical documentation MUST reflect changes"
    echo ""
    echo "3. 🔄 PARITY REQUIREMENT:"
    echo "   - Changes mirrored between development and production"
    echo "   - Environment configuration consistency enforced"
    echo "   - Security validation mandatory for sensitive changes"
    echo ""
    echo "4. 🗂️  LIFECYCLE REQUIREMENT:"
    echo "   - Completed tasks automatically archived"
    echo "   - Change logs generated for all modifications"
    echo "   - Audit trail maintained for compliance"
    echo ""
    echo "❌ COMMITS WILL BE BLOCKED if requirements are not met"
    echo ""
}

# Function: Initialize development environment
init_development_environment() {
    log "Initializing development environment for testing..."
    
    # Check if development environment is ready
    if [[ ! -f "$PROJECT_ROOT/.env.dev" ]]; then
        error "Development environment configuration missing"
        error "Create .env.dev before proceeding"
        return 1
    fi
    
    # Validate Docker environment
    if ! docker-compose -f "$PROJECT_ROOT/docker-compose.yml" config >/dev/null 2>&1; then
        error "Docker configuration invalid"
        return 1
    fi
    
    log "Development environment validated"
    return 0
}

# Function: Run comprehensive development tests
run_development_tests() {
    local change_description="$1"
    
    header "🧪 MANDATORY DEVELOPMENT TESTING"
    log "Running comprehensive test suite for: $change_description"
    
    local test_results=()
    local failed_tests=0
    
    # Backend API Tests
    info "Running backend API tests..."
    if "$SCRIPT_DIR/run_backend_tests.sh" >/dev/null 2>&1; then
        test_results+=("✅ Backend API tests: PASSED")
    else
        test_results+=("❌ Backend API tests: FAILED")
        ((failed_tests++))
    fi
    
    # Frontend Tests (if frontend changes detected)
    if git diff --cached --name-only | grep -q "^frontend/"; then
        info "Running frontend tests..."
        cd "$PROJECT_ROOT/frontend"
        if npm test >/dev/null 2>&1; then
            test_results+=("✅ Frontend tests: PASSED")
        else
            test_results+=("❌ Frontend tests: FAILED")
            ((failed_tests++))
        fi
        cd "$PROJECT_ROOT"
    fi
    
    # Integration Tests
    info "Running integration tests..."
    if pytest "$PROJECT_ROOT/tests/" -v >/dev/null 2>&1; then
        test_results+=("✅ Integration tests: PASSED")
    else
        test_results+=("❌ Integration tests: FAILED")
        ((failed_tests++))
    fi
    
    # Security Validation
    info "Running security validation..."
    if "$SCRIPT_DIR/security_validation.sh" validate >/dev/null 2>&1; then
        test_results+=("✅ Security validation: PASSED")
    else
        test_results+=("❌ Security validation: FAILED")
        ((failed_tests++))
    fi
    
    # Display results
    echo ""
    info "Test Results Summary:"
    for result in "${test_results[@]}"; do
        echo "  $result"
    done
    echo ""
    
    if [[ $failed_tests -eq 0 ]]; then
        log "✅ ALL DEVELOPMENT TESTS PASSED - Change viable for production"
        return 0
    else
        error "❌ DEVELOPMENT TESTS FAILED ($failed_tests failures)"
        error "🚫 CHANGE NOT VIABLE - Fix issues before proceeding"
        return 1
    fi
}

# Function: Validate production readiness
validate_production_readiness() {
    local change_description="$1"
    
    header "🏭 MANDATORY PRODUCTION READINESS VALIDATION"
    log "Validating production readiness for: $change_description"
    
    local validations=()
    local failed_validations=0
    
    # Environment parity check
    info "Checking environment parity..."
    if [[ -f "$PROJECT_ROOT/.env.production.template" ]]; then
        validations+=("✅ Production environment template: EXISTS")
    else
        validations+=("❌ Production environment template: MISSING")
        ((failed_validations++))
    fi
    
    # Docker production build validation
    info "Validating Docker production build..."
    if docker-compose -f "$PROJECT_ROOT/docker-compose.yml" config >/dev/null 2>&1; then
        validations+=("✅ Docker production config: VALID")
    else
        validations+=("❌ Docker production config: INVALID")
        ((failed_validations++))
    fi
    
    # Security configuration check
    info "Checking security configuration..."
    if grep -q "SECRET_KEY.*=" "$PROJECT_ROOT/.env.production.template"; then
        validations+=("✅ Security configuration: DEFINED")
    else
        validations+=("❌ Security configuration: MISSING")
        ((failed_validations++))
    fi
    
    # Database migration check
    info "Checking database migrations..."
    if [[ -d "$PROJECT_ROOT/api/migrations" ]]; then
        validations+=("✅ Database migrations: AVAILABLE")
    else
        validations+=("⚠️  Database migrations: NOT CONFIGURED")
    fi
    
    # Display results
    echo ""
    info "Production Readiness Summary:"
    for validation in "${validations[@]}"; do
        echo "  $validation"
    done
    echo ""
    
    if [[ $failed_validations -eq 0 ]]; then
        log "✅ PRODUCTION READINESS VALIDATED - Ready for deployment"
        return 0
    else
        error "❌ PRODUCTION READINESS FAILED ($failed_validations issues)"
        error "🚫 NOT READY FOR PRODUCTION - Fix issues before deploying"
        return 1
    fi
}

# Function: Enforce documentation updates
enforce_documentation_updates() {
    local change_description="$1"
    local task_id="${2:-}"
    
    header "📚 MANDATORY DOCUMENTATION UPDATES"
    log "Enforcing documentation updates for: $change_description"
    
    local doc_updates=()
    local missing_updates=0
    
    # Check CHANGELOG.md update
    if git diff --cached --name-only | grep -q "CHANGELOG.md"; then
        doc_updates+=("✅ CHANGELOG.md: UPDATED")
    else
        doc_updates+=("❌ CHANGELOG.md: NOT UPDATED")
        ((missing_updates++))
    fi
    
    # Check TASKS.md update (if task_id provided)
    if [[ -n "$task_id" ]]; then
        if git diff --cached "TASKS.md" | grep -q "$task_id.*✅.*COMPLETED"; then
            doc_updates+=("✅ TASKS.md: TASK COMPLETED")
        else
            doc_updates+=("❌ TASKS.md: TASK NOT MARKED COMPLETE")
            ((missing_updates++))
        fi
    fi
    
    # Check technical documentation
    if git diff --cached --name-only | grep -qE "^docs/|README.md"; then
        doc_updates+=("✅ Technical docs: UPDATED")
    else
        # Only require if code changes were made
        if git diff --cached --name-only | grep -qE "^(api|frontend)/"; then
            doc_updates+=("❌ Technical docs: NOT UPDATED")
            ((missing_updates++))
        else
            doc_updates+=("ℹ️  Technical docs: NO CODE CHANGES")
        fi
    fi
    
    # Display results
    echo ""
    info "Documentation Update Summary:"
    for update in "${doc_updates[@]}"; do
        echo "  $update"
    done
    echo ""
    
    if [[ $missing_updates -eq 0 ]]; then
        log "✅ DOCUMENTATION REQUIREMENTS SATISFIED"
        return 0
    else
        error "❌ DOCUMENTATION REQUIREMENTS NOT MET ($missing_updates missing)"
        error "🚫 MANDATORY: Update all documentation before committing"
        
        echo ""
        error "Required actions:"
        if echo "${doc_updates[@]}" | grep -q "CHANGELOG.md: NOT UPDATED"; then
            error "  - Add entry to CHANGELOG.md describing the change"
        fi
        if echo "${doc_updates[@]}" | grep -q "TASKS.md: TASK NOT MARKED COMPLETE"; then
            error "  - Mark task $task_id as completed in TASKS.md"
        fi
        if echo "${doc_updates[@]}" | grep -q "Technical docs: NOT UPDATED"; then
            error "  - Update relevant technical documentation"
        fi
        
        return 1
    fi
}

# Function: Execute complete workflow
execute_workflow() {
    local change_description="$1"
    local task_id="${2:-}"
    
    header "🔐 EXECUTING MANDATORY DEVELOPMENT-PRODUCTION PARITY WORKFLOW"
    echo ""
    info "Change: $change_description"
    info "Task ID: ${task_id:-N/A}"
    echo ""
    
    # Step 1: Initialize development environment
    if ! init_development_environment; then
        error "🚫 WORKFLOW BLOCKED: Development environment not ready"
        return 1
    fi
    
    # Step 2: Run comprehensive development tests
    if ! run_development_tests "$change_description"; then
        error "🚫 WORKFLOW BLOCKED: Development tests failed"
        return 1
    fi
    
    # Step 3: Validate production readiness
    if ! validate_production_readiness "$change_description"; then
        error "🚫 WORKFLOW BLOCKED: Production readiness validation failed"
        return 1
    fi
    
    # Step 4: Enforce documentation updates
    if ! enforce_documentation_updates "$change_description" "$task_id"; then
        error "🚫 WORKFLOW BLOCKED: Documentation requirements not met"
        return 1
    fi
    
    # Step 5: Generate change management artifacts
    header "📋 GENERATING CHANGE MANAGEMENT ARTIFACTS"
    
    # Create change log
    local change_log=$("$SCRIPT_DIR/change_management.sh" validate "$change_description" "$task_id" 2>/dev/null | grep "change_.*\.md" || echo "")
    if [[ -n "$change_log" ]]; then
        log "Change log generated: $change_log"
    fi
    
    # Archive completed tasks
    if [[ -n "$task_id" ]]; then
        "$SCRIPT_DIR/task_lifecycle.sh" archive >/dev/null 2>&1
        log "Completed tasks archived"
    fi
    
    # Final success
    header "✅ MANDATORY WORKFLOW COMPLETED SUCCESSFULLY"
    echo ""
    log "🔐 Development-Production Parity Enforced"
    log "📋 All Quality Standards Met"
    log "🚀 Ready for Production Deployment"
    echo ""
    
    return 0
}

# Function: Show status
show_status() {
    header "🔍 DEVELOPMENT-PRODUCTION PARITY STATUS"
    echo ""
    
    # Check current git status
    local staged_files=$(git diff --cached --name-only | wc -l)
    local modified_files=$(git diff --name-only | wc -l)
    
    info "Repository Status:"
    echo "  - Staged files: $staged_files"
    echo "  - Modified files: $modified_files"
    echo ""
    
    # Check if workflow requirements are in place
    info "Workflow Infrastructure:"
    
    if [[ -x "$SCRIPT_DIR/change_management.sh" ]]; then
        echo "  ✅ Change management system: ACTIVE"
    else
        echo "  ❌ Change management system: MISSING"
    fi
    
    if [[ -x "$SCRIPT_DIR/security_validation.sh" ]]; then
        echo "  ✅ Security validation: ACTIVE"
    else
        echo "  ❌ Security validation: MISSING"
    fi
    
    if [[ -x "$SCRIPT_DIR/task_lifecycle.sh" ]]; then
        echo "  ✅ Task lifecycle management: ACTIVE"
    else
        echo "  ❌ Task lifecycle management: MISSING"
    fi
    
    if [[ -f "$PROJECT_ROOT/.git/hooks/pre-commit" ]]; then
        echo "  ✅ Pre-commit enforcement: ACTIVE"
    else
        echo "  ❌ Pre-commit enforcement: MISSING"
    fi
    
    echo ""
    
    # Check pending tasks
    if [[ -f "$PROJECT_ROOT/TASKS.md" ]]; then
        local pending_tasks=$(grep -c "^\s*-\s*\[\s*\]\s*" "$PROJECT_ROOT/TASKS.md" 2>/dev/null || echo "0")
        local completed_tasks=$(grep -c "^\s*-\s*\[x\].*✅.*COMPLETED" "$PROJECT_ROOT/TASKS.md" 2>/dev/null || echo "0")
        
        info "Task Management:"
        echo "  - Pending tasks: $pending_tasks"
        echo "  - Completed tasks: $completed_tasks"
    fi
    
    echo ""
}

# Main function
main() {
    local action="${1:-help}"
    
    case "$action" in
        "execute"|"run")
            local change_description="${2:-}"
            local task_id="${3:-}"
            
            if [[ -z "$change_description" ]]; then
                error "Change description required"
                error "Usage: $0 execute '<description>' [task_id]"
                return 1
            fi
            
            execute_workflow "$change_description" "$task_id"
            ;;
        "requirements"|"info")
            show_workflow_requirements
            ;;
        "status")
            show_status
            ;;
        "help"|*)
            echo "Development-Production Parity Workflow Enforcement"
            echo ""
            echo "Usage: $0 <action> [arguments...]"
            echo ""
            echo "Actions:"
            echo "  execute <description> [task_id]  - Run complete workflow validation"
            echo "  requirements                     - Show workflow requirements"
            echo "  status                           - Show current workflow status"
            echo "  help                             - Show this help"
            echo ""
            echo "Examples:"
            echo "  $0 execute 'Implement authentication security hardening' S001"
            echo "  $0 requirements"
            echo "  $0 status"
            echo ""
            echo "This system enforces MANDATORY quality standards including:"
            echo "  - Development testing before production"
            echo "  - Documentation updates with all changes"  
            echo "  - Environment parity validation"
            echo "  - Security validation for sensitive changes"
            echo "  - Automatic task lifecycle management"
            ;;
    esac
}

main "$@"