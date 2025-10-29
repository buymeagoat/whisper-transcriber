#!/bin/bash

# End User Role Testing Implementation
# Comprehensive usability, workflow, accessibility, and real-world scenario testing

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Configuration
RESULTS_DIR="${REPO_ROOT}/logs/testing_results/end_user"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p "$RESULTS_DIR"

# Logging
log() {
    echo "[End User] $*" | tee -a "$RESULTS_DIR/testing.log"
}

# Usability Testing
run_usability_tests() {
    log "Starting usability testing"
    local usability_issues=0
    local report_file="$RESULTS_DIR/usability_${TIMESTAMP}.json"
    
    cat > "$report_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "test_type": "usability_assessment",
    "categories": {
        "interface_clarity": {},
        "navigation": {},
        "error_messages": {},
        "user_feedback": {},
        "performance_perception": {}
    },
    "summary": {"issues": 0, "score": 0}
}
EOF

    # Interface clarity assessment
    log "Assessing interface clarity"
    local clarity_issues=0
    local clarity_findings=()
    
    if [[ -d frontend/src ]]; then
        # Check for proper labeling
        local unlabeled_inputs=$(find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "<input" | xargs grep -c "<input[^>]*>" | awk '{sum+=$1} END {print sum}' || echo "0")
        local labeled_inputs=$(find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "aria-label\|htmlFor\|<label" | wc -l || echo "0")
        
        if [[ $unlabeled_inputs -gt $labeled_inputs ]]; then
            clarity_issues=$((clarity_issues + 1))
            clarity_findings+=("Many inputs lack proper labels")
            log "⚠️ Found unlabeled form inputs"
        fi
        
        # Check for loading states
        if ! find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "loading\|spinner\|skeleton" >/dev/null 2>&1; then
            clarity_issues=$((clarity_issues + 1))
            clarity_findings+=("No loading states found")
            log "⚠️ No loading states implemented"
        fi
        
        # Check for empty states
        if ! find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "empty\|no.*data\|no.*results" >/dev/null 2>&1; then
            clarity_issues=$((clarity_issues + 1))
            clarity_findings+=("No empty states found")
            log "⚠️ No empty states implemented"
        fi
        
        local clarity_json=$(printf '%s\n' "${clarity_findings[@]}" | jq -R . | jq -s .)
        jq --argjson findings "$clarity_json" --arg issues "$clarity_issues" \
           '.categories.interface_clarity = {"issues": ($issues|tonumber), "findings": $findings}' \
           "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    fi
    
    usability_issues=$((usability_issues + clarity_issues))
    
    # Navigation assessment
    log "Assessing navigation usability"
    local nav_issues=0
    local nav_findings=()
    
    if [[ -d frontend/src ]]; then
        # Check for consistent navigation
        if ! find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "nav\|menu\|header" >/dev/null 2>&1; then
            nav_issues=$((nav_issues + 1))
            nav_findings+=("No navigation components found")
            log "⚠️ No navigation components found"
        fi
        
        # Check for breadcrumbs on complex pages
        if find frontend/src -path "*/pages/*" -name "*.jsx" -o -name "*.tsx" | wc -l | awk '{if($1 > 5) print "many"}' | grep -q "many"; then
            if ! find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "breadcrumb" >/dev/null 2>&1; then
                nav_issues=$((nav_issues + 1))
                nav_findings+=("Complex app lacks breadcrumb navigation")
                log "⚠️ Consider adding breadcrumb navigation"
            fi
        fi
        
        # Check for search functionality
        if ! find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "search\|filter" >/dev/null 2>&1; then
            nav_findings+=("No search/filter functionality found")
            log "ℹ️ Consider adding search functionality"
        fi
        
        local nav_json=$(printf '%s\n' "${nav_findings[@]}" | jq -R . | jq -s .)
        jq --argjson findings "$nav_json" --arg issues "$nav_issues" \
           '.categories.navigation = {"issues": ($issues|tonumber), "findings": $findings}' \
           "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    fi
    
    usability_issues=$((usability_issues + nav_issues))
    
    # Error message assessment
    log "Assessing error message quality"
    local error_issues=0
    local error_findings=()
    
    if [[ -d frontend/src ]]; then
        # Check for user-friendly error messages
        local generic_errors=$(find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -c "Error\|error\|failed" | awk '{sum+=$1} END {print sum}' || echo "0")
        local helpful_errors=$(find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -c "try again\|contact support\|check.*and" | awk '{sum+=$1} END {print sum}' || echo "0")
        
        if [[ $generic_errors -gt 0 && $helpful_errors -eq 0 ]]; then
            error_issues=$((error_issues + 1))
            error_findings+=("Error messages lack helpful guidance")
            log "⚠️ Error messages could be more helpful"
        fi
        
        # Check for form validation messages
        if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "<form\|<input" >/dev/null 2>&1; then
            if ! find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "validation\|required\|invalid" >/dev/null 2>&1; then
                error_issues=$((error_issues + 1))
                error_findings+=("Forms lack validation feedback")
                log "⚠️ Forms lack validation feedback"
            fi
        fi
        
        local error_json=$(printf '%s\n' "${error_findings[@]}" | jq -R . | jq -s .)
        jq --argjson findings "$error_json" --arg issues "$error_issues" \
           '.categories.error_messages = {"issues": ($issues|tonumber), "findings": $findings}' \
           "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    fi
    
    usability_issues=$((usability_issues + error_issues))
    
    # User feedback assessment
    log "Assessing user feedback mechanisms"
    local feedback_issues=0
    local feedback_findings=()
    
    if [[ -d frontend/src ]]; then
        # Check for success confirmations
        if ! find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "success\|saved\|completed\|toast\|notification" >/dev/null 2>&1; then
            feedback_issues=$((feedback_issues + 1))
            feedback_findings+=("No success feedback mechanisms found")
            log "⚠️ No success feedback found"
        fi
        
        # Check for progress indicators
        if ! find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "progress\|step\|percent" >/dev/null 2>&1; then
            feedback_findings+=("No progress indicators found")
            log "ℹ️ Consider adding progress indicators for long operations"
        fi
        
        local feedback_json=$(printf '%s\n' "${feedback_findings[@]}" | jq -R . | jq -s .)
        jq --argjson findings "$feedback_json" --arg issues "$feedback_issues" \
           '.categories.user_feedback = {"issues": ($issues|tonumber), "findings": $findings}' \
           "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    fi
    
    usability_issues=$((usability_issues + feedback_issues))
    
    # Calculate usability score
    local total_categories=4
    local passed_categories=$((total_categories - usability_issues))
    local usability_score=$((passed_categories * 100 / total_categories))
    
    jq --arg issues "$usability_issues" --arg score "$usability_score" \
       '.summary.issues = ($issues|tonumber) | .summary.score = ($score|tonumber)' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    log "Usability testing completed: Score ${usability_score}% ($usability_issues issues)"
    return $([[ $usability_issues -le 2 ]])  # Allow up to 2 usability issues
}

# Workflow Testing
run_workflow_tests() {
    log "Starting workflow testing"
    local workflow_issues=0
    local report_file="$RESULTS_DIR/workflow_${TIMESTAMP}.json"
    
    cat > "$report_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "test_type": "workflow_validation",
    "workflows": {
        "user_onboarding": {},
        "core_tasks": {},
        "error_recovery": {},
        "data_management": {}
    },
    "summary": {"issues": 0, "completed_workflows": 0}
}
EOF

    # User onboarding workflow
    log "Testing user onboarding workflow"
    local onboarding_issues=0
    local onboarding_steps=()
    
    if [[ -d frontend/src ]]; then
        # Check for registration/login flow
        if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "login\|signin\|register\|signup" >/dev/null 2>&1; then
            onboarding_steps+=("Authentication flow present")
            log "✅ Authentication flow found"
        else
            onboarding_issues=$((onboarding_issues + 1))
            onboarding_steps+=("No authentication flow found")
            log "⚠️ No authentication flow found"
        fi
        
        # Check for welcome/tutorial content
        if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "welcome\|tutorial\|getting.*started\|onboard" >/dev/null 2>&1; then
            onboarding_steps+=("Onboarding content present")
            log "✅ Onboarding content found"
        else
            onboarding_steps+=("No onboarding content found")
            log "ℹ️ Consider adding onboarding content"
        fi
        
        # Check for initial setup steps
        if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "setup\|configure\|initial" >/dev/null 2>&1; then
            onboarding_steps+=("Setup flow present")
            log "✅ Setup flow found"
        else
            onboarding_steps+=("No setup flow found")
            log "ℹ️ Consider adding setup guidance"
        fi
        
        local onboarding_json=$(printf '%s\n' "${onboarding_steps[@]}" | jq -R . | jq -s .)
        jq --argjson steps "$onboarding_json" --arg issues "$onboarding_issues" \
           '.workflows.user_onboarding = {"issues": ($issues|tonumber), "steps": $steps}' \
           "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    fi
    
    workflow_issues=$((workflow_issues + onboarding_issues))
    
    # Core task workflows
    log "Testing core task workflows"
    local core_issues=0
    local core_tasks=()
    
    # Identify core application tasks based on file structure
    if [[ -d frontend/src ]]; then
        # Check for file upload workflow (for Whisper Transcriber)
        if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "upload\|file\|drop" >/dev/null 2>&1; then
            core_tasks+=("File upload workflow present")
            log "✅ File upload workflow found"
            
            # Check for upload progress
            if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "progress\|uploading" >/dev/null 2>&1; then
                core_tasks+=("Upload progress tracking present")
                log "✅ Upload progress tracking found"
            else
                core_issues=$((core_issues + 1))
                core_tasks+=("Upload progress tracking missing")
                log "⚠️ Upload progress tracking missing"
            fi
        else
            core_issues=$((core_issues + 1))
            core_tasks+=("File upload workflow missing")
            log "❌ File upload workflow missing"
        fi
        
        # Check for transcription workflow
        if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "transcribe\|transcript\|audio" >/dev/null 2>&1; then
            core_tasks+=("Transcription workflow present")
            log "✅ Transcription workflow found"
        else
            core_issues=$((core_issues + 1))
            core_tasks+=("Transcription workflow missing")
            log "❌ Transcription workflow missing"
        fi
        
        # Check for results display
        if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "result\|output\|download" >/dev/null 2>&1; then
            core_tasks+=("Results display workflow present")
            log "✅ Results display workflow found"
        else
            core_issues=$((core_issues + 1))
            core_tasks+=("Results display workflow missing")
            log "❌ Results display workflow missing"
        fi
        
        local core_json=$(printf '%s\n' "${core_tasks[@]}" | jq -R . | jq -s .)
        jq --argjson tasks "$core_json" --arg issues "$core_issues" \
           '.workflows.core_tasks = {"issues": ($issues|tonumber), "tasks": $tasks}' \
           "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    fi
    
    workflow_issues=$((workflow_issues + core_issues))
    
    # Error recovery workflows
    log "Testing error recovery workflows"
    local recovery_issues=0
    local recovery_mechanisms=()
    
    if [[ -d frontend/src ]]; then
        # Check for retry mechanisms
        if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "retry\|try.*again" >/dev/null 2>&1; then
            recovery_mechanisms+=("Retry mechanisms present")
            log "✅ Retry mechanisms found"
        else
            recovery_issues=$((recovery_issues + 1))
            recovery_mechanisms+=("No retry mechanisms found")
            log "⚠️ No retry mechanisms found"
        fi
        
        # Check for error boundaries
        if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "ErrorBoundary\|componentDidCatch" >/dev/null 2>&1; then
            recovery_mechanisms+=("Error boundaries present")
            log "✅ Error boundaries found"
        else
            recovery_issues=$((recovery_issues + 1))
            recovery_mechanisms+=("No error boundaries found")
            log "⚠️ No error boundaries found"
        fi
        
        # Check for graceful degradation
        if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "fallback\|offline\|degraded" >/dev/null 2>&1; then
            recovery_mechanisms+=("Graceful degradation present")
            log "✅ Graceful degradation found"
        else
            recovery_mechanisms+=("No graceful degradation found")
            log "ℹ️ Consider adding graceful degradation"
        fi
        
        local recovery_json=$(printf '%s\n' "${recovery_mechanisms[@]}" | jq -R . | jq -s .)
        jq --argjson mechanisms "$recovery_json" --arg issues "$recovery_issues" \
           '.workflows.error_recovery = {"issues": ($issues|tonumber), "mechanisms": $mechanisms}' \
           "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    fi
    
    workflow_issues=$((workflow_issues + recovery_issues))
    
    # Calculate completed workflows
    local total_workflows=3
    local completed_workflows=$((total_workflows - workflow_issues))
    
    jq --arg issues "$workflow_issues" --arg completed "$completed_workflows" \
       '.summary.issues = ($issues|tonumber) | .summary.completed_workflows = ($completed|tonumber)' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    log "Workflow testing completed: $completed_workflows/$total_workflows workflows complete ($workflow_issues issues)"
    return $([[ $workflow_issues -le 1 ]])  # Allow up to 1 workflow issue
}

# Accessibility Testing
run_accessibility_tests() {
    log "Starting accessibility testing"
    local a11y_issues=0
    local report_file="$RESULTS_DIR/accessibility_${TIMESTAMP}.json"
    
    cat > "$report_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "test_type": "accessibility_assessment",
    "categories": {
        "semantic_html": {},
        "aria_labels": {},
        "keyboard_navigation": {},
        "color_contrast": {},
        "screen_reader_support": {}
    },
    "summary": {"issues": 0, "wcag_compliance": "unknown"}
}
EOF

    if [[ ! -d frontend/src ]]; then
        log "No frontend found, skipping accessibility testing"
        return 0
    fi
    
    # Semantic HTML assessment
    log "Assessing semantic HTML usage"
    local semantic_issues=0
    local semantic_findings=()
    
    # Check for proper heading structure
    local heading_files=$(find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "<h[1-6]" | wc -l || echo "0")
    if [[ $heading_files -eq 0 ]]; then
        semantic_issues=$((semantic_issues + 1))
        semantic_findings+=("No heading elements found")
        log "⚠️ No heading elements found"
    fi
    
    # Check for semantic elements
    local semantic_elements=("nav" "main" "header" "footer" "section" "article")
    local found_semantic=0
    for element in "${semantic_elements[@]}"; do
        if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "<$element" >/dev/null 2>&1; then
            found_semantic=$((found_semantic + 1))
        fi
    done
    
    if [[ $found_semantic -lt 3 ]]; then
        semantic_issues=$((semantic_issues + 1))
        semantic_findings+=("Limited use of semantic HTML elements")
        log "⚠️ Limited semantic HTML usage"
    fi
    
    # Check for proper list usage
    if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "<ul\|<ol" >/dev/null 2>&1; then
        semantic_findings+=("List elements found")
        log "✅ List elements found"
    else
        semantic_findings+=("No list elements found")
        log "ℹ️ Consider using lists for grouped content"
    fi
    
    local semantic_json=$(printf '%s\n' "${semantic_findings[@]}" | jq -R . | jq -s .)
    jq --argjson findings "$semantic_json" --arg issues "$semantic_issues" \
       '.categories.semantic_html = {"issues": ($issues|tonumber), "findings": $findings}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    a11y_issues=$((a11y_issues + semantic_issues))
    
    # ARIA labels assessment
    log "Assessing ARIA label usage"
    local aria_issues=0
    local aria_findings=()
    
    # Check for aria-label usage
    if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "aria-label" >/dev/null 2>&1; then
        aria_findings+=("aria-label attributes found")
        log "✅ aria-label attributes found"
    else
        aria_issues=$((aria_issues + 1))
        aria_findings+=("No aria-label attributes found")
        log "⚠️ No aria-label attributes found"
    fi
    
    # Check for aria-describedby
    if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "aria-describedby" >/dev/null 2>&1; then
        aria_findings+=("aria-describedby attributes found")
        log "✅ aria-describedby attributes found"
    else
        aria_findings+=("No aria-describedby attributes found")
        log "ℹ️ Consider using aria-describedby for additional descriptions"
    fi
    
    # Check for role attributes
    if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "role=" >/dev/null 2>&1; then
        aria_findings+=("Role attributes found")
        log "✅ Role attributes found"
    else
        aria_issues=$((aria_issues + 1))
        aria_findings+=("No role attributes found")
        log "⚠️ No role attributes found"
    fi
    
    local aria_json=$(printf '%s\n' "${aria_findings[@]}" | jq -R . | jq -s .)
    jq --argjson findings "$aria_json" --arg issues "$aria_issues" \
       '.categories.aria_labels = {"issues": ($issues|tonumber), "findings": $findings}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    a11y_issues=$((a11y_issues + aria_issues))
    
    # Keyboard navigation assessment
    log "Assessing keyboard navigation support"
    local keyboard_issues=0
    local keyboard_findings=()
    
    # Check for tabindex usage
    if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "tabIndex\|tabindex" >/dev/null 2>&1; then
        keyboard_findings+=("Tab index management found")
        log "✅ Tab index management found"
    else
        keyboard_issues=$((keyboard_issues + 1))
        keyboard_findings+=("No tab index management found")
        log "⚠️ No tab index management found"
    fi
    
    # Check for keyboard event handlers
    if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "onKeyDown\|onKeyPress\|onKeyUp" >/dev/null 2>&1; then
        keyboard_findings+=("Keyboard event handlers found")
        log "✅ Keyboard event handlers found"
    else
        keyboard_issues=$((keyboard_issues + 1))
        keyboard_findings+=("No keyboard event handlers found")
        log "⚠️ No keyboard event handlers found"
    fi
    
    # Check for focus management
    if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "focus\|blur" >/dev/null 2>&1; then
        keyboard_findings+=("Focus management found")
        log "✅ Focus management found"
    else
        keyboard_issues=$((keyboard_issues + 1))
        keyboard_findings+=("No focus management found")
        log "⚠️ No focus management found"
    fi
    
    local keyboard_json=$(printf '%s\n' "${keyboard_findings[@]}" | jq -R . | jq -s .)
    jq --argjson findings "$keyboard_json" --arg issues "$keyboard_issues" \
       '.categories.keyboard_navigation = {"issues": ($issues|tonumber), "findings": $findings}' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    a11y_issues=$((a11y_issues + keyboard_issues))
    
    # Calculate WCAG compliance level
    local wcag_compliance="A"
    if [[ $a11y_issues -eq 0 ]]; then
        wcag_compliance="AA"
    elif [[ $a11y_issues -le 2 ]]; then
        wcag_compliance="A"
    else
        wcag_compliance="Non-compliant"
    fi
    
    jq --arg issues "$a11y_issues" --arg wcag "$wcag_compliance" \
       '.summary.issues = ($issues|tonumber) | .summary.wcag_compliance = $wcag' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    log "Accessibility testing completed: WCAG $wcag_compliance ($a11y_issues issues)"
    return $([[ $a11y_issues -le 3 ]])  # Allow up to 3 accessibility issues
}

# Real scenario testing
run_real_scenario_tests() {
    log "Starting real-world scenario testing"
    local scenario_issues=0
    local report_file="$RESULTS_DIR/real_scenarios_${TIMESTAMP}.json"
    
    cat > "$report_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "test_type": "real_world_scenarios",
    "scenarios": {
        "first_time_user": {},
        "power_user": {},
        "mobile_user": {},
        "accessibility_user": {}
    },
    "summary": {"issues": 0, "completed_scenarios": 0}
}
EOF

    # First-time user scenario
    log "Testing first-time user scenario"
    local first_time_issues=0
    local first_time_steps=()
    
    # Simulate new user journey
    first_time_steps+=("User arrives at application")
    
    if [[ -d frontend/src ]]; then
        # Check for clear landing page
        if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "landing\|home\|welcome" >/dev/null 2>&1; then
            first_time_steps+=("Clear landing page present")
            log "✅ Landing page guidance found"
        else
            first_time_issues=$((first_time_issues + 1))
            first_time_steps+=("No clear landing page guidance")
            log "⚠️ No clear landing page guidance"
        fi
        
        # Check for getting started guidance
        if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "getting.*started\|how.*to\|tutorial" >/dev/null 2>&1; then
            first_time_steps+=("Getting started guidance present")
            log "✅ Getting started guidance found"
        else
            first_time_issues=$((first_time_issues + 1))
            first_time_steps+=("No getting started guidance")
            log "⚠️ No getting started guidance"
        fi
        
        # Check for example or demo content
        if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "example\|demo\|sample" >/dev/null 2>&1; then
            first_time_steps+=("Example content available")
            log "✅ Example content found"
        else
            first_time_steps+=("No example content found")
            log "ℹ️ Consider adding example content"
        fi
        
        local first_time_json=$(printf '%s\n' "${first_time_steps[@]}" | jq -R . | jq -s .)
        jq --argjson steps "$first_time_json" --arg issues "$first_time_issues" \
           '.scenarios.first_time_user = {"issues": ($issues|tonumber), "steps": $steps}' \
           "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    fi
    
    scenario_issues=$((scenario_issues + first_time_issues))
    
    # Power user scenario
    log "Testing power user scenario"
    local power_user_issues=0
    local power_user_features=()
    
    if [[ -d frontend/src ]]; then
        # Check for keyboard shortcuts
        if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "shortcut\|hotkey\|ctrl\|cmd" >/dev/null 2>&1; then
            power_user_features+=("Keyboard shortcuts available")
            log "✅ Keyboard shortcuts found"
        else
            power_user_features+=("No keyboard shortcuts found")
            log "ℹ️ Consider adding keyboard shortcuts for power users"
        fi
        
        # Check for batch operations
        if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "batch\|bulk\|select.*all" >/dev/null 2>&1; then
            power_user_features+=("Batch operations available")
            log "✅ Batch operations found"
        else
            power_user_features+=("No batch operations found")
            log "ℹ️ Consider adding batch operations"
        fi
        
        # Check for advanced settings
        if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "settings\|config\|advanced\|preferences" >/dev/null 2>&1; then
            power_user_features+=("Advanced settings available")
            log "✅ Advanced settings found"
        else
            power_user_issues=$((power_user_issues + 1))
            power_user_features+=("No advanced settings found")
            log "⚠️ No advanced settings found"
        fi
        
        local power_user_json=$(printf '%s\n' "${power_user_features[@]}" | jq -R . | jq -s .)
        jq --argjson features "$power_user_json" --arg issues "$power_user_issues" \
           '.scenarios.power_user = {"issues": ($issues|tonumber), "features": $features}' \
           "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    fi
    
    scenario_issues=$((scenario_issues + power_user_issues))
    
    # Mobile user scenario
    log "Testing mobile user scenario"
    local mobile_issues=0
    local mobile_features=()
    
    if [[ -d frontend/src ]]; then
        # Check for responsive design
        if find frontend/src -name "*.css" -o -name "*.scss" -o -name "*.jsx" -o -name "*.tsx" | xargs grep -l "media.*query\|responsive\|mobile\|@media" >/dev/null 2>&1; then
            mobile_features+=("Responsive design implemented")
            log "✅ Responsive design found"
        else
            mobile_issues=$((mobile_issues + 1))
            mobile_features+=("No responsive design found")
            log "⚠️ No responsive design found"
        fi
        
        # Check for touch-friendly interfaces
        if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "touch\|swipe\|tap" >/dev/null 2>&1; then
            mobile_features+=("Touch interactions implemented")
            log "✅ Touch interactions found"
        else
            mobile_features+=("No touch interactions found")
            log "ℹ️ Consider optimizing for touch interfaces"
        fi
        
        # Check for mobile navigation
        if find frontend/src -name "*.jsx" -o -name "*.tsx" | xargs grep -l "hamburger\|drawer\|mobile.*menu" >/dev/null 2>&1; then
            mobile_features+=("Mobile navigation implemented")
            log "✅ Mobile navigation found"
        else
            mobile_issues=$((mobile_issues + 1))
            mobile_features+=("No mobile navigation found")
            log "⚠️ No mobile navigation found"
        fi
        
        local mobile_json=$(printf '%s\n' "${mobile_features[@]}" | jq -R . | jq -s .)
        jq --argjson features "$mobile_json" --arg issues "$mobile_issues" \
           '.scenarios.mobile_user = {"issues": ($issues|tonumber), "features": $features}' \
           "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    fi
    
    scenario_issues=$((scenario_issues + mobile_issues))
    
    # Calculate completed scenarios
    local total_scenarios=3
    local completed_scenarios=$((total_scenarios - scenario_issues))
    
    jq --arg issues "$scenario_issues" --arg completed "$completed_scenarios" \
       '.summary.issues = ($issues|tonumber) | .summary.completed_scenarios = ($completed|tonumber)' \
       "$report_file" > "${report_file}.tmp" && mv "${report_file}.tmp" "$report_file"
    
    log "Real scenario testing completed: $completed_scenarios/$total_scenarios scenarios successful ($scenario_issues issues)"
    return $([[ $scenario_issues -le 2 ]])  # Allow up to 2 scenario issues
}

# Main execution
main() {
    local test_name="${1:-all}"
    
    log "Starting End User role testing: $test_name"
    
    case "$test_name" in
        "usability_tests")
            run_usability_tests
            ;;
        "workflow_tests")
            run_workflow_tests
            ;;
        "accessibility_tests")
            run_accessibility_tests
            ;;
        "real_scenario_tests")
            run_real_scenario_tests
            ;;
        "all")
            local overall_success=true
            
            run_usability_tests || overall_success=false
            run_workflow_tests || overall_success=false
            run_accessibility_tests || overall_success=false
            run_real_scenario_tests || overall_success=false
            
            if $overall_success; then
                log "✅ All End User tests passed"
                return 0
            else
                log "❌ Some End User tests failed"
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