#!/bin/bash

# Senior Developer Role Testing Implementation
# Comprehensive code quality, architecture, security, and maintainability testing

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Configuration
RESULTS_DIR="${REPO_ROOT}/logs/testing_results/senior_developer"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p "$RESULTS_DIR"

# Logging
log() {
    echo "[Senior Developer] $*" | tee -a "$RESULTS_DIR/testing.log"
}

# Code Quality Assessment
run_code_quality_check() {
    log "Starting comprehensive code quality assessment"
    local issues=0
    local report_file="$RESULTS_DIR/code_quality_${TIMESTAMP}.json"
    
    # Initialize report
    cat > "$report_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "checks": {
        "python_quality": {},
        "javascript_quality": {},
        "type_annotations": {},
        "documentation": {},
        "complexity": {}
    },
    "summary": {"issues": 0, "warnings": 0, "passed": 0}
}
EOF

    # Python Code Quality
    log "Checking Python code quality"
    local python_issues=0
    
    if command -v flake8 >/dev/null 2>&1; then
        local flake8_output=$(flake8 api/ --max-line-length=88 --statistics --format='%(path)s:%(row)d:%(col)d: %(code)s %(text)s' 2>&1 || true)
        if [[ -n "$flake8_output" ]]; then
            python_issues=$((python_issues + $(echo "$flake8_output" | wc -l)))
            log "Flake8 issues found: $python_issues"
        fi
        
        # Update JSON report
        jq --arg output "$flake8_output" --arg count "$python_issues" \
           '.checks.python_quality.flake8 = {"issues": ($count|tonumber), "output": $output}' \
           "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    fi
    
    # Check for Python type annotations
    local type_coverage=$(find api/ -name "*.py" -exec grep -l "def \|class " {} \; | wc -l)
    local typed_files=$(find api/ -name "*.py" -exec grep -l ": \w\+\|-> \w\+" {} \; | wc -l)
    local type_percentage=$((typed_files * 100 / type_coverage))
    
    if [[ $type_percentage -lt 80 ]]; then
        issues=$((issues + 1))
        log "WARNING: Type annotation coverage is $type_percentage% (target: 80%)"
    fi
    
    jq --arg coverage "$type_percentage" \
       '.checks.type_annotations = {"coverage": ($coverage|tonumber), "target": 80}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    # JavaScript/React Code Quality
    if [[ -d frontend/ ]]; then
        log "Checking JavaScript/React code quality"
        cd frontend
        
        # ESLint check
        if [[ -f package.json ]] && command -v npm >/dev/null 2>&1; then
            local eslint_output=""
            if npm run lint >/dev/null 2>&1; then
                log "ESLint: All checks passed"
            else
                eslint_output=$(npm run lint 2>&1 || true)
                local js_issues=$(echo "$eslint_output" | grep -c "error\|warning" || echo "0")
                issues=$((issues + js_issues))
                log "ESLint issues found: $js_issues"
            fi
            
            jq --arg output "$eslint_output" \
               '.checks.javascript_quality.eslint = {"output": $output}' \
               "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
        fi
        
        cd "$REPO_ROOT"
    fi
    
    # Check documentation coverage
    local total_functions=$(find api/ -name "*.py" -exec grep -c "^def \|^class " {} \; | awk '{sum+=$1} END {print sum}')
    local documented_functions=$(find api/ -name "*.py" -exec grep -A1 "^def \|^class " {} \; | grep -c '"""' || echo "0")
    local doc_percentage=$((documented_functions * 100 / total_functions))
    
    if [[ $doc_percentage -lt 60 ]]; then
        issues=$((issues + 1))
        log "WARNING: Documentation coverage is $doc_percentage% (target: 60%)"
    fi
    
    jq --arg coverage "$doc_percentage" \
       '.checks.documentation = {"coverage": ($coverage|tonumber), "target": 60}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    # Complexity analysis
    if command -v radon >/dev/null 2>&1; then
        local complexity_output=$(radon cc api/ -a 2>&1 || echo "radon not available")
        jq --arg output "$complexity_output" \
           '.checks.complexity = {"output": $output}' \
           "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    fi
    
    # Update summary
    jq --arg issues "$issues" \
       '.summary.issues = ($issues|tonumber)' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    log "Code quality assessment completed with $issues issues"
    return $([[ $issues -eq 0 ]])
}

# Architecture Review
run_architecture_review() {
    log "Starting architecture review"
    local issues=0
    local report_file="$RESULTS_DIR/architecture_${TIMESTAMP}.json"
    
    cat > "$report_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "checks": {
        "separation_of_concerns": {},
        "dependency_management": {},
        "api_design": {},
        "database_design": {},
        "frontend_architecture": {}
    },
    "summary": {"issues": 0, "warnings": 0}
}
EOF

    # Check separation of concerns
    log "Checking separation of concerns"
    local soc_issues=0
    
    # Check for proper directory structure
    local required_dirs=("api/routes" "api/services" "api/models" "api/schemas")
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            soc_issues=$((soc_issues + 1))
            log "ISSUE: Missing directory $dir - poor separation of concerns"
        fi
    done
    
    # Check for business logic in routes
    if find api/routes/ -name "*.py" -exec grep -l "SELECT\|INSERT\|UPDATE\|DELETE" {} \; 2>/dev/null | head -1; then
        soc_issues=$((soc_issues + 1))
        log "ISSUE: Database queries found in routes - should be in services"
    fi
    
    jq --arg issues "$soc_issues" \
       '.checks.separation_of_concerns = {"issues": ($issues|tonumber)}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    issues=$((issues + soc_issues))
    
    # Check API design patterns
    log "Checking API design patterns"
    local api_issues=0
    
    # Check for RESTful patterns
    if ! find api/routes/ -name "*.py" -exec grep -l "GET\|POST\|PUT\|DELETE" {} \; >/dev/null 2>&1; then
        api_issues=$((api_issues + 1))
        log "WARNING: No HTTP methods found in routes - check API implementation"
    fi
    
    # Check for proper error handling
    if ! find api/ -name "*.py" -exec grep -l "HTTPException\|raise" {} \; >/dev/null 2>&1; then
        api_issues=$((api_issues + 1))
        log "WARNING: Limited error handling patterns found"
    fi
    
    jq --arg issues "$api_issues" \
       '.checks.api_design = {"issues": ($issues|tonumber)}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    issues=$((issues + api_issues))
    
    # Check database design
    log "Checking database design"
    local db_issues=0
    
    if [[ -f api/models.py ]]; then
        # Check for proper relationships
        if ! grep -q "relationship\|ForeignKey" api/models.py; then
            db_issues=$((db_issues + 1))
            log "WARNING: No relationships found in models - check database design"
        fi
        
        # Check for indexes
        if ! grep -q "index=True\|Index" api/models.py; then
            db_issues=$((db_issues + 1))
            log "WARNING: No database indexes found - performance concern"
        fi
    fi
    
    jq --arg issues "$db_issues" \
       '.checks.database_design = {"issues": ($issues|tonumber)}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    issues=$((issues + db_issues))
    
    # Check frontend architecture
    if [[ -d frontend/src ]]; then
        log "Checking frontend architecture"
        local frontend_issues=0
        
        # Check for proper component structure
        if [[ ! -d frontend/src/components ]]; then
            frontend_issues=$((frontend_issues + 1))
            log "ISSUE: Missing components directory"
        fi
        
        # Check for state management
        if ! find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "useState\|useContext\|useReducer" >/dev/null 2>&1; then
            frontend_issues=$((frontend_issues + 1))
            log "WARNING: No state management patterns found"
        fi
        
        jq --arg issues "$frontend_issues" \
           '.checks.frontend_architecture = {"issues": ($issues|tonumber)}' \
           "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
        
        issues=$((issues + frontend_issues))
    fi
    
    # Update summary
    jq --arg issues "$issues" \
       '.summary.issues = ($issues|tonumber)' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    log "Architecture review completed with $issues issues"
    return $([[ $issues -eq 0 ]])
}

# Security Patterns Review
run_security_patterns_check() {
    log "Starting security patterns review"
    local issues=0
    local report_file="$RESULTS_DIR/security_patterns_${TIMESTAMP}.json"
    
    cat > "$report_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "checks": {
        "authentication": {},
        "authorization": {},
        "input_validation": {},
        "secure_headers": {},
        "dependency_security": {}
    },
    "summary": {"issues": 0, "critical": 0}
}
EOF

    # Check authentication implementation
    log "Checking authentication patterns"
    local auth_issues=0
    
    # Check for proper password hashing
    if find api/ -name "*.py" -exec grep -l "password" {} \; | xargs grep -l "bcrypt\|scrypt\|argon2" >/dev/null 2>&1; then
        log "GOOD: Secure password hashing found"
    else
        auth_issues=$((auth_issues + 1))
        log "CRITICAL: No secure password hashing patterns found"
    fi
    
    # Check for JWT implementation
    if find api/ -name "*.py" -exec grep -l "jwt\|token" {} \; >/dev/null 2>&1; then
        log "Found JWT/token implementation"
        
        # Check for proper JWT validation
        if ! find api/ -name "*.py" -exec grep -l "verify\|decode.*jwt" {} \; >/dev/null 2>&1; then
            auth_issues=$((auth_issues + 1))
            log "WARNING: JWT tokens found but no validation patterns"
        fi
    fi
    
    jq --arg issues "$auth_issues" \
       '.checks.authentication = {"issues": ($issues|tonumber)}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    issues=$((issues + auth_issues))
    
    # Check input validation
    log "Checking input validation patterns"
    local validation_issues=0
    
    # Check for Pydantic models
    if find api/ -name "*.py" -exec grep -l "BaseModel\|validator" {} \; >/dev/null 2>&1; then
        log "GOOD: Pydantic validation found"
    else
        validation_issues=$((validation_issues + 1))
        log "WARNING: No input validation patterns found"
    fi
    
    # Check for SQL injection prevention
    if find api/ -name "*.py" -exec grep -l "execute.*format\|execute.*%" {} \; >/dev/null 2>&1; then
        validation_issues=$((validation_issues + 1))
        log "CRITICAL: Potential SQL injection patterns found"
    fi
    
    jq --arg issues "$validation_issues" \
       '.checks.input_validation = {"issues": ($issues|tonumber)}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    issues=$((issues + validation_issues))
    
    # Check security headers
    log "Checking security headers implementation"
    local header_issues=0
    
    if find api/ -name "*.py" -exec grep -l "CSP\|Content-Security-Policy\|X-Frame-Options" {} \; >/dev/null 2>&1; then
        log "GOOD: Security headers implementation found"
    else
        header_issues=$((header_issues + 1))
        log "WARNING: No security headers implementation found"
    fi
    
    jq --arg issues "$header_issues" \
       '.checks.secure_headers = {"issues": ($issues|tonumber)}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    issues=$((issues + header_issues))
    
    # Update summary
    local critical_issues=$(jq -r '[.checks[].issues // 0] | add' "$report_file")
    jq --arg issues "$issues" --arg critical "$critical_issues" \
       '.summary.issues = ($issues|tonumber) | .summary.critical = ($critical|tonumber)' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    log "Security patterns review completed with $issues issues"
    return $([[ $issues -eq 0 ]])
}

# Maintainability Assessment
run_maintainability_check() {
    log "Starting maintainability assessment"
    local issues=0
    local report_file="$RESULTS_DIR/maintainability_${TIMESTAMP}.json"
    
    cat > "$report_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "checks": {
        "code_duplication": {},
        "function_length": {},
        "test_coverage": {},
        "configuration_management": {},
        "dependency_updates": {}
    },
    "summary": {"issues": 0, "score": 0}
}
EOF

    # Check for code duplication
    log "Checking code duplication"
    local duplication_issues=0
    
    # Simple duplication check using repeated patterns
    local duplicate_lines=$(find api/ -name "*.py" -exec cat {} \; | sort | uniq -d | wc -l)
    if [[ $duplicate_lines -gt 100 ]]; then
        duplication_issues=$((duplication_issues + 1))
        log "WARNING: High code duplication detected ($duplicate_lines duplicate lines)"
    fi
    
    jq --arg lines "$duplicate_lines" --arg issues "$duplication_issues" \
       '.checks.code_duplication = {"duplicate_lines": ($lines|tonumber), "issues": ($issues|tonumber)}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    issues=$((issues + duplication_issues))
    
    # Check function length
    log "Checking function length"
    local length_issues=0
    
    # Find long functions (>50 lines)
    local long_functions=$(find api/ -name "*.py" -exec awk '/^def / {start=NR; name=$0} /^$/ && start {if(NR-start > 50) print FILENAME":"start":"name}' {} \; | wc -l)
    if [[ $long_functions -gt 0 ]]; then
        length_issues=$((length_issues + 1))
        log "WARNING: Found $long_functions functions longer than 50 lines"
    fi
    
    jq --arg count "$long_functions" --arg issues "$length_issues" \
       '.checks.function_length = {"long_functions": ($count|tonumber), "issues": ($issues|tonumber)}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    issues=$((issues + length_issues))
    
    # Check test coverage
    log "Checking test coverage"
    local coverage_issues=0
    
    local test_files=$(find tests/ -name "*.py" | wc -l)
    local source_files=$(find api/ -name "*.py" | wc -l)
    local coverage_ratio=$((test_files * 100 / source_files))
    
    if [[ $coverage_ratio -lt 50 ]]; then
        coverage_issues=$((coverage_issues + 1))
        log "WARNING: Test coverage ratio is $coverage_ratio% (target: 50%)"
    fi
    
    jq --arg ratio "$coverage_ratio" --arg issues "$coverage_issues" \
       '.checks.test_coverage = {"ratio": ($ratio|tonumber), "issues": ($issues|tonumber)}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    issues=$((issues + coverage_issues))
    
    # Check configuration management
    log "Checking configuration management"
    local config_issues=0
    
    # Check for hardcoded values
    local hardcoded_count=$(find api/ -name "*.py" -exec grep -c "localhost\|127\.0\.0\.1\|password.*=" {} \; | awk '{sum+=$1} END {print sum}')
    if [[ $hardcoded_count -gt 5 ]]; then
        config_issues=$((config_issues + 1))
        log "WARNING: Found $hardcoded_count potential hardcoded configuration values"
    fi
    
    jq --arg count "$hardcoded_count" --arg issues "$config_issues" \
       '.checks.configuration_management = {"hardcoded_values": ($count|tonumber), "issues": ($issues|tonumber)}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    issues=$((issues + config_issues))
    
    # Calculate maintainability score
    local total_checks=4
    local passed_checks=$((total_checks - issues))
    local score=$((passed_checks * 100 / total_checks))
    
    jq --arg issues "$issues" --arg score "$score" \
       '.summary.issues = ($issues|tonumber) | .summary.score = ($score|tonumber)' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    log "Maintainability assessment completed with score: $score% ($issues issues)"
    return $([[ $issues -le 2 ]])  # Allow up to 2 minor issues
}

# Main execution
main() {
    local test_name="${1:-all}"
    
    log "Starting Senior Developer role testing: $test_name"
    
    case "$test_name" in
        "code_quality")
            run_code_quality_check
            ;;
        "architecture_review")
            run_architecture_review
            ;;
        "security_patterns")
            run_security_patterns_check
            ;;
        "maintainability_check")
            run_maintainability_check
            ;;
        "all")
            local overall_success=true
            
            run_code_quality_check || overall_success=false
            run_architecture_review || overall_success=false
            run_security_patterns_check || overall_success=false
            run_maintainability_check || overall_success=false
            
            if $overall_success; then
                log "✅ All Senior Developer tests passed"
                return 0
            else
                log "❌ Some Senior Developer tests failed"
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