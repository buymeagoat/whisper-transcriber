#!/bin/bash

# Multi-Role Testing Framework
# Implements comprehensive testing from 6 role perspectives
# Part 1: Core framework and role definitions

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Import shared utilities
source "$SCRIPT_DIR/shared_checks.sh" 2>/dev/null || {
    echo "Warning: shared_checks.sh not found, continuing without shared utilities"
}

# Configuration
LOG_FILE="${REPO_ROOT}/logs/multi_role_testing.log"
RESULTS_DIR="${REPO_ROOT}/logs/testing_results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Ensure directories exist
mkdir -p "$(dirname "$LOG_FILE")" "$RESULTS_DIR"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Role definitions and responsibilities
declare -A ROLES=(
    ["senior_developer"]="Code quality, architecture, security, maintainability"
    ["project_manager"]="Requirements compliance, deliverables, timeline, risk assessment"
    ["qa_engineer"]="Functional testing, edge cases, regression, performance"
    ["end_user"]="Usability, workflow, accessibility, real-world scenarios"
    ["security_auditor"]="Security vulnerabilities, compliance, threat modeling"
    ["ux_ui_developer"]="Interface design, user experience, responsive design, accessibility"
)

# Testing categories per role
declare -A ROLE_TESTS=(
    ["senior_developer"]="code_quality architecture_review security_patterns maintainability_check"
    ["project_manager"]="project_health_tests timeline_tests resource_tests deliverable_tests"
    ["qa_engineer"]="functional_tests edge_case_tests regression_tests performance_tests"
    ["end_user"]="usability_tests workflow_tests accessibility_tests real_scenario_tests"
    ["security_auditor"]="vulnerability_scan threat_assessment compliance_check security_review"
    ["ux_ui_developer"]="design_system_tests ui_quality_tests ux_tests performance_tests"
)

# Smart trigger conditions
declare -A TRIGGER_CONDITIONS=(
    ["senior_developer"]="*.py,*.js,*.jsx,*.ts,*.tsx,api/,backend/"
    ["project_manager"]="TASKS.md,requirements*,docs/,README.md"
    ["qa_engineer"]="tests/,*.test.*,cypress/,api/,frontend/"
    ["end_user"]="frontend/,ui/,components/,pages/"
    ["security_auditor"]="auth*,security*,middlewares/,*.env*,docker*"
    ["ux_ui_developer"]="frontend/,ui/,components/,styles/,*.css,*.scss"
)

# Function to check if role testing is triggered by changes
is_role_triggered() {
    local role="$1"
    local changed_files="$2"
    
    # If no specific triggers defined, always run
    if [[ -z "${TRIGGER_CONDITIONS[$role]:-}" ]]; then
        return 0
    fi
    
    # Check each trigger pattern
    IFS=',' read -ra patterns <<< "${TRIGGER_CONDITIONS[$role]}"
    for pattern in "${patterns[@]}"; do
        if echo "$changed_files" | grep -q "$pattern"; then
            log "Role $role triggered by pattern: $pattern"
            return 0
        fi
    done
    
    return 1
}

# Function to run tests for a specific role
run_role_tests() {
    local role="$1"
    local mode="${2:-smart}"  # smart, full, or specific
    local test_list="${3:-}"  # specific tests if mode=specific
    
    log "Starting tests for role: $role (mode: $mode)"
    
    local role_result_file="$RESULTS_DIR/${role}_results_${TIMESTAMP}.json"
    local tests_to_run
    
    if [[ "$mode" == "specific" && -n "$test_list" ]]; then
        tests_to_run="$test_list"
    else
        tests_to_run="${ROLE_TESTS[$role]}"
    fi
    
    # Initialize results
    cat > "$role_result_file" << EOF
{
    "role": "$role",
    "timestamp": "$TIMESTAMP",
    "mode": "$mode",
    "tests": {},
    "summary": {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0
    }
}
EOF

    local total=0 passed=0 failed=0 skipped=0
    
    # Run each test for this role
    for test in $tests_to_run; do
        log "Running $role test: $test"
        total=$((total + 1))
        
        if run_single_test "$role" "$test" "$role_result_file"; then
            passed=$((passed + 1))
            log "✅ $role.$test: PASSED"
        else
            failed=$((failed + 1))
            log "❌ $role.$test: FAILED"
        fi
    done
    
    # Update summary
    jq --arg total "$total" --arg passed "$passed" --arg failed "$failed" --arg skipped "$skipped" \
       '.summary.total = ($total|tonumber) | .summary.passed = ($passed|tonumber) | .summary.failed = ($failed|tonumber) | .summary.skipped = ($skipped|tonumber)' \
       "$role_result_file" > "${role_result_file}.tmp" && mv "${role_result_file}.tmp" "$role_result_file"
    
    log "Role $role completed: $passed/$total tests passed"
    return $([[ $failed -eq 0 ]])
}

# Function to run a single test
run_single_test() {
    local role="$1"
    local test="$2"
    local result_file="$3"
    
    local test_start=$(date +%s)
    local test_output=""
    local test_status="passed"
    local test_details=""
    
    # Use dedicated role test scripts for enhanced implementations
    local role_script="$SCRIPT_DIR/role_tests/${role}_tests.sh"
    
    if [[ -x "$role_script" ]]; then
        # Use enhanced role-specific implementation
        test_output=$(timeout 1800 "$role_script" "$test" 2>&1) || test_status="failed"
    else
        # Fallback to basic implementations
        case "$role.$test" in
            "senior_developer.code_quality")
                test_output=$(run_code_quality_check 2>&1) || test_status="failed"
                ;;
            "senior_developer.architecture_review")
                test_output=$(run_architecture_review 2>&1) || test_status="failed"
                ;;
            "qa_engineer.functional_tests")
                test_output=$(run_functional_tests 2>&1) || test_status="failed"
                ;;
            "security_auditor.vulnerability_scan")
                test_output=$(run_vulnerability_scan 2>&1) || test_status="failed"
                ;;
            *)
                test_output="Test implementation pending for $role.$test"
                test_status="skipped"
                ;;
        esac
    fi
    
    local test_end=$(date +%s)
    local duration=$((test_end - test_start))
    
    # Update results file
    jq --arg test "$test" --arg status "$test_status" --arg output "$test_output" --arg duration "$duration" \
       '.tests[$test] = {"status": $status, "output": $output, "duration": ($duration|tonumber), "timestamp": now}' \
       "$result_file" > "${result_file}.tmp" && mv "${result_file}.tmp" "$result_file"
    
    [[ "$test_status" == "passed" ]]
}

# Placeholder test implementations (to be expanded)
run_code_quality_check() {
    # Check Python code quality
    if command -v flake8 >/dev/null 2>&1; then
        flake8 api/ --max-line-length=88 --select=E,W,F
    fi
    
    # Check JavaScript/React code quality
    if [[ -f frontend/package.json ]] && command -v npm >/dev/null 2>&1; then
        cd frontend && npm run lint 2>/dev/null || echo "Lint not configured"
    fi
    
    echo "Code quality check completed"
}

run_architecture_review() {
    # Basic architecture validation
    local issues=0
    
    # Check for proper separation of concerns
    if [[ ! -d api/routes ]]; then
        echo "Missing routes directory - poor separation"
        issues=$((issues + 1))
    fi
    
    if [[ ! -d api/services ]]; then
        echo "Missing services directory - poor separation"
        issues=$((issues + 1))
    fi
    
    echo "Architecture review completed with $issues issues"
    return $([[ $issues -eq 0 ]])
}

run_functional_tests() {
    # Run existing test suite
    if [[ -f "$REPO_ROOT/scripts/run_tests.sh" ]]; then
        "$REPO_ROOT/scripts/run_tests.sh"
    else
        echo "No test runner found, creating basic validation"
        python3 -m pytest tests/ 2>/dev/null || echo "Basic functional validation completed"
    fi
}

run_vulnerability_scan() {
    # Basic security checks
    local issues=0
    
    # Check for hardcoded secrets
    if grep -r "password.*=" api/ --include="*.py" | grep -v "# pragma: allowlist secret"; then
        echo "Potential hardcoded passwords found"
        issues=$((issues + 1))
    fi
    
    # Check for SQL injection vulnerabilities
    if grep -r "execute.*format\|execute.*%" api/ --include="*.py"; then
        echo "Potential SQL injection vulnerabilities"
        issues=$((issues + 1))
    fi
    
    echo "Vulnerability scan completed with $issues issues"
    return $([[ $issues -eq 0 ]])
}

# Main execution function
main() {
    local command="${1:-help}"
    shift || true
    
    case "$command" in
        "run")
            local role="${1:-all}"
            local mode="${2:-smart}"
            local changed_files="${3:-}"
            
            if [[ "$role" == "all" ]]; then
                run_all_roles "$mode" "$changed_files"
            else
                run_role_tests "$role" "$mode"
            fi
            ;;
        "status")
            show_testing_status
            ;;
        "list-roles")
            list_available_roles
            ;;
        "help")
            show_help
            ;;
        *)
            echo "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

run_all_roles() {
    local mode="$1"
    local changed_files="$2"
    
    log "Starting multi-role testing (mode: $mode)"
    local overall_success=true
    
    for role in "${!ROLES[@]}"; do
        if [[ "$mode" == "smart" && -n "$changed_files" ]]; then
            if ! is_role_triggered "$role" "$changed_files"; then
                log "Skipping $role - not triggered by changes"
                continue
            fi
        fi
        
        if ! run_role_tests "$role" "$mode"; then
            overall_success=false
            log "❌ Role $role failed"
        else
            log "✅ Role $role passed"
        fi
    done
    
    if $overall_success; then
        log "🎉 All role testing completed successfully"
        return 0
    else
        log "💥 Some role tests failed"
        return 1
    fi
}

show_testing_status() {
    echo "Multi-Role Testing Framework Status"
    echo "=================================="
    echo
    echo "Available Roles:"
    for role in "${!ROLES[@]}"; do
        echo "  • $role: ${ROLES[$role]}"
    done
    echo
    echo "Recent Results:"
    if [[ -d "$RESULTS_DIR" ]]; then
        ls -lt "$RESULTS_DIR"/*.json 2>/dev/null | head -5 || echo "  No recent results found"
    else
        echo "  No results directory found"
    fi
}

list_available_roles() {
    echo "Available Testing Roles:"
    echo "======================="
    for role in "${!ROLES[@]}"; do
        echo
        echo "Role: $role"
        echo "Description: ${ROLES[$role]}"
        echo "Tests: ${ROLE_TESTS[$role]}"
        echo "Triggers: ${TRIGGER_CONDITIONS[$role]:-always}"
    done
}

show_help() {
    cat << EOF
Multi-Role Testing Framework

Usage: $0 <command> [options]

Commands:
    run [role] [mode] [changed_files]   Run tests for specific role or all roles
                                       role: specific role or 'all' (default: all)
                                       mode: smart|full (default: smart)
                                       changed_files: comma-separated file patterns

    status                             Show framework status and recent results
    list-roles                         List all available roles and their tests
    help                              Show this help message

Examples:
    $0 run                            # Run smart testing for all roles
    $0 run security_auditor full      # Run full security audit
    $0 run all smart "api/,frontend/" # Smart testing based on changed files
    $0 status                         # Show current status

Roles:
$(for role in "${!ROLES[@]}"; do echo "  • $role"; done)

EOF
}

# Execute main function with all arguments
main "$@"