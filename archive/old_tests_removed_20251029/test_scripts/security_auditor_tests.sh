#!/bin/bash

# Security Auditor Role Testing Implementation
# Comprehensive security vulnerability assessment and compliance checking

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Configuration
RESULTS_DIR="${REPO_ROOT}/logs/testing_results/security_auditor"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p "$RESULTS_DIR"

# Logging
log() {
    echo "[Security Auditor] $*" | tee -a "$RESULTS_DIR/testing.log"
}

# Vulnerability Scanning
run_vulnerability_scan() {
    log "Starting comprehensive vulnerability scan"
    local critical_issues=0
    local high_issues=0
    local medium_issues=0
    local report_file="$RESULTS_DIR/vulnerability_scan_${TIMESTAMP}.json"
    
    cat > "$report_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "scan_type": "comprehensive_vulnerability_scan",
    "vulnerabilities": {
        "hardcoded_secrets": [],
        "sql_injection": [],
        "xss_vulnerabilities": [],
        "authentication_flaws": [],
        "authorization_bypasses": [],
        "dependency_vulnerabilities": []
    },
    "summary": {"critical": 0, "high": 0, "medium": 0, "low": 0}
}
EOF

    # Scan for hardcoded secrets
    log "Scanning for hardcoded secrets and credentials"
    local secret_patterns=(
        "password\s*=\s*['\"][^'\"]{8,}['\"]"
        "api_key\s*=\s*['\"][^'\"]+['\"]"
        "secret\s*=\s*['\"][^'\"]+['\"]"
        "token\s*=\s*['\"][^'\"]{20,}['\"]"
        "-----BEGIN.*PRIVATE.*KEY-----"
        "AKIA[0-9A-Z]{16}"  # AWS Access Key
        "sk_live_[0-9a-zA-Z]{24}"  # Stripe Live Key
    )
    
    local secret_findings=()
    for pattern in "${secret_patterns[@]}"; do
        while IFS= read -r finding; do
            if [[ -n "$finding" ]]; then
                critical_issues=$((critical_issues + 1))
                secret_findings+=("$finding")
                log "CRITICAL: Potential hardcoded secret found: $finding"
            fi
        done < <(find . -type f -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" \
                 | grep -v node_modules | grep -v .git \
                 | xargs grep -Hn "$pattern" 2>/dev/null || true)
    done
    
    # Update JSON with secret findings
    local secrets_json=$(printf '%s\n' "${secret_findings[@]}" | jq -R . | jq -s .)
    jq --argjson secrets "$secrets_json" \
       '.vulnerabilities.hardcoded_secrets = $secrets' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    # SQL Injection vulnerability scan
    log "Scanning for SQL injection vulnerabilities"
    local sql_patterns=(
        "execute.*format"
        "execute.*%"
        "query.*format"
        "cursor\.execute.*%"
        "SELECT.*\+.*"
        "INSERT.*\+.*"
        "UPDATE.*\+.*"
        "DELETE.*\+.*"
    )
    
    local sql_findings=()
    for pattern in "${sql_patterns[@]}"; do
        while IFS= read -r finding; do
            if [[ -n "$finding" ]]; then
                high_issues=$((high_issues + 1))
                sql_findings+=("$finding")
                log "HIGH: Potential SQL injection vulnerability: $finding"
            fi
        done < <(find api/ -name "*.py" | xargs grep -Hn "$pattern" 2>/dev/null || true)
    done
    
    local sql_json=$(printf '%s\n' "${sql_findings[@]}" | jq -R . | jq -s .)
    jq --argjson sql "$sql_json" \
       '.vulnerabilities.sql_injection = $sql' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    # XSS vulnerability scan
    log "Scanning for XSS vulnerabilities"
    local xss_patterns=(
        "innerHTML.*\+"
        "outerHTML.*\+"
        "document\.write\("
        "eval\("
        "dangerouslySetInnerHTML"
        "v-html"
    )
    
    local xss_findings=()
    for pattern in "${xss_patterns[@]}"; do
        while IFS= read -r finding; do
            if [[ -n "$finding" ]]; then
                high_issues=$((high_issues + 1))
                xss_findings+=("$finding")
                log "HIGH: Potential XSS vulnerability: $finding"
            fi
        done < <(find frontend/ -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" \
                 2>/dev/null | xargs grep -Hn "$pattern" 2>/dev/null || true)
    done
    
    local xss_json=$(printf '%s\n' "${xss_findings[@]}" | jq -R . | jq -s .)
    jq --argjson xss "$xss_json" \
       '.vulnerabilities.xss_vulnerabilities = $xss' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    # Authentication security scan
    log "Scanning authentication implementation"
    local auth_issues=0
    local auth_findings=()
    
    # Check for weak password requirements
    if find api/ -name "*.py" -exec grep -l "password" {} \; | xargs grep -v "bcrypt\|scrypt\|argon2\|PBKDF2" | grep -q "password"; then
        auth_issues=$((auth_issues + 1))
        auth_findings+=("Weak password hashing detected")
        log "HIGH: Weak password hashing implementation"
    fi
    
    # Check for missing JWT signature verification
    if find api/ -name "*.py" -exec grep -l "jwt\|token" {} \; >/dev/null 2>&1; then
        if ! find api/ -name "*.py" -exec grep -l "verify_signature.*True\|decode.*verify" {} \; >/dev/null 2>&1; then
            auth_issues=$((auth_issues + 1))
            auth_findings+=("JWT signature verification not enforced")
            log "CRITICAL: JWT signature verification not properly enforced"
            critical_issues=$((critical_issues + 1))
        fi
    fi
    
    # Check for session management issues
    if find api/ -name "*.py" -exec grep -l "session" {} \; >/dev/null 2>&1; then
        if ! find api/ -name "*.py" -exec grep -l "session.*timeout\|session.*expire" {} \; >/dev/null 2>&1; then
            auth_issues=$((auth_issues + 1))
            auth_findings+=("No session timeout implementation found")
            log "MEDIUM: No session timeout implementation found"
            medium_issues=$((medium_issues + 1))
        fi
    fi
    
    local auth_json=$(printf '%s\n' "${auth_findings[@]}" | jq -R . | jq -s .)
    jq --argjson auth "$auth_json" \
       '.vulnerabilities.authentication_flaws = $auth' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    # Dependency vulnerability scan
    log "Scanning dependencies for known vulnerabilities"
    local dep_findings=()
    
    # Check Python dependencies
    if [[ -f requirements.txt ]] && command -v safety >/dev/null 2>&1; then
        local safety_output=$(safety check --json 2>/dev/null || echo "[]")
        local vuln_count=$(echo "$safety_output" | jq length)
        if [[ $vuln_count -gt 0 ]]; then
            dep_findings+=("Python dependencies: $vuln_count vulnerabilities found")
            high_issues=$((high_issues + vuln_count))
            log "HIGH: $vuln_count vulnerabilities found in Python dependencies"
        fi
    fi
    
    # Check Node.js dependencies
    if [[ -f frontend/package.json ]] && command -v npm >/dev/null 2>&1; then
        cd frontend
        local npm_audit=$(npm audit --json 2>/dev/null || echo '{"vulnerabilities":{}}')
        local npm_vuln_count=$(echo "$npm_audit" | jq '.metadata.vulnerabilities.total // 0')
        if [[ $npm_vuln_count -gt 0 ]]; then
            dep_findings+=("Node.js dependencies: $npm_vuln_count vulnerabilities found")
            high_issues=$((high_issues + npm_vuln_count))
            log "HIGH: $npm_vuln_count vulnerabilities found in Node.js dependencies"
        fi
        cd "$REPO_ROOT"
    fi
    
    local dep_json=$(printf '%s\n' "${dep_findings[@]}" | jq -R . | jq -s .)
    jq --argjson deps "$dep_json" \
       '.vulnerabilities.dependency_vulnerabilities = $deps' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    # Update summary
    jq --arg critical "$critical_issues" --arg high "$high_issues" --arg medium "$medium_issues" \
       '.summary.critical = ($critical|tonumber) | .summary.high = ($high|tonumber) | .summary.medium = ($medium|tonumber)' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    local total_issues=$((critical_issues + high_issues + medium_issues))
    log "Vulnerability scan completed: $critical_issues critical, $high_issues high, $medium_issues medium issues"
    
    # Return failure if critical or high issues found
    return $([[ $critical_issues -eq 0 && $high_issues -eq 0 ]])
}

# Threat Assessment
run_threat_assessment() {
    log "Starting threat assessment"
    local threats=0
    local report_file="$RESULTS_DIR/threat_assessment_${TIMESTAMP}.json"
    
    cat > "$report_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "threat_model": {
        "attack_vectors": [],
        "security_controls": [],
        "risk_assessment": {},
        "mitigation_recommendations": []
    },
    "summary": {"high_risk": 0, "medium_risk": 0, "low_risk": 0}
}
EOF

    log "Analyzing attack vectors"
    local attack_vectors=()
    local high_risk=0
    local medium_risk=0
    
    # Check for common attack vectors
    
    # 1. Authentication bypass
    if ! find api/ -name "*.py" -exec grep -l "authenticate\|verify.*user" {} \; >/dev/null 2>&1; then
        attack_vectors+=("Missing authentication mechanisms")
        high_risk=$((high_risk + 1))
        log "HIGH RISK: No authentication mechanisms found"
    fi
    
    # 2. Authorization bypass
    if ! find api/ -name "*.py" -exec grep -l "authorize\|permission\|role" {} \; >/dev/null 2>&1; then
        attack_vectors+=("Missing authorization controls")
        high_risk=$((high_risk + 1))
        log "HIGH RISK: No authorization controls found"
    fi
    
    # 3. CSRF vulnerability
    if find api/ -name "*.py" -exec grep -l "POST\|PUT\|DELETE" {} \; >/dev/null 2>&1; then
        if ! find api/ -name "*.py" -exec grep -l "csrf\|CSRFProtect" {} \; >/dev/null 2>&1; then
            attack_vectors+=("Potential CSRF vulnerability")
            medium_risk=$((medium_risk + 1))
            log "MEDIUM RISK: No CSRF protection found for state-changing operations"
        fi
    fi
    
    # 4. Insecure direct object references
    if find api/ -name "*.py" -exec grep -l "id.*request\|request.*id" {} \; >/dev/null 2>&1; then
        if ! find api/ -name "*.py" -exec grep -l "owner\|user.*id.*check" {} \; >/dev/null 2>&1; then
            attack_vectors+=("Potential insecure direct object references")
            medium_risk=$((medium_risk + 1))
            log "MEDIUM RISK: Object access controls may be insufficient"
        fi
    fi
    
    # 5. Information disclosure
    if find api/ -name "*.py" -exec grep -l "debug.*True\|DEBUG.*True" {} \; >/dev/null 2>&1; then
        attack_vectors+=("Debug mode enabled - information disclosure risk")
        medium_risk=$((medium_risk + 1))
        log "MEDIUM RISK: Debug mode may be enabled in production"
    fi
    
    # Analyze security controls
    log "Analyzing existing security controls"
    local security_controls=()
    
    # Check for security headers
    if find api/ -name "*.py" -exec grep -l "X-Frame-Options\|Content-Security-Policy\|X-Content-Type-Options" {} \; >/dev/null 2>&1; then
        security_controls+=("Security headers implementation found")
        log "GOOD: Security headers implementation detected"
    else
        attack_vectors+=("Missing security headers")
        medium_risk=$((medium_risk + 1))
        log "MEDIUM RISK: No security headers implementation found"
    fi
    
    # Check for rate limiting
    if find api/ -name "*.py" -exec grep -l "rate.*limit\|throttle" {} \; >/dev/null 2>&1; then
        security_controls+=("Rate limiting implementation found")
        log "GOOD: Rate limiting detected"
    else
        attack_vectors+=("No rate limiting - DoS vulnerability")
        medium_risk=$((medium_risk + 1))
        log "MEDIUM RISK: No rate limiting implementation found"
    fi
    
    # Check for input validation
    if find api/ -name "*.py" -exec grep -l "validator\|ValidationError\|BaseModel" {} \; >/dev/null 2>&1; then
        security_controls+=("Input validation framework found")
        log "GOOD: Input validation framework detected"
    else
        attack_vectors+=("Insufficient input validation")
        high_risk=$((high_risk + 1))
        log "HIGH RISK: No input validation framework found"
    fi
    
    # Check for logging and monitoring
    if find api/ -name "*.py" -exec grep -l "logger\|log\." {} \; >/dev/null 2>&1; then
        security_controls+=("Logging implementation found")
        log "GOOD: Logging implementation detected"
    else
        attack_vectors+=("Insufficient security logging")
        medium_risk=$((medium_risk + 1))
        log "MEDIUM RISK: No security logging implementation found"
    fi
    
    # Generate risk assessment
    local total_risks=$((high_risk + medium_risk))
    local risk_level="LOW"
    if [[ $high_risk -gt 0 ]]; then
        risk_level="HIGH"
    elif [[ $medium_risk -gt 2 ]]; then
        risk_level="MEDIUM"
    fi
    
    # Update JSON report
    local vectors_json=$(printf '%s\n' "${attack_vectors[@]}" | jq -R . | jq -s .)
    local controls_json=$(printf '%s\n' "${security_controls[@]}" | jq -R . | jq -s .)
    
    jq --argjson vectors "$vectors_json" --argjson controls "$controls_json" \
       --arg risk_level "$risk_level" --arg high "$high_risk" --arg medium "$medium_risk" \
       '.threat_model.attack_vectors = $vectors |
        .threat_model.security_controls = $controls |
        .threat_model.risk_assessment = {"level": $risk_level, "high_risk_items": ($high|tonumber), "medium_risk_items": ($medium|tonumber)} |
        .summary.high_risk = ($high|tonumber) |
        .summary.medium_risk = ($medium|tonumber)' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    threats=$total_risks
    log "Threat assessment completed: $risk_level risk level ($high_risk high, $medium_risk medium risks)"
    
    return $([[ $high_risk -eq 0 ]])
}

# Compliance Check
run_compliance_check() {
    log "Starting security compliance check"
    local violations=0
    local report_file="$RESULTS_DIR/compliance_${TIMESTAMP}.json"
    
    cat > "$report_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "standards": {
        "owasp_top_10": {},
        "security_headers": {},
        "data_protection": {},
        "access_controls": {}
    },
    "summary": {"violations": 0, "warnings": 0, "compliance_score": 0}
}
EOF

    # OWASP Top 10 compliance check
    log "Checking OWASP Top 10 compliance"
    local owasp_violations=0
    
    # A01:2021 – Broken Access Control
    if ! find api/ -name "*.py" -exec grep -l "authorize\|permission\|@requires" {} \; >/dev/null 2>&1; then
        owasp_violations=$((owasp_violations + 1))
        log "VIOLATION: A01 - No access control implementation found"
    fi
    
    # A02:2021 – Cryptographic Failures
    if ! find api/ -name "*.py" -exec grep -l "bcrypt\|scrypt\|argon2\|hashlib" {} \; >/dev/null 2>&1; then
        owasp_violations=$((owasp_violations + 1))
        log "VIOLATION: A02 - No strong cryptographic implementation found"
    fi
    
    # A03:2021 – Injection
    if find api/ -name "*.py" -exec grep -l "execute.*format\|execute.*%" {} \; >/dev/null 2>&1; then
        owasp_violations=$((owasp_violations + 1))
        log "VIOLATION: A03 - SQL injection vulnerabilities detected"
    fi
    
    # A05:2021 – Security Misconfiguration
    if find . -name "*.env*" -exec grep -l "DEBUG.*True\|debug.*true" {} \; >/dev/null 2>&1; then
        owasp_violations=$((owasp_violations + 1))
        log "VIOLATION: A05 - Debug mode enabled in configuration"
    fi
    
    # A06:2021 – Vulnerable and Outdated Components
    if [[ -f requirements.txt ]]; then
        local old_packages=$(grep -c "==" requirements.txt || echo "0")
        if [[ $old_packages -gt 5 ]]; then
            owasp_violations=$((owasp_violations + 1))
            log "WARNING: A06 - Many pinned dependencies may be outdated"
        fi
    fi
    
    jq --arg violations "$owasp_violations" \
       '.standards.owasp_top_10 = {"violations": ($violations|tonumber)}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    violations=$((violations + owasp_violations))
    
    # Security headers compliance
    log "Checking security headers compliance"
    local header_violations=0
    
    local required_headers=(
        "Content-Security-Policy"
        "X-Frame-Options"
        "X-Content-Type-Options"
        "Strict-Transport-Security"
        "Referrer-Policy"
    )
    
    for header in "${required_headers[@]}"; do
        if ! find api/ -name "*.py" -exec grep -l "$header" {} \; >/dev/null 2>&1; then
            header_violations=$((header_violations + 1))
            log "VIOLATION: Missing security header: $header"
        fi
    done
    
    jq --arg violations "$header_violations" \
       '.standards.security_headers = {"violations": ($violations|tonumber)}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    violations=$((violations + header_violations))
    
    # Data protection compliance
    log "Checking data protection compliance"
    local data_violations=0
    
    # Check for data encryption
    if find api/ -name "*.py" -exec grep -l "password\|token\|secret" {} \; >/dev/null 2>&1; then
        if ! find api/ -name "*.py" -exec grep -l "encrypt\|cipher\|crypto" {} \; >/dev/null 2>&1; then
            data_violations=$((data_violations + 1))
            log "VIOLATION: Sensitive data handling without encryption"
        fi
    fi
    
    # Check for data retention policies
    if ! find api/ -name "*.py" -exec grep -l "retention\|expire\|cleanup" {} \; >/dev/null 2>&1; then
        data_violations=$((data_violations + 1))
        log "WARNING: No data retention policies found"
    fi
    
    jq --arg violations "$data_violations" \
       '.standards.data_protection = {"violations": ($violations|tonumber)}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    violations=$((violations + data_violations))
    
    # Calculate compliance score
    local total_checks=15  # Approximate total compliance checks
    local passed_checks=$((total_checks - violations))
    local compliance_score=$((passed_checks * 100 / total_checks))
    
    jq --arg violations "$violations" --arg score "$compliance_score" \
       '.summary.violations = ($violations|tonumber) | .summary.compliance_score = ($score|tonumber)' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    log "Compliance check completed: $compliance_score% compliance score ($violations violations)"
    
    return $([[ $violations -le 3 ]])  # Allow up to 3 minor violations
}

# Security Review Summary
run_security_review() {
    log "Starting comprehensive security review"
    local overall_success=true
    
    # Run all security tests
    run_vulnerability_scan || overall_success=false
    run_threat_assessment || overall_success=false
    run_compliance_check || overall_success=false
    
    # Generate comprehensive security report
    local summary_file="$RESULTS_DIR/security_summary_${TIMESTAMP}.json"
    
    cat > "$summary_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "overall_status": "$(if $overall_success; then echo "PASSED"; else echo "FAILED"; fi)",
    "recommendations": [
        "Implement strong authentication and authorization controls",
        "Add comprehensive input validation",
        "Implement security headers",
        "Add rate limiting to prevent DoS attacks",
        "Regular dependency updates and vulnerability scanning",
        "Implement comprehensive security logging",
        "Add CSRF protection for state-changing operations",
        "Ensure proper session management with timeouts",
        "Implement data encryption for sensitive information",
        "Regular security assessments and penetration testing"
    ]
}
EOF

    if $overall_success; then
        log "✅ Security review passed - application meets security standards"
        return 0
    else
        log "❌ Security review failed - critical security issues found"
        return 1
    fi
}

# Main execution
main() {
    local test_name="${1:-all}"
    
    log "Starting Security Auditor role testing: $test_name"
    
    case "$test_name" in
        "vulnerability_scan")
            run_vulnerability_scan
            ;;
        "threat_assessment")
            run_threat_assessment
            ;;
        "compliance_check")
            run_compliance_check
            ;;
        "security_review")
            run_security_review
            ;;
        "all")
            run_security_review
            ;;
        *)
            log "Unknown test: $test_name"
            return 1
            ;;
    esac
}

main "$@"