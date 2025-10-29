#!/bin/bash

# Testing Integration Manager
# Integrates multi-role testing with existing workflow enforcement
# Implements smart hybrid approach: fast pre-commit + comprehensive post-commit

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration
LOG_FILE="${REPO_ROOT}/logs/testing_integration.log"
INTEGRATION_CONFIG="${REPO_ROOT}/.testing_integration_config"

# Logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Load integration configuration
load_config() {
    if [[ -f "$INTEGRATION_CONFIG" ]]; then
        source "$INTEGRATION_CONFIG"
    else
        # Default configuration
        cat > "$INTEGRATION_CONFIG" << 'EOF'
# Testing Integration Configuration

# Testing timing mode: pre-commit, post-commit, hybrid
TESTING_MODE="hybrid"

# Testing scope: smart (triggered), full (always), user-choice
TESTING_SCOPE="smart"

# Build validation frequency: every-commit, continuous, on-demand
BUILD_VALIDATION="continuous"

# Documentation management: with-changes, periodic, triggered
DOC_MANAGEMENT="triggered"

# Role-specific settings
ENABLE_SENIOR_DEVELOPER=true
ENABLE_PROJECT_MANAGER=true
ENABLE_QA_ENGINEER=true
ENABLE_END_USER=true
ENABLE_SECURITY_AUDITOR=true
ENABLE_UX_UI_DEVELOPER=true

# Performance settings
PARALLEL_TESTING=true
MAX_PARALLEL_ROLES=3
TIMEOUT_MINUTES=30
EOF
        log "Created default integration configuration"
    fi
    source "$INTEGRATION_CONFIG"
}

# Get changed files since last commit
get_changed_files() {
    local base="${1:-HEAD~1}"
    git diff --name-only "$base" HEAD 2>/dev/null || echo ""
}

# Determine testing phase
determine_testing_phase() {
    local context="$1"  # pre-commit, post-commit, manual
    
    case "$TESTING_MODE" in
        "pre-commit")
            echo "pre-commit"
            ;;
        "post-commit")
            echo "post-commit"
            ;;
        "hybrid")
            case "$context" in
                "pre-commit") echo "fast-pre-commit" ;;
                "post-commit") echo "comprehensive-post-commit" ;;
                *) echo "comprehensive" ;;
            esac
            ;;
        *)
            echo "comprehensive"
            ;;
    esac
}

# Run fast pre-commit testing
run_fast_testing() {
    local changed_files="$1"
    
    log "Running fast pre-commit testing"
    
    # Quick security check
    if echo "$changed_files" | grep -q "auth\|security\|middleware"; then
        log "Security-related changes detected, running security audit"
        "$SCRIPT_DIR/multi_role_testing.sh" run security_auditor smart "$changed_files"
    fi
    
    # Quick code quality for code changes
    if echo "$changed_files" | grep -q "\.py$\|\.js$\|\.jsx$\|\.ts$\|\.tsx$"; then
        log "Code changes detected, running code quality check"
        "$SCRIPT_DIR/multi_role_testing.sh" run senior_developer smart "$changed_files"
    fi
    
    # Quick functional test for API changes
    if echo "$changed_files" | grep -q "api/\|routes/\|services/"; then
        log "API changes detected, running quick functional tests"
        timeout 300 "$SCRIPT_DIR/multi_role_testing.sh" run qa_engineer smart "$changed_files" || {
            log "Fast functional tests timed out or failed"
            return 1
        }
    fi
    
    log "Fast pre-commit testing completed"
}

# Run comprehensive post-commit testing
run_comprehensive_testing() {
    local changed_files="$1"
    local mode="${2:-smart}"
    
    log "Running comprehensive testing (mode: $mode)"
    
    # Determine which roles to run
    local roles_to_run=()
    
    if [[ "$TESTING_SCOPE" == "full" ]]; then
        # Run all enabled roles
        [[ "$ENABLE_SENIOR_DEVELOPER" == "true" ]] && roles_to_run+=("senior_developer")
        [[ "$ENABLE_PROJECT_MANAGER" == "true" ]] && roles_to_run+=("project_manager")
        [[ "$ENABLE_QA_ENGINEER" == "true" ]] && roles_to_run+=("qa_engineer")
        [[ "$ENABLE_END_USER" == "true" ]] && roles_to_run+=("end_user")
        [[ "$ENABLE_SECURITY_AUDITOR" == "true" ]] && roles_to_run+=("security_auditor")
        [[ "$ENABLE_UX_UI_DEVELOPER" == "true" ]] && roles_to_run+=("ux_ui_developer")
    else
        # Smart mode - only run triggered roles
        roles_to_run=($(determine_triggered_roles "$changed_files"))
    fi
    
    if [[ ${#roles_to_run[@]} -eq 0 ]]; then
        log "No roles triggered for comprehensive testing"
        return 0
    fi
    
    log "Running comprehensive testing for roles: ${roles_to_run[*]}"
    
    # Run roles in parallel or sequential based on configuration
    if [[ "$PARALLEL_TESTING" == "true" ]] && [[ ${#roles_to_run[@]} -gt 1 ]]; then
        run_parallel_testing "${roles_to_run[@]}"
    else
        run_sequential_testing "${roles_to_run[@]}"
    fi
}

# Determine which roles are triggered by changes
determine_triggered_roles() {
    local changed_files="$1"
    local triggered_roles=()
    
    # Check each role's trigger conditions
    if [[ "$ENABLE_SENIOR_DEVELOPER" == "true" ]] && echo "$changed_files" | grep -q "\.py$\|\.js$\|\.jsx$\|\.ts$\|\.tsx$\|api/\|backend/"; then
        triggered_roles+=("senior_developer")
    fi
    
    if [[ "$ENABLE_PROJECT_MANAGER" == "true" ]] && echo "$changed_files" | grep -q "TASKS\.md\|requirements\|docs/\|README\.md"; then
        triggered_roles+=("project_manager")
    fi
    
    if [[ "$ENABLE_QA_ENGINEER" == "true" ]] && echo "$changed_files" | grep -q "tests/\|\.test\.\|cypress/\|api/\|frontend/"; then
        triggered_roles+=("qa_engineer")
    fi
    
    if [[ "$ENABLE_END_USER" == "true" ]] && echo "$changed_files" | grep -q "frontend/\|ui/\|components/\|pages/"; then
        triggered_roles+=("end_user")
    fi
    
    if [[ "$ENABLE_SECURITY_AUDITOR" == "true" ]] && echo "$changed_files" | grep -q "auth\|security\|middlewares/\|\.env\|docker"; then
        triggered_roles+=("security_auditor")
    fi
    
    if [[ "$ENABLE_UX_UI_DEVELOPER" == "true" ]] && echo "$changed_files" | grep -q "frontend/\|ui/\|components/\|styles/\|\.css\|\.scss"; then
        triggered_roles+=("ux_ui_developer")
    fi
    
    echo "${triggered_roles[@]}"
}

# Run roles in parallel
run_parallel_testing() {
    local roles=("$@")
    local pids=()
    local results=()
    
    log "Running ${#roles[@]} roles in parallel (max: $MAX_PARALLEL_ROLES)"
    
    # Start roles in batches
    local batch_size=${MAX_PARALLEL_ROLES:-3}
    local batch_start=0
    
    while [[ $batch_start -lt ${#roles[@]} ]]; do
        local batch_end=$((batch_start + batch_size))
        [[ $batch_end -gt ${#roles[@]} ]] && batch_end=${#roles[@]}
        
        # Start batch
        for ((i=batch_start; i<batch_end; i++)); do
            local role="${roles[$i]}"
            log "Starting role: $role"
            timeout "${TIMEOUT_MINUTES:-30}m" "$SCRIPT_DIR/multi_role_testing.sh" run "$role" full &
            pids+=($!)
            results+=("$role:pending")
        done
        
        # Wait for batch to complete
        for ((i=0; i<${#pids[@]}; i++)); do
            local pid="${pids[$i]}"
            local role="${roles[$((batch_start + i))]}"
            
            if wait "$pid"; then
                results[$((batch_start + i))]="$role:passed"
                log "✅ Role $role completed successfully"
            else
                results[$((batch_start + i))]="$role:failed"
                log "❌ Role $role failed"
            fi
        done
        
        pids=()
        batch_start=$batch_end
    done
    
    # Report results
    local failed_count=0
    for result in "${results[@]}"; do
        if [[ "$result" == *":failed" ]]; then
            failed_count=$((failed_count + 1))
        fi
    done
    
    if [[ $failed_count -eq 0 ]]; then
        log "🎉 All parallel testing completed successfully"
        return 0
    else
        log "💥 $failed_count role(s) failed in parallel testing"
        return 1
    fi
}

# Run roles sequentially
run_sequential_testing() {
    local roles=("$@")
    local failed_roles=()
    
    log "Running ${#roles[@]} roles sequentially"
    
    for role in "${roles[@]}"; do
        log "Running role: $role"
        if timeout "${TIMEOUT_MINUTES:-30}m" "$SCRIPT_DIR/multi_role_testing.sh" run "$role" full; then
            log "✅ Role $role completed successfully"
        else
            log "❌ Role $role failed"
            failed_roles+=("$role")
        fi
    done
    
    if [[ ${#failed_roles[@]} -eq 0 ]]; then
        log "🎉 All sequential testing completed successfully"
        return 0
    else
        log "💥 Failed roles: ${failed_roles[*]}"
        return 1
    fi
}

# Integration with existing workflow
integrate_with_workflow() {
    local context="$1"  # pre-commit, post-commit, manual
    local changed_files="${2:-}"
    
    if [[ -z "$changed_files" ]]; then
        changed_files=$(get_changed_files)
    fi
    
    local testing_phase=$(determine_testing_phase "$context")
    
    log "Integration context: $context, phase: $testing_phase"
    log "Changed files: $changed_files"
    
    case "$testing_phase" in
        "fast-pre-commit")
            run_fast_testing "$changed_files"
            ;;
        "comprehensive-post-commit"|"comprehensive")
            run_comprehensive_testing "$changed_files"
            ;;
        "pre-commit")
            run_comprehensive_testing "$changed_files" "smart"
            ;;
        "post-commit")
            run_comprehensive_testing "$changed_files" "full"
            ;;
        *)
            log "Unknown testing phase: $testing_phase"
            return 1
            ;;
    esac
}

# Build validation management
manage_build_validation() {
    local mode="$1"  # check, start-monitoring, stop-monitoring, full-validation
    
    case "$mode" in
        "check")
            check_build_status
            ;;
        "start-monitoring")
            start_continuous_monitoring
            ;;
        "stop-monitoring")
            stop_continuous_monitoring
            ;;
        "full-validation")
            run_full_build_validation
            ;;
        *)
            log "Unknown build validation mode: $mode"
            return 1
            ;;
    esac
}

check_build_status() {
    log "Checking build status using enhanced build validation"
    
    # Use the comprehensive build validation system
    if [[ -x "$SCRIPT_DIR/build_validation.sh" ]]; then
        # Run quick validation checks
        if "$SCRIPT_DIR/build_validation.sh" validate docker >/dev/null 2>&1; then
            log "✅ Docker build validation passed"
        else
            log "❌ Docker build validation failed"
            return 1
        fi
        
        if "$SCRIPT_DIR/build_validation.sh" validate frontend >/dev/null 2>&1; then
            log "✅ Frontend build validation passed"
        else
            log "❌ Frontend build validation failed"
            return 1
        fi
        
        if "$SCRIPT_DIR/build_validation.sh" validate backend >/dev/null 2>&1; then
            log "✅ Backend setup validation passed"
        else
            log "❌ Backend setup validation failed"
            return 1
        fi
    else
        # Fallback to basic checks
        if ! docker-compose -f docker-compose.yml config >/dev/null 2>&1; then
            log "❌ Docker compose configuration invalid"
            return 1
        fi
        
        if ! docker-compose -f docker-compose.yml build --dry-run >/dev/null 2>&1; then
            log "❌ Docker build would fail"
            return 1
        fi
    fi
    
    log "✅ Build validation passed"
    return 0
}

start_continuous_monitoring() {
    log "Starting continuous build monitoring"
    
    if [[ -x "$SCRIPT_DIR/build_validation.sh" ]]; then
        "$SCRIPT_DIR/build_validation.sh" monitor start
        log "✅ Continuous build monitoring started"
    else
        log "⚠️ Build validation system not available"
        return 1
    fi
}

stop_continuous_monitoring() {
    log "Stopping continuous build monitoring"
    
    if [[ -x "$SCRIPT_DIR/build_validation.sh" ]]; then
        "$SCRIPT_DIR/build_validation.sh" monitor stop
        log "✅ Continuous build monitoring stopped"
    else
        log "⚠️ Build validation system not available"
    fi
}

run_full_build_validation() {
    log "Running full build validation suite"
    
    if [[ -x "$SCRIPT_DIR/build_validation.sh" ]]; then
        if "$SCRIPT_DIR/build_validation.sh" validate full; then
            log "✅ Full build validation completed successfully"
            return 0
        else
            log "❌ Full build validation failed"
            return 1
        fi
    else
        log "❌ Build validation system not available"
        return 1
    fi
}

# Main execution
main() {
    local command="${1:-help}"
    shift || true
    
    load_config
    
    case "$command" in
        "integrate")
            local context="${1:-manual}"
            local changed_files="${2:-}"
            integrate_with_workflow "$context" "$changed_files"
            ;;
        "build")
            local mode="${1:-check}"
            manage_build_validation "$mode"
            ;;
        "config")
            echo "Current configuration:"
            cat "$INTEGRATION_CONFIG"
            echo
            echo "Build Validation Configuration:"
            if [[ -x "$SCRIPT_DIR/build_validation.sh" ]]; then
                "$SCRIPT_DIR/build_validation.sh" config
            else
                echo "Build validation system not available"
            fi
            ;;
        "status")
            echo "Testing Integration Status"
            echo "========================="
            echo "Mode: $TESTING_MODE"
            echo "Scope: $TESTING_SCOPE"
            echo "Build Validation: $BUILD_VALIDATION"
            echo "Documentation Management: $DOC_MANAGEMENT"
            echo
            echo "Enabled Roles:"
            [[ "$ENABLE_SENIOR_DEVELOPER" == "true" ]] && echo "  ✅ Senior Developer"
            [[ "$ENABLE_PROJECT_MANAGER" == "true" ]] && echo "  ✅ Project Manager"
            [[ "$ENABLE_QA_ENGINEER" == "true" ]] && echo "  ✅ QA Engineer"
            [[ "$ENABLE_END_USER" == "true" ]] && echo "  ✅ End User"
            [[ "$ENABLE_SECURITY_AUDITOR" == "true" ]] && echo "  ✅ Security Auditor"
            [[ "$ENABLE_UX_UI_DEVELOPER" == "true" ]] && echo "  ✅ UX/UI Developer"
            echo
            echo "Build Validation Status:"
            if [[ -x "$SCRIPT_DIR/build_validation.sh" ]]; then
                "$SCRIPT_DIR/build_validation.sh" status
            else
                echo "  Build validation system not available"
            fi
            ;;
        "help")
            cat << EOF
Testing Integration Manager

Usage: $0 <command> [options]

Commands:
    integrate <context> [changed_files]  Integrate with workflow
                                        context: pre-commit|post-commit|manual
    build <mode>                        Manage build validation
                                        mode: check|start-monitoring|stop-monitoring|full-validation
    config                              Show current configuration
    status                              Show integration status
    help                               Show this help

Examples:
    $0 integrate pre-commit "api/main.py,frontend/src/App.jsx"
    $0 integrate post-commit
    $0 build check
    $0 build full-validation
    $0 build start-monitoring
    $0 status

EOF
            ;;
        *)
            echo "Unknown command: $command"
            main help
            exit 1
            ;;
    esac
}

main "$@"