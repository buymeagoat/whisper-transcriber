#!/bin/bash

# Project Manager Role Testing Implementation
# Comprehensive project health, timeline, resource, and deliverable assessment

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Configuration
RESULTS_DIR="${REPO_ROOT}/logs/testing_results/project_manager"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p "$RESULTS_DIR"

# Logging
log() {
    echo "[Project Manager] $*" | tee -a "$RESULTS_DIR/testing.log"
}

# Project health assessment
run_project_health_tests() {
    log "Starting project health assessment"
    local health_issues=0
    local report_file="$RESULTS_DIR/project_health_${TIMESTAMP}.json"
    
    cat > "$report_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "test_type": "project_health_assessment",
    "metrics": {
        "code_metrics": {},
        "dependency_health": {},
        "documentation_coverage": {},
        "test_coverage": {},
        "build_stability": {}
    },
    "summary": {"issues": 0, "health_score": 0}
}
EOF

    # Code metrics analysis
    log "Analyzing code metrics"
    local code_issues=0
    local code_metrics=()
    
    # Lines of code analysis
    local total_lines=0
    local code_lines=0
    local comment_lines=0
    
    if [[ -d api ]]; then
        local api_lines=$(find api -name "*.py" -exec wc -l {} + | tail -1 | awk '{print $1}' || echo "0")
        total_lines=$((total_lines + api_lines))
        code_lines=$((code_lines + api_lines))
        code_metrics+=("Backend: $api_lines lines of Python code")
        log "Backend: $api_lines lines of Python code"
    fi
    
    if [[ -d frontend/src ]]; then
        local frontend_lines=$(find frontend/src -name "*.jsx" -o -name "*.tsx" -o -name "*.js" -o -name "*.ts" -exec wc -l {} + | tail -1 | awk '{print $1}' || echo "0")
        total_lines=$((total_lines + frontend_lines))
        code_lines=$((code_lines + frontend_lines))
        code_metrics+=("Frontend: $frontend_lines lines of JavaScript/TypeScript code")
        log "Frontend: $frontend_lines lines of code"
    fi
    
    if [[ -d tests ]]; then
        local test_lines=$(find tests -name "*.py" -exec wc -l {} + | tail -1 | awk '{print $1}' || echo "0")
        total_lines=$((total_lines + test_lines))
        code_metrics+=("Tests: $test_lines lines of test code")
        log "Tests: $test_lines lines of test code"
        
        # Test-to-code ratio
        if [[ $code_lines -gt 0 ]]; then
            local test_ratio=$((test_lines * 100 / code_lines))
            code_metrics+=("Test-to-code ratio: ${test_ratio}%")
            log "Test-to-code ratio: ${test_ratio}%"
            
            if [[ $test_ratio -lt 20 ]]; then
                code_issues=$((code_issues + 1))
                code_metrics+=("Low test coverage ratio")
                log "⚠️ Test coverage ratio below 20%"
            fi
        fi
    fi
    
    # Complexity assessment
    if [[ -d api ]]; then
        local large_files=$(find api -name "*.py" -exec wc -l {} + | awk '$1 > 500 {print $2}' | wc -l || echo "0")
        if [[ $large_files -gt 0 ]]; then
            code_issues=$((code_issues + 1))
            code_metrics+=("$large_files files exceed 500 lines")
            log "⚠️ $large_files large files found (>500 lines)"
        fi
    fi
    
    code_metrics+=("Total codebase: $total_lines lines")
    log "Total codebase: $total_lines lines"
    
    local code_json=$(printf '%s\n' "${code_metrics[@]}" | jq -R . | jq -s .)
    jq --argjson metrics "$code_json" --arg issues "$code_issues" \
       '.metrics.code_metrics = {"issues": ($issues|tonumber), "metrics": $metrics}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    health_issues=$((health_issues + code_issues))
    
    # Dependency health analysis
    log "Analyzing dependency health"
    local dep_issues=0
    local dep_health=()
    
    # Python dependencies
    if [[ -f requirements.txt ]]; then
        local python_deps=$(wc -l < requirements.txt || echo "0")
        dep_health+=("Python dependencies: $python_deps packages")
        log "Python dependencies: $python_deps packages"
        
        # Check for version pinning
        local unpinned=$(grep -c "^[^=<>]*$" requirements.txt || echo "0")
        if [[ $unpinned -gt 0 ]]; then
            dep_issues=$((dep_issues + 1))
            dep_health+=("$unpinned unpinned Python dependencies")
            log "⚠️ $unpinned unpinned Python dependencies"
        fi
        
        # Check for security vulnerabilities (if safety is available)
        if command -v safety &> /dev/null; then
            local vuln_count=$(safety check -r requirements.txt --json 2>/dev/null | jq '.vulnerabilities | length' 2>/dev/null || echo "0")
            if [[ $vuln_count -gt 0 ]]; then
                dep_issues=$((dep_issues + 1))
                dep_health+=("$vuln_count security vulnerabilities in Python dependencies")
                log "⚠️ $vuln_count security vulnerabilities found"
            else
                dep_health+=("No Python security vulnerabilities found")
                log "✅ No Python security vulnerabilities"
            fi
        fi
    fi
    
    # Node.js dependencies
    if [[ -f frontend/package.json ]]; then
        local node_deps=$(jq '.dependencies | length' frontend/package.json 2>/dev/null || echo "0")
        local dev_deps=$(jq '.devDependencies | length' frontend/package.json 2>/dev/null || echo "0")
        local total_node_deps=$((node_deps + dev_deps))
        dep_health+=("Node.js dependencies: $total_node_deps packages ($node_deps prod, $dev_deps dev)")
        log "Node.js dependencies: $total_node_deps packages"
        
        # Check for npm audit issues
        if [[ -d frontend ]] && cd frontend; then
            if command -v npm &> /dev/null; then
                local audit_result=$(npm audit --audit-level=moderate --json 2>/dev/null | jq '.metadata.vulnerabilities.total' 2>/dev/null || echo "0")
                if [[ $audit_result -gt 0 ]]; then
                    dep_issues=$((dep_issues + 1))
                    dep_health+=("$audit_result Node.js security vulnerabilities")
                    log "⚠️ $audit_result Node.js security vulnerabilities"
                else
                    dep_health+=("No Node.js security vulnerabilities found")
                    log "✅ No Node.js security vulnerabilities"
                fi
            fi
            cd "$REPO_ROOT"
        fi
    fi
    
    local dep_json=$(printf '%s\n' "${dep_health[@]}" | jq -R . | jq -s .)
    jq --argjson health "$dep_json" --arg issues "$dep_issues" \
       '.metrics.dependency_health = {"issues": ($issues|tonumber), "health": $health}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    health_issues=$((health_issues + dep_issues))
    
    # Documentation coverage analysis
    log "Analyzing documentation coverage"
    local doc_issues=0
    local doc_coverage=()
    
    # Check for essential documentation files
    local essential_docs=("README.md" "CHANGELOG.md" "LICENSE")
    local missing_docs=()
    
    for doc in "${essential_docs[@]}"; do
        if [[ -f "$doc" ]]; then
            doc_coverage+=("$doc present")
            log "✅ $doc found"
        else
            missing_docs+=("$doc")
            doc_issues=$((doc_issues + 1))
            log "❌ $doc missing"
        fi
    done
    
    if [[ ${#missing_docs[@]} -gt 0 ]]; then
        doc_coverage+=("Missing: ${missing_docs[*]}")
    fi
    
    # Check for API documentation
    if [[ -d docs ]]; then
        local doc_files=$(find docs -name "*.md" | wc -l || echo "0")
        doc_coverage+=("Documentation files: $doc_files")
        log "Documentation files: $doc_files"
        
        if find docs -name "*api*" -o -name "*reference*" >/dev/null 2>&1; then
            doc_coverage+=("API documentation present")
            log "✅ API documentation found"
        else
            doc_issues=$((doc_issues + 1))
            doc_coverage+=("No API documentation found")
            log "⚠️ No API documentation found"
        fi
    else
        doc_issues=$((doc_issues + 1))
        doc_coverage+=("No docs directory found")
        log "⚠️ No docs directory found"
    fi
    
    # Check for inline documentation
    if [[ -d api ]]; then
        local documented_functions=$(find api -name "*.py" -exec grep -l "def.*:" {} \; | xargs grep -l '"""' | wc -l || echo "0")
        local total_py_files=$(find api -name "*.py" | wc -l || echo "0")
        if [[ $total_py_files -gt 0 ]]; then
            local doc_ratio=$((documented_functions * 100 / total_py_files))
            doc_coverage+=("Python docstring coverage: ${doc_ratio}%")
            log "Python docstring coverage: ${doc_ratio}%"
            
            if [[ $doc_ratio -lt 50 ]]; then
                doc_issues=$((doc_issues + 1))
                doc_coverage+=("Low Python docstring coverage")
                log "⚠️ Low Python docstring coverage"
            fi
        fi
    fi
    
    local doc_json=$(printf '%s\n' "${doc_coverage[@]}" | jq -R . | jq -s .)
    jq --argjson coverage "$doc_json" --arg issues "$doc_issues" \
       '.metrics.documentation_coverage = {"issues": ($issues|tonumber), "coverage": $coverage}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    health_issues=$((health_issues + doc_issues))
    
    # Test coverage analysis
    log "Analyzing test coverage"
    local test_issues=0
    local test_coverage=()
    
    if [[ -d tests ]]; then
        local test_files=$(find tests -name "test_*.py" | wc -l || echo "0")
        test_coverage+=("Test files: $test_files")
        log "Test files: $test_files"
        
        # Check for different types of tests
        local unit_tests=$(find tests -name "test_*.py" -exec grep -l "def test_" {} \; | wc -l || echo "0")
        local integration_tests=$(find tests -name "*integration*" -o -name "*api*" | wc -l || echo "0")
        
        test_coverage+=("Unit test files: $unit_tests")
        test_coverage+=("Integration test files: $integration_tests")
        log "Unit tests: $unit_tests, Integration tests: $integration_tests"
        
        if [[ $unit_tests -eq 0 ]]; then
            test_issues=$((test_issues + 1))
            test_coverage+=("No unit tests found")
            log "⚠️ No unit tests found"
        fi
        
        # Check test execution (if pytest is available)
        if command -v pytest &> /dev/null; then
            log "Running test coverage analysis..."
            local coverage_result=$(cd "$REPO_ROOT" && timeout 60 python -m pytest tests/ --cov=api --cov-report=term-missing --tb=no -q 2>/dev/null | grep "TOTAL" | awk '{print $4}' | sed 's/%//' || echo "0")
            if [[ -n "$coverage_result" && "$coverage_result" != "0" ]]; then
                test_coverage+=("Code coverage: ${coverage_result}%")
                log "Code coverage: ${coverage_result}%"
                
                if [[ $(echo "$coverage_result < 70" | bc -l 2>/dev/null || echo "1") -eq 1 ]]; then
                    test_issues=$((test_issues + 1))
                    test_coverage+=("Low code coverage")
                    log "⚠️ Code coverage below 70%"
                fi
            else
                test_coverage+=("Could not determine code coverage")
                log "ℹ️ Could not determine code coverage"
            fi
        fi
    else
        test_issues=$((test_issues + 1))
        test_coverage+=("No tests directory found")
        log "❌ No tests directory found"
    fi
    
    # Frontend testing
    if [[ -f frontend/package.json ]]; then
        if jq -e '.scripts.test' frontend/package.json >/dev/null 2>&1; then
            test_coverage+=("Frontend test script configured")
            log "✅ Frontend test script found"
        else
            test_issues=$((test_issues + 1))
            test_coverage+=("No frontend test script configured")
            log "⚠️ No frontend test script configured"
        fi
    fi
    
    local test_json=$(printf '%s\n' "${test_coverage[@]}" | jq -R . | jq -s .)
    jq --argjson coverage "$test_json" --arg issues "$test_issues" \
       '.metrics.test_coverage = {"issues": ($issues|tonumber), "coverage": $coverage}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    health_issues=$((health_issues + test_issues))
    
    # Build stability analysis
    log "Analyzing build stability"
    local build_issues=0
    local build_stability=()
    
    # Docker build check
    if [[ -f Dockerfile ]]; then
        build_stability+=("Dockerfile present")
        log "✅ Dockerfile found"
        
        # Quick Dockerfile validation
        if grep -q "FROM" Dockerfile; then
            build_stability+=("Dockerfile has base image")
            log "✅ Dockerfile has base image"
        else
            build_issues=$((build_issues + 1))
            build_stability+=("Dockerfile missing base image")
            log "❌ Dockerfile missing base image"
        fi
    else
        build_stability+=("No Dockerfile found")
        log "ℹ️ No Dockerfile found"
    fi
    
    # Docker Compose check
    if [[ -f docker-compose.yml ]]; then
        build_stability+=("docker-compose.yml present")
        log "✅ docker-compose.yml found"
    else
        build_stability+=("No docker-compose.yml found")
        log "ℹ️ No docker-compose.yml found"
    fi
    
    # CI/CD configuration check
    if [[ -d .github/workflows ]]; then
        local workflow_files=$(find .github/workflows -name "*.yml" -o -name "*.yaml" | wc -l || echo "0")
        build_stability+=("GitHub Actions workflows: $workflow_files")
        log "GitHub Actions workflows: $workflow_files"
        
        if [[ $workflow_files -eq 0 ]]; then
            build_issues=$((build_issues + 1))
            build_stability+=("No CI/CD workflows configured")
            log "⚠️ No CI/CD workflows configured"
        fi
    else
        build_issues=$((build_issues + 1))
        build_stability+=("No CI/CD configuration found")
        log "⚠️ No CI/CD configuration found"
    fi
    
    # Package configuration check
    if [[ -f pyproject.toml ]]; then
        build_stability+=("Python packaging configured (pyproject.toml)")
        log "✅ Python packaging configured"
    elif [[ -f setup.py ]]; then
        build_stability+=("Python packaging configured (setup.py)")
        log "✅ Python packaging configured"
    else
        build_stability+=("No Python packaging configuration")
        log "ℹ️ No Python packaging configuration"
    fi
    
    local build_json=$(printf '%s\n' "${build_stability[@]}" | jq -R . | jq -s .)
    jq --argjson stability "$build_json" --arg issues "$build_issues" \
       '.metrics.build_stability = {"issues": ($issues|tonumber), "stability": $stability}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    health_issues=$((health_issues + build_issues))
    
    # Calculate overall health score
    local total_categories=5
    local healthy_categories=$((total_categories - health_issues))
    local health_score=$((healthy_categories * 100 / total_categories))
    
    jq --arg issues "$health_issues" --arg score "$health_score" \
       '.summary.issues = ($issues|tonumber) | .summary.health_score = ($score|tonumber)' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    log "Project health assessment completed: Score ${health_score}% ($health_issues issues)"
    return $([[ $health_issues -le 3 ]])  # Allow up to 3 health issues
}

# Timeline and milestone tracking
run_timeline_tests() {
    log "Starting timeline and milestone assessment"
    local timeline_issues=0
    local report_file="$RESULTS_DIR/timeline_${TIMESTAMP}.json"
    
    cat > "$report_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "test_type": "timeline_assessment",
    "tracking": {
        "version_control": {},
        "release_management": {},
        "milestone_tracking": {},
        "change_velocity": {}
    },
    "summary": {"issues": 0, "timeline_health": "unknown"}
}
EOF

    # Version control analysis
    log "Analyzing version control patterns"
    local vc_issues=0
    local vc_tracking=()
    
    if [[ -d .git ]]; then
        # Commit frequency analysis
        local commits_last_month=$(git log --since="1 month ago" --oneline | wc -l || echo "0")
        local commits_last_week=$(git log --since="1 week ago" --oneline | wc -l || echo "0")
        
        vc_tracking+=("Commits last month: $commits_last_month")
        vc_tracking+=("Commits last week: $commits_last_week")
        log "Recent activity: $commits_last_week commits (week), $commits_last_month commits (month)"
        
        if [[ $commits_last_month -eq 0 ]]; then
            vc_issues=$((vc_issues + 1))
            vc_tracking+=("No recent development activity")
            log "⚠️ No commits in the last month"
        fi
        
        # Branch analysis
        local total_branches=$(git branch -a | wc -l || echo "0")
        local active_branches=$(git for-each-ref --format='%(refname:short) %(committerdate)' refs/heads | awk '$2 >= "'$(date -d '1 month ago' '+%Y-%m-%d')'"' | wc -l || echo "0")
        
        vc_tracking+=("Total branches: $total_branches")
        vc_tracking+=("Active branches (last month): $active_branches")
        log "Branches: $active_branches active of $total_branches total"
        
        # Contributor analysis
        local contributors=$(git log --since="3 months ago" --pretty=format:'%an' | sort | uniq | wc -l || echo "0")
        vc_tracking+=("Active contributors (3 months): $contributors")
        log "Active contributors: $contributors"
        
        if [[ $contributors -eq 0 ]]; then
            vc_issues=$((vc_issues + 1))
            vc_tracking+=("No active contributors")
            log "⚠️ No active contributors in last 3 months"
        fi
        
        local vc_json=$(printf '%s\n' "${vc_tracking[@]}" | jq -R . | jq -s .)
        jq --argjson tracking "$vc_json" --arg issues "$vc_issues" \
           '.tracking.version_control = {"issues": ($issues|tonumber), "tracking": $tracking}' \
           "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    else
        vc_issues=$((vc_issues + 1))
        vc_tracking+=("Not a git repository")
        log "❌ Not a git repository"
    fi
    
    timeline_issues=$((timeline_issues + vc_issues))
    
    # Release management analysis
    log "Analyzing release management"
    local release_issues=0
    local release_tracking=()
    
    if [[ -d .git ]]; then
        # Tag analysis
        local total_tags=$(git tag | wc -l || echo "0")
        local recent_tags=$(git tag --sort=-creatordate | head -5 | wc -l || echo "0")
        
        release_tracking+=("Total releases/tags: $total_tags")
        log "Total releases: $total_tags"
        
        if [[ $total_tags -eq 0 ]]; then
            release_issues=$((release_issues + 1))
            release_tracking+=("No releases/tags found")
            log "⚠️ No releases or tags found"
        else
            local latest_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "unknown")
            local tag_age=$(git log -1 --format="%cr" "$latest_tag" 2>/dev/null || echo "unknown")
            release_tracking+=("Latest release: $latest_tag ($tag_age)")
            log "Latest release: $latest_tag ($tag_age)"
        fi
        
        # Check for semantic versioning
        if [[ $total_tags -gt 0 ]]; then
            local semver_tags=$(git tag | grep -E '^v?[0-9]+\.[0-9]+\.[0-9]+' | wc -l || echo "0")
            local semver_ratio=$((semver_tags * 100 / total_tags))
            release_tracking+=("Semantic versioning compliance: ${semver_ratio}%")
            log "Semantic versioning: ${semver_ratio}%"
            
            if [[ $semver_ratio -lt 80 ]]; then
                release_issues=$((release_issues + 1))
                release_tracking+=("Inconsistent versioning scheme")
                log "⚠️ Inconsistent versioning scheme"
            fi
        fi
        
        local release_json=$(printf '%s\n' "${release_tracking[@]}" | jq -R . | jq -s .)
        jq --argjson tracking "$release_json" --arg issues "$release_issues" \
           '.tracking.release_management = {"issues": ($issues|tonumber), "tracking": $tracking}' \
           "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    fi
    
    timeline_issues=$((timeline_issues + release_issues))
    
    # Milestone tracking analysis
    log "Analyzing milestone tracking"
    local milestone_issues=0
    local milestone_tracking=()
    
    # Check for CHANGELOG.md
    if [[ -f CHANGELOG.md ]]; then
        milestone_tracking+=("CHANGELOG.md present")
        log "✅ CHANGELOG.md found"
        
        # Analyze changelog structure
        local changelog_entries=$(grep -c "^##\|^#" CHANGELOG.md || echo "0")
        milestone_tracking+=("Changelog entries: $changelog_entries")
        log "Changelog entries: $changelog_entries"
        
        if [[ $changelog_entries -eq 0 ]]; then
            milestone_issues=$((milestone_issues + 1))
            milestone_tracking+=("Empty changelog")
            log "⚠️ Empty changelog"
        fi
    else
        milestone_issues=$((milestone_issues + 1))
        milestone_tracking+=("No CHANGELOG.md found")
        log "⚠️ No CHANGELOG.md found"
    fi
    
    # Check for project management files
    if [[ -f ROADMAP.md ]]; then
        milestone_tracking+=("ROADMAP.md present")
        log "✅ ROADMAP.md found"
    else
        milestone_tracking+=("No ROADMAP.md found")
        log "ℹ️ No ROADMAP.md found"
    fi
    
    # Check for issue tracking integration
    if [[ -d .github ]]; then
        if [[ -d .github/ISSUE_TEMPLATE ]] || [[ -f .github/ISSUE_TEMPLATE.md ]]; then
            milestone_tracking+=("Issue templates configured")
            log "✅ Issue templates found"
        else
            milestone_issues=$((milestone_issues + 1))
            milestone_tracking+=("No issue templates found")
            log "⚠️ No issue templates found"
        fi
        
        if [[ -d .github/PULL_REQUEST_TEMPLATE ]] || [[ -f .github/PULL_REQUEST_TEMPLATE.md ]]; then
            milestone_tracking+=("PR templates configured")
            log "✅ PR templates found"
        else
            milestone_tracking+=("No PR templates found")
            log "ℹ️ No PR templates found"
        fi
    fi
    
    local milestone_json=$(printf '%s\n' "${milestone_tracking[@]}" | jq -R . | jq -s .)
    jq --argjson tracking "$milestone_json" --arg issues "$milestone_issues" \
       '.tracking.milestone_tracking = {"issues": ($issues|tonumber), "tracking": $tracking}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    timeline_issues=$((timeline_issues + milestone_issues))
    
    # Change velocity analysis
    log "Analyzing change velocity"
    local velocity_issues=0
    local velocity_tracking=()
    
    if [[ -d .git ]]; then
        # Lines changed analysis
        local lines_added=$(git log --since="1 month ago" --numstat | awk '{add+=$1} END {print add}' || echo "0")
        local lines_deleted=$(git log --since="1 month ago" --numstat | awk '{del+=$2} END {print del}' || echo "0")
        local net_change=$((lines_added - lines_deleted))
        
        velocity_tracking+=("Lines added (month): $lines_added")
        velocity_tracking+=("Lines deleted (month): $lines_deleted")
        velocity_tracking+=("Net change (month): $net_change")
        log "Monthly velocity: +$lines_added -$lines_deleted (net: $net_change)"
        
        # Files changed analysis
        local files_changed=$(git log --since="1 month ago" --name-only --pretty=format: | sort | uniq | wc -l || echo "0")
        velocity_tracking+=("Files changed (month): $files_changed")
        log "Files changed: $files_changed"
        
        # Average commit size
        if [[ $commits_last_month -gt 0 ]]; then
            local avg_commit_size=$((lines_added / commits_last_month))
            velocity_tracking+=("Average commit size: $avg_commit_size lines")
            log "Average commit size: $avg_commit_size lines"
            
            if [[ $avg_commit_size -gt 500 ]]; then
                velocity_issues=$((velocity_issues + 1))
                velocity_tracking+=("Large commit sizes detected")
                log "⚠️ Large commit sizes detected"
            fi
        fi
        
        local velocity_json=$(printf '%s\n' "${velocity_tracking[@]}" | jq -R . | jq -s .)
        jq --argjson tracking "$velocity_json" --arg issues "$velocity_issues" \
           '.tracking.change_velocity = {"issues": ($issues|tonumber), "tracking": $tracking}' \
           "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    fi
    
    timeline_issues=$((timeline_issues + velocity_issues))
    
    # Calculate timeline health
    local timeline_health="Excellent"
    if [[ $timeline_issues -eq 0 ]]; then
        timeline_health="Excellent"
    elif [[ $timeline_issues -le 2 ]]; then
        timeline_health="Good"
    elif [[ $timeline_issues -le 4 ]]; then
        timeline_health="Fair"
    else
        timeline_health="Poor"
    fi
    
    jq --arg issues "$timeline_issues" --arg health "$timeline_health" \
       '.summary.issues = ($issues|tonumber) | .summary.timeline_health = $health' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    log "Timeline assessment completed: $timeline_health ($timeline_issues issues)"
    return $([[ $timeline_issues -le 3 ]])  # Allow up to 3 timeline issues
}

# Resource allocation assessment
run_resource_tests() {
    log "Starting resource allocation assessment"
    local resource_issues=0
    local report_file="$RESULTS_DIR/resources_${TIMESTAMP}.json"
    
    cat > "$report_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "test_type": "resource_allocation_assessment",
    "resources": {
        "infrastructure": {},
        "tooling": {},
        "automation": {},
        "monitoring": {}
    },
    "summary": {"issues": 0, "efficiency_score": 0}
}
EOF

    # Infrastructure resource assessment
    log "Analyzing infrastructure resources"
    local infra_issues=0
    local infra_resources=()
    
    # Docker resource configuration
    if [[ -f docker-compose.yml ]]; then
        infra_resources+=("Docker Compose configuration present")
        log "✅ Docker Compose found"
        
        # Check for resource limits
        if grep -q "mem_limit\|cpus\|memory" docker-compose.yml; then
            infra_resources+=("Resource limits configured")
            log "✅ Resource limits configured"
        else
            infra_issues=$((infra_issues + 1))
            infra_resources+=("No resource limits configured")
            log "⚠️ No resource limits in Docker Compose"
        fi
        
        # Check for health checks
        if grep -q "healthcheck" docker-compose.yml; then
            infra_resources+=("Health checks configured")
            log "✅ Health checks configured"
        else
            infra_issues=$((infra_issues + 1))
            infra_resources+=("No health checks configured")
            log "⚠️ No health checks configured"
        fi
    else
        infra_resources+=("No Docker Compose configuration")
        log "ℹ️ No Docker Compose configuration"
    fi
    
    # Check for caching infrastructure
    if grep -q "redis\|memcached\|cache" docker-compose.yml 2>/dev/null || [[ -d cache ]]; then
        infra_resources+=("Caching infrastructure present")
        log "✅ Caching infrastructure found"
    else
        infra_resources+=("No caching infrastructure found")
        log "ℹ️ No caching infrastructure found"
    fi
    
    # Check for database optimization
    if grep -q "database\|postgres\|mysql\|sqlite" docker-compose.yml 2>/dev/null; then
        infra_resources+=("Database infrastructure present")
        log "✅ Database infrastructure found"
    else
        infra_resources+=("No database infrastructure found")
        log "ℹ️ No database infrastructure found"
    fi
    
    local infra_json=$(printf '%s\n' "${infra_resources[@]}" | jq -R . | jq -s .)
    jq --argjson resources "$infra_json" --arg issues "$infra_issues" \
       '.resources.infrastructure = {"issues": ($issues|tonumber), "resources": $resources}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    resource_issues=$((resource_issues + infra_issues))
    
    # Tooling resource assessment
    log "Analyzing development tooling"
    local tooling_issues=0
    local tooling_resources=()
    
    # Code quality tools
    local quality_tools=()
    if [[ -f .flake8 ]] || [[ -f setup.cfg ]] || [[ -f pyproject.toml ]]; then
        quality_tools+=("Python linting")
    fi
    if [[ -f frontend/eslint.config.js ]] || [[ -f frontend/.eslintrc.* ]]; then
        quality_tools+=("JavaScript linting")
    fi
    if [[ -f .pre-commit-config.yaml ]]; then
        quality_tools+=("Pre-commit hooks")
    fi
    
    if [[ ${#quality_tools[@]} -gt 0 ]]; then
        tooling_resources+=("Quality tools: ${quality_tools[*]}")
        log "✅ Quality tools: ${quality_tools[*]}"
    else
        tooling_issues=$((tooling_issues + 1))
        tooling_resources+=("No code quality tools configured")
        log "⚠️ No code quality tools configured"
    fi
    
    # Testing tools
    local testing_tools=()
    if [[ -f requirements.txt ]] && grep -q "pytest" requirements.txt; then
        testing_tools+=("pytest")
    fi
    if [[ -f frontend/package.json ]] && jq -e '.devDependencies | has("jest")' frontend/package.json >/dev/null 2>&1; then
        testing_tools+=("jest")
    fi
    if [[ -f cypress.config.js ]]; then
        testing_tools+=("cypress")
    fi
    
    if [[ ${#testing_tools[@]} -gt 0 ]]; then
        tooling_resources+=("Testing tools: ${testing_tools[*]}")
        log "✅ Testing tools: ${testing_tools[*]}"
    else
        tooling_issues=$((tooling_issues + 1))
        tooling_resources+=("No testing tools configured")
        log "⚠️ No testing tools configured"
    fi
    
    # Documentation tools
    if [[ -d docs ]]; then
        tooling_resources+=("Documentation system present")
        log "✅ Documentation system found"
    else
        tooling_resources+=("No documentation system")
        log "ℹ️ No documentation system found"
    fi
    
    local tooling_json=$(printf '%s\n' "${tooling_resources[@]}" | jq -R . | jq -s .)
    jq --argjson resources "$tooling_json" --arg issues "$tooling_issues" \
       '.resources.tooling = {"issues": ($issues|tonumber), "resources": $resources}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    resource_issues=$((resource_issues + tooling_issues))
    
    # Automation assessment
    log "Analyzing automation resources"
    local automation_issues=0
    local automation_resources=()
    
    # CI/CD automation
    if [[ -d .github/workflows ]]; then
        local workflow_count=$(find .github/workflows -name "*.yml" -o -name "*.yaml" | wc -l || echo "0")
        automation_resources+=("GitHub Actions workflows: $workflow_count")
        log "✅ GitHub Actions: $workflow_count workflows"
        
        if [[ $workflow_count -eq 0 ]]; then
            automation_issues=$((automation_issues + 1))
            automation_resources+=("No CI/CD workflows")
            log "⚠️ No CI/CD workflows"
        fi
    else
        automation_issues=$((automation_issues + 1))
        automation_resources+=("No CI/CD automation")
        log "⚠️ No CI/CD automation"
    fi
    
    # Build automation
    if [[ -f Dockerfile ]]; then
        automation_resources+=("Containerized builds available")
        log "✅ Containerized builds available"
    else
        automation_resources+=("No containerized builds")
        log "ℹ️ No containerized builds"
    fi
    
    # Deployment automation
    if find .github/workflows -name "*.yml" -o -name "*.yaml" 2>/dev/null | xargs grep -l "deploy" >/dev/null 2>&1; then
        automation_resources+=("Deployment automation configured")
        log "✅ Deployment automation found"
    else
        automation_resources+=("No deployment automation")
        log "ℹ️ No deployment automation found"
    fi
    
    # Dependency automation
    if find .github/workflows -name "*.yml" -o -name "*.yaml" 2>/dev/null | xargs grep -l "dependabot\|renovate" >/dev/null 2>&1; then
        automation_resources+=("Dependency automation configured")
        log "✅ Dependency automation found"
    else
        automation_resources+=("No dependency automation")
        log "ℹ️ No dependency automation found"
    fi
    
    local automation_json=$(printf '%s\n' "${automation_resources[@]}" | jq -R . | jq -s .)
    jq --argjson resources "$automation_json" --arg issues "$automation_issues" \
       '.resources.automation = {"issues": ($issues|tonumber), "resources": $resources}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    resource_issues=$((resource_issues + automation_issues))
    
    # Calculate efficiency score
    local total_categories=3
    local efficient_categories=$((total_categories - resource_issues))
    local efficiency_score=$((efficient_categories * 100 / total_categories))
    
    jq --arg issues "$resource_issues" --arg score "$efficiency_score" \
       '.summary.issues = ($issues|tonumber) | .summary.efficiency_score = ($score|tonumber)' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    log "Resource allocation assessment completed: Efficiency ${efficiency_score}% ($resource_issues issues)"
    return $([[ $resource_issues -le 2 ]])  # Allow up to 2 resource issues
}

# Deliverable assessment
run_deliverable_tests() {
    log "Starting deliverable assessment"
    local deliverable_issues=0
    local report_file="$RESULTS_DIR/deliverables_${TIMESTAMP}.json"
    
    cat > "$report_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "test_type": "deliverable_assessment",
    "deliverables": {
        "application_readiness": {},
        "deployment_readiness": {},
        "documentation_readiness": {},
        "support_readiness": {}
    },
    "summary": {"issues": 0, "delivery_readiness": "unknown"}
}
EOF

    # Application readiness assessment
    log "Analyzing application readiness"
    local app_issues=0
    local app_readiness=()
    
    # Core functionality completeness
    if [[ -d api ]] && [[ -d frontend ]]; then
        app_readiness+=("Full-stack application present")
        log "✅ Full-stack application found"
    else
        app_issues=$((app_issues + 1))
        app_readiness+=("Incomplete application stack")
        log "❌ Incomplete application stack"
    fi
    
    # Configuration management
    if [[ -f api/settings.py ]] || [[ -f config.py ]] || [[ -f .env.example ]]; then
        app_readiness+=("Configuration management present")
        log "✅ Configuration management found"
    else
        app_issues=$((app_issues + 1))
        app_readiness+=("No configuration management")
        log "⚠️ No configuration management found"
    fi
    
    # Error handling
    if [[ -d api ]] && find api -name "*.py" | xargs grep -l "try:\|except\|raise" >/dev/null 2>&1; then
        app_readiness+=("Error handling implemented")
        log "✅ Error handling found"
    else
        app_issues=$((app_issues + 1))
        app_readiness+=("Limited error handling")
        log "⚠️ Limited error handling"
    fi
    
    # Security features
    local security_features=()
    if [[ -d api ]] && find api -name "*.py" | xargs grep -l "authentication\|jwt\|token" >/dev/null 2>&1; then
        security_features+=("authentication")
    fi
    if [[ -d api ]] && find api -name "*.py" | xargs grep -l "cors\|Cross" >/dev/null 2>&1; then
        security_features+=("CORS")
    fi
    if [[ -d api ]] && find api -name "*.py" | xargs grep -l "validation\|validate" >/dev/null 2>&1; then
        security_features+=("input validation")
    fi
    
    if [[ ${#security_features[@]} -gt 0 ]]; then
        app_readiness+=("Security features: ${security_features[*]}")
        log "✅ Security features: ${security_features[*]}"
    else
        app_issues=$((app_issues + 1))
        app_readiness+=("No security features identified")
        log "⚠️ No security features identified"
    fi
    
    local app_json=$(printf '%s\n' "${app_readiness[@]}" | jq -R . | jq -s .)
    jq --argjson readiness "$app_json" --arg issues "$app_issues" \
       '.deliverables.application_readiness = {"issues": ($issues|tonumber), "readiness": $readiness}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    deliverable_issues=$((deliverable_issues + app_issues))
    
    # Deployment readiness assessment
    log "Analyzing deployment readiness"
    local deploy_issues=0
    local deploy_readiness=()
    
    # Containerization
    if [[ -f Dockerfile ]] && [[ -f docker-compose.yml ]]; then
        deploy_readiness+=("Full containerization support")
        log "✅ Full containerization support"
    elif [[ -f Dockerfile ]]; then
        deploy_readiness+=("Partial containerization (Dockerfile only)")
        log "⚠️ Partial containerization"
    else
        deploy_issues=$((deploy_issues + 1))
        deploy_readiness+=("No containerization")
        log "❌ No containerization"
    fi
    
    # Environment configuration
    if [[ -f .env.example ]] || [[ -f docker-compose.yml ]]; then
        deploy_readiness+=("Environment configuration documented")
        log "✅ Environment configuration documented"
    else
        deploy_issues=$((deploy_issues + 1))
        deploy_readiness+=("No environment configuration")
        log "⚠️ No environment configuration"
    fi
    
    # Production optimizations
    if [[ -f Dockerfile ]] && grep -q "production\|optimize" Dockerfile; then
        deploy_readiness+=("Production optimizations present")
        log "✅ Production optimizations found"
    else
        deploy_readiness+=("No production optimizations identified")
        log "ℹ️ No production optimizations identified"
    fi
    
    # Monitoring and logging
    if grep -r "logging\|logger\|log" api/ >/dev/null 2>&1; then
        deploy_readiness+=("Logging implementation present")
        log "✅ Logging implementation found"
    else
        deploy_issues=$((deploy_issues + 1))
        deploy_readiness+=("No logging implementation")
        log "⚠️ No logging implementation"
    fi
    
    local deploy_json=$(printf '%s\n' "${deploy_readiness[@]}" | jq -R . | jq -s .)
    jq --argjson readiness "$deploy_json" --arg issues "$deploy_issues" \
       '.deliverables.deployment_readiness = {"issues": ($issues|tonumber), "readiness": $readiness}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    deliverable_issues=$((deliverable_issues + deploy_issues))
    
    # Documentation readiness assessment
    log "Analyzing documentation readiness"
    local doc_issues=0
    local doc_readiness=()
    
    # User documentation
    if [[ -f README.md ]]; then
        local readme_size=$(wc -l < README.md || echo "0")
        if [[ $readme_size -gt 20 ]]; then
            doc_readiness+=("Comprehensive README.md ($readme_size lines)")
            log "✅ Comprehensive README.md"
        else
            doc_issues=$((doc_issues + 1))
            doc_readiness+=("Minimal README.md ($readme_size lines)")
            log "⚠️ Minimal README.md"
        fi
    else
        doc_issues=$((doc_issues + 1))
        doc_readiness+=("No README.md")
        log "❌ No README.md"
    fi
    
    # Installation instructions
    if [[ -f README.md ]] && grep -q "install\|setup\|getting.started" README.md; then
        doc_readiness+=("Installation instructions present")
        log "✅ Installation instructions found"
    else
        doc_issues=$((doc_issues + 1))
        doc_readiness+=("No installation instructions")
        log "⚠️ No installation instructions"
    fi
    
    # API documentation
    if [[ -d docs ]] && find docs -name "*api*" >/dev/null 2>&1; then
        doc_readiness+=("API documentation present")
        log "✅ API documentation found"
    else
        doc_readiness+=("No API documentation")
        log "ℹ️ No API documentation found"
    fi
    
    # Change documentation
    if [[ -f CHANGELOG.md ]]; then
        doc_readiness+=("Change log present")
        log "✅ Change log found"
    else
        doc_issues=$((doc_issues + 1))
        doc_readiness+=("No change log")
        log "⚠️ No change log"
    fi
    
    local doc_json=$(printf '%s\n' "${doc_readiness[@]}" | jq -R . | jq -s .)
    jq --argjson readiness "$doc_json" --arg issues "$doc_issues" \
       '.deliverables.documentation_readiness = {"issues": ($issues|tonumber), "readiness": $readiness}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    deliverable_issues=$((deliverable_issues + doc_issues))
    
    # Support readiness assessment
    log "Analyzing support readiness"
    local support_issues=0
    local support_readiness=()
    
    # Issue tracking
    if [[ -d .github/ISSUE_TEMPLATE ]]; then
        support_readiness+=("Issue templates configured")
        log "✅ Issue templates found"
    else
        support_issues=$((support_issues + 1))
        support_readiness+=("No issue templates")
        log "⚠️ No issue templates"
    fi
    
    # Contributing guidelines
    if [[ -f CONTRIBUTING.md ]]; then
        support_readiness+=("Contributing guidelines present")
        log "✅ Contributing guidelines found"
    else
        support_readiness+=("No contributing guidelines")
        log "ℹ️ No contributing guidelines"
    fi
    
    # License
    if [[ -f LICENSE ]]; then
        support_readiness+=("License file present")
        log "✅ License file found"
    else
        support_issues=$((support_issues + 1))
        support_readiness+=("No license file")
        log "⚠️ No license file"
    fi
    
    # Security policy
    if [[ -f SECURITY.md ]] || [[ -f .github/SECURITY.md ]]; then
        support_readiness+=("Security policy present")
        log "✅ Security policy found"
    else
        support_readiness+=("No security policy")
        log "ℹ️ No security policy found"
    fi
    
    local support_json=$(printf '%s\n' "${support_readiness[@]}" | jq -R . | jq -s .)
    jq --argjson readiness "$support_json" --arg issues "$support_issues" \
       '.deliverables.support_readiness = {"issues": ($issues|tonumber), "readiness": $readiness}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    deliverable_issues=$((deliverable_issues + support_issues))
    
    # Calculate delivery readiness
    local delivery_readiness="Production Ready"
    if [[ $deliverable_issues -eq 0 ]]; then
        delivery_readiness="Production Ready"
    elif [[ $deliverable_issues -le 2 ]]; then
        delivery_readiness="Nearly Ready"
    elif [[ $deliverable_issues -le 4 ]]; then
        delivery_readiness="Development Complete"
    else
        delivery_readiness="In Development"
    fi
    
    jq --arg issues "$deliverable_issues" --arg readiness "$delivery_readiness" \
       '.summary.issues = ($issues|tonumber) | .summary.delivery_readiness = $readiness' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    log "Deliverable assessment completed: $delivery_readiness ($deliverable_issues issues)"
    return $([[ $deliverable_issues -le 3 ]])  # Allow up to 3 deliverable issues
}

# Main execution
main() {
    local test_name="${1:-all}"
    
    log "Starting Project Manager role testing: $test_name"
    
    case "$test_name" in
        "project_health_tests")
            run_project_health_tests
            ;;
        "timeline_tests")
            run_timeline_tests
            ;;
        "resource_tests")
            run_resource_tests
            ;;
        "deliverable_tests")
            run_deliverable_tests
            ;;
        "all")
            local overall_success=true
            
            run_project_health_tests || overall_success=false
            run_timeline_tests || overall_success=false
            run_resource_tests || overall_success=false
            run_deliverable_tests || overall_success=false
            
            if $overall_success; then
                log "✅ All Project Manager tests passed"
                return 0
            else
                log "❌ Some Project Manager tests failed"
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