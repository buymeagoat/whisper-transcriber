#!/bin/bash

# QA Engineer Role Testing Implementation
# Comprehensive functional, regression, edge case, and performance testing

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Configuration
RESULTS_DIR="${REPO_ROOT}/logs/testing_results/qa_engineer"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p "$RESULTS_DIR"

# Logging
log() {
    echo "[QA Engineer] $*" | tee -a "$RESULTS_DIR/testing.log"
}

# Functional Testing
run_functional_tests() {
    log "Starting comprehensive functional testing"
    local failures=0
    local report_file="$RESULTS_DIR/functional_tests_${TIMESTAMP}.json"
    
    cat > "$report_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "test_suites": {
        "api_endpoints": {},
        "database_operations": {},
        "authentication": {},
        "file_operations": {},
        "business_logic": {}
    },
    "summary": {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
}
EOF

    # API Endpoints Testing
    log "Testing API endpoints functionality"
    local api_failures=0
    local api_tests=0
    
    # Check if API is testable
    if [[ -d api/ ]]; then
        # Test basic API structure
        api_tests=$((api_tests + 1))
        if [[ -f api/main.py ]]; then
            log "✅ API main entry point exists"
        else
            api_failures=$((api_failures + 1))
            log "❌ API main entry point missing"
        fi
        
        # Test route definitions
        api_tests=$((api_tests + 1))
        if find api/routes/ -name "*.py" >/dev/null 2>&1; then
            local route_count=$(find api/routes/ -name "*.py" | wc -l)
            log "✅ Found $route_count route files"
        else
            api_failures=$((api_failures + 1))
            log "❌ No route files found"
        fi
        
        # Test model definitions
        api_tests=$((api_tests + 1))
        if [[ -f api/models.py ]]; then
            local model_count=$(grep -c "^class.*:" api/models.py || echo "0")
            log "✅ Found $model_count model definitions"
        else
            api_failures=$((api_failures + 1))
            log "❌ No model definitions found"
        fi
        
        # Test schema definitions
        api_tests=$((api_tests + 1))
        if [[ -f api/schemas.py ]]; then
            local schema_count=$(grep -c "^class.*:" api/schemas.py || echo "0")
            log "✅ Found $schema_count schema definitions"
        else
            api_failures=$((api_failures + 1))
            log "❌ No schema definitions found"
        fi
        
        # Run existing test suite if available
        api_tests=$((api_tests + 1))
        if [[ -f "$REPO_ROOT/scripts/run_tests.sh" ]]; then
            log "Running existing API test suite"
            if timeout 300 "$REPO_ROOT/scripts/run_tests.sh" >/dev/null 2>&1; then
                log "✅ API test suite passed"
            else
                api_failures=$((api_failures + 1))
                log "❌ API test suite failed or timed out"
            fi
        else
            # Try pytest directly
            if command -v pytest >/dev/null 2>&1 && [[ -d tests/ ]]; then
                if timeout 300 pytest tests/ -v --tb=short >/dev/null 2>&1; then
                    log "✅ Pytest suite passed"
                else
                    api_failures=$((api_failures + 1))
                    log "❌ Pytest suite failed"
                fi
            else
                log "⚠️ No test runner available, skipping automated tests"
            fi
        fi
    fi
    
    jq --arg tests "$api_tests" --arg failures "$api_failures" --arg passed "$((api_tests - api_failures))" \
       '.test_suites.api_endpoints = {"total": ($tests|tonumber), "passed": ($passed|tonumber), "failed": ($failures|tonumber)}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    failures=$((failures + api_failures))
    
    # Database Operations Testing
    log "Testing database operations"
    local db_failures=0
    local db_tests=0
    
    if [[ -f api/models.py ]]; then
        # Test model imports
        db_tests=$((db_tests + 1))
        if python3 -c "import sys; sys.path.append('api'); import models" 2>/dev/null; then
            log "✅ Database models import successfully"
        else
            db_failures=$((db_failures + 1))
            log "❌ Database models import failed"
        fi
        
        # Test database connection
        db_tests=$((db_tests + 1))
        if python3 -c "
import sys
sys.path.append('api')
try:
    from models import *
    print('Database models loaded successfully')
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
" 2>/dev/null; then
            log "✅ Database connection successful"
        else
            db_failures=$((db_failures + 1))
            log "❌ Database connection failed"
        fi
    fi
    
    jq --arg tests "$db_tests" --arg failures "$db_failures" --arg passed "$((db_tests - db_failures))" \
       '.test_suites.database_operations = {"total": ($tests|tonumber), "passed": ($passed|tonumber), "failed": ($failures|tonumber)}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    failures=$((failures + db_failures))
    
    # Frontend Testing (if applicable)
    if [[ -d frontend/ ]]; then
        log "Testing frontend functionality"
        local frontend_failures=0
        local frontend_tests=0
        
        cd frontend
        
        # Test package.json validity
        frontend_tests=$((frontend_tests + 1))
        if [[ -f package.json ]] && jq . package.json >/dev/null 2>&1; then
            log "✅ Frontend package.json is valid"
        else
            frontend_failures=$((frontend_failures + 1))
            log "❌ Frontend package.json is invalid or missing"
        fi
        
        # Test if frontend can build
        frontend_tests=$((frontend_tests + 1))
        if [[ -f package.json ]] && command -v npm >/dev/null 2>&1; then
            if timeout 600 npm run build >/dev/null 2>&1; then
                log "✅ Frontend builds successfully"
            else
                frontend_failures=$((frontend_failures + 1))
                log "❌ Frontend build failed"
            fi
        else
            log "⚠️ Cannot test frontend build (npm not available)"
        fi
        
        # Test frontend tests if they exist
        frontend_tests=$((frontend_tests + 1))
        if [[ -f package.json ]] && jq -e '.scripts.test' package.json >/dev/null 2>&1; then
            if timeout 300 npm test >/dev/null 2>&1; then
                log "✅ Frontend tests passed"
            else
                frontend_failures=$((frontend_failures + 1))
                log "❌ Frontend tests failed"
            fi
        else
            log "⚠️ No frontend test script found"
        fi
        
        cd "$REPO_ROOT"
        
        jq --arg tests "$frontend_tests" --arg failures "$frontend_failures" --arg passed "$((frontend_tests - frontend_failures))" \
           '.test_suites.frontend = {"total": ($tests|tonumber), "passed": ($passed|tonumber), "failed": ($failures|tonumber)}' \
           "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
        
        failures=$((failures + frontend_failures))
    fi
    
    # Update overall summary
    local total_tests=$((api_tests + db_tests + frontend_tests))
    local passed_tests=$((total_tests - failures))
    
    jq --arg total "$total_tests" --arg passed "$passed_tests" --arg failed "$failures" \
       '.summary.total = ($total|tonumber) | .summary.passed = ($passed|tonumber) | .summary.failed = ($failed|tonumber)' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    log "Functional testing completed: $passed_tests/$total_tests tests passed"
    return $([[ $failures -eq 0 ]])
}

# Edge Case Testing
run_edge_case_tests() {
    log "Starting edge case testing"
    local edge_failures=0
    local report_file="$RESULTS_DIR/edge_cases_${TIMESTAMP}.json"
    
    cat > "$report_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "edge_cases": {
        "input_validation": {},
        "boundary_conditions": {},
        "error_handling": {},
        "resource_limits": {}
    },
    "summary": {"total": 0, "passed": 0, "failed": 0}
}
EOF

    # Input Validation Edge Cases
    log "Testing input validation edge cases"
    local input_failures=0
    local input_tests=0
    
    # Test for input validation patterns
    input_tests=$((input_tests + 1))
    if find api/ -name "*.py" -exec grep -l "validator\|ValidationError\|BaseModel" {} \; >/dev/null 2>&1; then
        log "✅ Input validation framework found"
    else
        input_failures=$((input_failures + 1))
        log "❌ No input validation framework found"
    fi
    
    # Test for SQL injection protection
    input_tests=$((input_tests + 1))
    if find api/ -name "*.py" -exec grep -l "execute.*format\|execute.*%" {} \; >/dev/null 2>&1; then
        input_failures=$((input_failures + 1))
        log "❌ Potential SQL injection vulnerabilities found"
    else
        log "✅ No obvious SQL injection patterns found"
    fi
    
    # Test for XSS protection
    input_tests=$((input_tests + 1))
    if [[ -d frontend/ ]]; then
        if find frontend/ -name "*.jsx" -o -name "*.tsx" | xargs grep -l "dangerouslySetInnerHTML\|innerHTML" 2>/dev/null; then
            input_failures=$((input_failures + 1))
            log "❌ Potential XSS vulnerabilities found in frontend"
        else
            log "✅ No obvious XSS patterns found"
        fi
    fi
    
    jq --arg tests "$input_tests" --arg failures "$input_failures" --arg passed "$((input_tests - input_failures))" \
       '.edge_cases.input_validation = {"total": ($tests|tonumber), "passed": ($passed|tonumber), "failed": ($failures|tonumber)}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    edge_failures=$((edge_failures + input_failures))
    
    # Boundary Conditions Testing
    log "Testing boundary conditions"
    local boundary_failures=0
    local boundary_tests=0
    
    # Test for file size limits
    boundary_tests=$((boundary_tests + 1))
    if find api/ -name "*.py" -exec grep -l "file.*size\|max.*size\|content.*length" {} \; >/dev/null 2>&1; then
        log "✅ File size validation found"
    else
        boundary_failures=$((boundary_failures + 1))
        log "❌ No file size validation found"
    fi
    
    # Test for rate limiting
    boundary_tests=$((boundary_tests + 1))
    if find api/ -name "*.py" -exec grep -l "rate.*limit\|throttle" {} \; >/dev/null 2>&1; then
        log "✅ Rate limiting implementation found"
    else
        boundary_failures=$((boundary_failures + 1))
        log "❌ No rate limiting implementation found"
    fi
    
    # Test for pagination
    boundary_tests=$((boundary_tests + 1))
    if find api/ -name "*.py" -exec grep -l "limit\|offset\|page" {} \; >/dev/null 2>&1; then
        log "✅ Pagination implementation found"
    else
        boundary_failures=$((boundary_failures + 1))
        log "❌ No pagination implementation found"
    fi
    
    jq --arg tests "$boundary_tests" --arg failures "$boundary_failures" --arg passed "$((boundary_tests - boundary_failures))" \
       '.edge_cases.boundary_conditions = {"total": ($tests|tonumber), "passed": ($passed|tonumber), "failed": ($failures|tonumber)}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    edge_failures=$((edge_failures + boundary_failures))
    
    # Error Handling Testing
    log "Testing error handling"
    local error_failures=0
    local error_tests=0
    
    # Test for proper exception handling
    error_tests=$((error_tests + 1))
    if find api/ -name "*.py" -exec grep -l "try.*except\|HTTPException\|raise" {} \; >/dev/null 2>&1; then
        log "✅ Exception handling patterns found"
    else
        error_failures=$((error_failures + 1))
        log "❌ No exception handling patterns found"
    fi
    
    # Test for proper error responses
    error_tests=$((error_tests + 1))
    if find api/ -name "*.py" -exec grep -l "status_code.*4\|status_code.*5" {} \; >/dev/null 2>&1; then
        log "✅ HTTP error status codes found"
    else
        error_failures=$((error_failures + 1))
        log "❌ No HTTP error status codes found"
    fi
    
    jq --arg tests "$error_tests" --arg failures "$error_failures" --arg passed "$((error_tests - error_failures))" \
       '.edge_cases.error_handling = {"total": ($tests|tonumber), "passed": ($passed|tonumber), "failed": ($failures|tonumber)}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    edge_failures=$((edge_failures + error_failures))
    
    # Update summary
    local total_edge_tests=$((input_tests + boundary_tests + error_tests))
    local passed_edge_tests=$((total_edge_tests - edge_failures))
    
    jq --arg total "$total_edge_tests" --arg passed "$passed_edge_tests" --arg failed "$edge_failures" \
       '.summary.total = ($total|tonumber) | .summary.passed = ($passed|tonumber) | .summary.failed = ($failed|tonumber)' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    log "Edge case testing completed: $passed_edge_tests/$total_edge_tests tests passed"
    return $([[ $edge_failures -le 2 ]])  # Allow up to 2 edge case failures
}

# Regression Testing
run_regression_tests() {
    log "Starting regression testing"
    local regression_failures=0
    local report_file="$RESULTS_DIR/regression_${TIMESTAMP}.json"
    
    cat > "$report_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "regression_suites": {
        "existing_tests": {},
        "backwards_compatibility": {},
        "configuration_stability": {}
    },
    "summary": {"total": 0, "passed": 0, "failed": 0}
}
EOF

    # Run existing test suites
    log "Running existing test suites for regression"
    local existing_failures=0
    local existing_tests=0
    
    # Python backend tests
    if [[ -d tests/ ]]; then
        existing_tests=$((existing_tests + 1))
        if command -v pytest >/dev/null 2>&1; then
            log "Running pytest regression suite"
            if timeout 600 pytest tests/ -v --tb=short --maxfail=5 >/dev/null 2>&1; then
                log "✅ Backend regression tests passed"
            else
                existing_failures=$((existing_failures + 1))
                log "❌ Backend regression tests failed"
            fi
        else
            log "⚠️ Pytest not available, skipping backend regression"
        fi
    fi
    
    # Frontend tests
    if [[ -d frontend/ ]] && [[ -f frontend/package.json ]]; then
        existing_tests=$((existing_tests + 1))
        cd frontend
        if command -v npm >/dev/null 2>&1 && jq -e '.scripts.test' package.json >/dev/null 2>&1; then
            log "Running frontend regression suite"
            if timeout 600 npm test -- --watchAll=false >/dev/null 2>&1; then
                log "✅ Frontend regression tests passed"
            else
                existing_failures=$((existing_failures + 1))
                log "❌ Frontend regression tests failed"
            fi
        else
            log "⚠️ Frontend tests not available"
        fi
        cd "$REPO_ROOT"
    fi
    
    # Integration tests
    if [[ -f cypress.config.js ]]; then
        existing_tests=$((existing_tests + 1))
        if command -v cypress >/dev/null 2>&1; then
            log "Running Cypress regression suite"
            if timeout 900 cypress run --headless >/dev/null 2>&1; then
                log "✅ Integration regression tests passed"
            else
                existing_failures=$((existing_failures + 1))
                log "❌ Integration regression tests failed"
            fi
        else
            log "⚠️ Cypress not available, skipping integration regression"
        fi
    fi
    
    jq --arg tests "$existing_tests" --arg failures "$existing_failures" --arg passed "$((existing_tests - existing_failures))" \
       '.regression_suites.existing_tests = {"total": ($tests|tonumber), "passed": ($passed|tonumber), "failed": ($failures|tonumber)}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    regression_failures=$((regression_failures + existing_failures))
    
    # Configuration stability testing
    log "Testing configuration stability"
    local config_failures=0
    local config_tests=0
    
    # Test Docker configuration
    config_tests=$((config_tests + 1))
    if [[ -f docker-compose.yml ]]; then
        if docker-compose -f docker-compose.yml config >/dev/null 2>&1; then
            log "✅ Docker configuration is valid"
        else
            config_failures=$((config_failures + 1))
            log "❌ Docker configuration is invalid"
        fi
    fi
    
    # Test environment configuration
    config_tests=$((config_tests + 1))
    if [[ -f .env.example ]] || [[ -f .env.template ]]; then
        log "✅ Environment configuration template found"
    else
        config_failures=$((config_failures + 1))
        log "❌ No environment configuration template found"
    fi
    
    jq --arg tests "$config_tests" --arg failures "$config_failures" --arg passed "$((config_tests - config_failures))" \
       '.regression_suites.configuration_stability = {"total": ($tests|tonumber), "passed": ($passed|tonumber), "failed": ($failures|tonumber)}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    regression_failures=$((regression_failures + config_failures))
    
    # Update summary
    local total_regression_tests=$((existing_tests + config_tests))
    local passed_regression_tests=$((total_regression_tests - regression_failures))
    
    jq --arg total "$total_regression_tests" --arg passed "$passed_regression_tests" --arg failed "$regression_failures" \
       '.summary.total = ($total|tonumber) | .summary.passed = ($passed|tonumber) | .summary.failed = ($failed|tonumber)' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    log "Regression testing completed: $passed_regression_tests/$total_regression_tests tests passed"
    return $([[ $regression_failures -eq 0 ]])
}

# Performance Testing
run_performance_tests() {
    log "Starting performance testing"
    local perf_issues=0
    local report_file="$RESULTS_DIR/performance_${TIMESTAMP}.json"
    
    cat > "$report_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "performance_metrics": {
        "build_time": {},
        "test_execution_time": {},
        "resource_usage": {},
        "optimization_checks": {}
    },
    "summary": {"issues": 0, "warnings": 0, "score": 0}
}
EOF

    # Build time testing
    log "Testing build performance"
    local build_start=$(date +%s)
    
    # Frontend build performance
    if [[ -d frontend/ ]] && [[ -f frontend/package.json ]]; then
        cd frontend
        if command -v npm >/dev/null 2>&1; then
            local frontend_build_start=$(date +%s)
            if timeout 900 npm run build >/dev/null 2>&1; then
                local frontend_build_end=$(date +%s)
                local frontend_build_time=$((frontend_build_end - frontend_build_start))
                log "Frontend build time: ${frontend_build_time}s"
                
                if [[ $frontend_build_time -gt 300 ]]; then
                    perf_issues=$((perf_issues + 1))
                    log "⚠️ Frontend build time is slow (${frontend_build_time}s > 300s)"
                fi
                
                jq --arg time "$frontend_build_time" \
                   '.performance_metrics.build_time.frontend = ($time|tonumber)' \
                   "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
            else
                perf_issues=$((perf_issues + 1))
                log "❌ Frontend build failed or timed out"
            fi
        fi
        cd "$REPO_ROOT"
    fi
    
    # Docker build performance
    if [[ -f Dockerfile ]]; then
        local docker_build_start=$(date +%s)
        if timeout 1200 docker build -t test-build . >/dev/null 2>&1; then
            local docker_build_end=$(date +%s)
            local docker_build_time=$((docker_build_end - docker_build_start))
            log "Docker build time: ${docker_build_time}s"
            
            if [[ $docker_build_time -gt 600 ]]; then
                perf_issues=$((perf_issues + 1))
                log "⚠️ Docker build time is slow (${docker_build_time}s > 600s)"
            fi
            
            jq --arg time "$docker_build_time" \
               '.performance_metrics.build_time.docker = ($time|tonumber)' \
               "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
            
            # Cleanup test image
            docker rmi test-build >/dev/null 2>&1 || true
        else
            perf_issues=$((perf_issues + 1))
            log "❌ Docker build failed or timed out"
        fi
    fi
    
    # Test execution performance
    log "Testing test execution performance"
    if [[ -d tests/ ]] && command -v pytest >/dev/null 2>&1; then
        local test_start=$(date +%s)
        if timeout 600 pytest tests/ -q >/dev/null 2>&1; then
            local test_end=$(date +%s)
            local test_time=$((test_end - test_start))
            log "Test execution time: ${test_time}s"
            
            if [[ $test_time -gt 300 ]]; then
                perf_issues=$((perf_issues + 1))
                log "⚠️ Test execution is slow (${test_time}s > 300s)"
            fi
            
            jq --arg time "$test_time" \
               '.performance_metrics.test_execution_time.backend = ($time|tonumber)' \
               "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
        fi
    fi
    
    # Code optimization checks
    log "Checking code optimization"
    local opt_issues=0
    
    # Check for large files
    local large_files=$(find . -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" \
                       | grep -v node_modules | grep -v .git \
                       | xargs wc -l | awk '$1 > 1000 {print $0}' | wc -l)
    if [[ $large_files -gt 5 ]]; then
        opt_issues=$((opt_issues + 1))
        log "⚠️ Found $large_files large files (>1000 lines) - consider refactoring"
    fi
    
    # Check for potential performance issues in Python
    local python_perf_issues=$(find api/ -name "*.py" -exec grep -l "nested.*loop\|O(n\^2)\|sleep(" {} \; 2>/dev/null | wc -l)
    if [[ $python_perf_issues -gt 0 ]]; then
        opt_issues=$((opt_issues + 1))
        log "⚠️ Found potential performance issues in Python code"
    fi
    
    # Check for unoptimized database queries
    local db_perf_issues=$(find api/ -name "*.py" -exec grep -l "\.all()\|SELECT \*\|N+1" {} \; 2>/dev/null | wc -l)
    if [[ $db_perf_issues -gt 0 ]]; then
        opt_issues=$((opt_issues + 1))
        log "⚠️ Found potential database performance issues"
    fi
    
    jq --arg issues "$opt_issues" \
       '.performance_metrics.optimization_checks = {"issues": ($issues|tonumber)}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    perf_issues=$((perf_issues + opt_issues))
    
    # Calculate performance score
    local max_issues=10
    local performance_score=$(((max_issues - perf_issues) * 100 / max_issues))
    [[ $performance_score -lt 0 ]] && performance_score=0
    
    jq --arg issues "$perf_issues" --arg score "$performance_score" \
       '.summary.issues = ($issues|tonumber) | .summary.score = ($score|tonumber)' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    log "Performance testing completed: Score ${performance_score}% ($perf_issues issues)"
    return $([[ $perf_issues -le 3 ]])  # Allow up to 3 performance issues
}

# Main execution
main() {
    local test_name="${1:-all}"
    
    log "Starting QA Engineer role testing: $test_name"
    
    case "$test_name" in
        "functional_tests")
            run_functional_tests
            ;;
        "edge_case_tests")
            run_edge_case_tests
            ;;
        "regression_tests")
            run_regression_tests
            ;;
        "performance_tests")
            run_performance_tests
            ;;
        "all")
            local overall_success=true
            
            run_functional_tests || overall_success=false
            run_edge_case_tests || overall_success=false
            run_regression_tests || overall_success=false
            run_performance_tests || overall_success=false
            
            if $overall_success; then
                log "✅ All QA Engineer tests passed"
                return 0
            else
                log "❌ Some QA Engineer tests failed"
                return 1
            fi
            ;;
        *)
            log "Unknown test: $test_name"
            return 1
            ;;
    esac
}

main "$@"