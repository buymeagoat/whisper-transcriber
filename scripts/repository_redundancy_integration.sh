#!/bin/bash

# Repository Redundancy Analysis Integration Hub
# Orchestrates comprehensive redundancy analysis and cleanup workflow

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration
INTEGRATION_DIR="${REPO_ROOT}/logs/redundancy_integration"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p "$INTEGRATION_DIR"

# Logging
log() {
    echo "[Redundancy Integration] $*" | tee -a "$INTEGRATION_DIR/integration.log"
}

# Component scripts
REDUNDANCY_ANALYSIS_SCRIPT="$SCRIPT_DIR/repository_redundancy_analysis.sh"
DEDUPLICATION_SCRIPT="$SCRIPT_DIR/intelligent_deduplication.sh"
HEALTH_MONITORING_SCRIPT="$SCRIPT_DIR/repository_health_monitoring.sh"

# Validate component availability
validate_components() {
    log "Validating redundancy analysis components"
    
    local components_valid=true
    
    if [[ ! -x "$REDUNDANCY_ANALYSIS_SCRIPT" ]]; then
        log "❌ Repository redundancy analysis script not found or not executable: $REDUNDANCY_ANALYSIS_SCRIPT"
        components_valid=false
    fi
    
    if [[ ! -x "$DEDUPLICATION_SCRIPT" ]]; then
        log "❌ Intelligent deduplication script not found or not executable: $DEDUPLICATION_SCRIPT"
        components_valid=false
    fi
    
    if [[ ! -x "$HEALTH_MONITORING_SCRIPT" ]]; then
        log "❌ Repository health monitoring script not found or not executable: $HEALTH_MONITORING_SCRIPT"
        components_valid=false
    fi
    
    if $components_valid; then
        log "✅ All redundancy analysis components validated"
        return 0
    else
        log "❌ Component validation failed"
        return 1
    fi
}

# Complete redundancy analysis workflow
complete_redundancy_analysis() {
    local analysis_mode="${1:-comprehensive}"  # comprehensive, quick, focused
    local cleanup_mode="${2:-preview}"         # preview, safe, aggressive
    
    log "Starting complete redundancy analysis workflow"
    log "Analysis mode: $analysis_mode, Cleanup mode: $cleanup_mode"
    
    local workflow_file="$INTEGRATION_DIR/redundancy_workflow_${TIMESTAMP}.json"
    
    cat > "$workflow_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "workflow_type": "complete_redundancy_analysis",
    "analysis_mode": "$analysis_mode",
    "cleanup_mode": "$cleanup_mode",
    "phases": {
        "baseline_health": {"status": "pending", "start_time": null, "end_time": null, "exit_code": null},
        "redundancy_analysis": {"status": "pending", "start_time": null, "end_time": null, "exit_code": null},
        "intelligent_deduplication": {"status": "pending", "start_time": null, "end_time": null, "exit_code": null},
        "post_analysis_health": {"status": "pending", "start_time": null, "end_time": null, "exit_code": null},
        "effectiveness_monitoring": {"status": "pending", "start_time": null, "end_time": null, "exit_code": null}
    },
    "summary": {"total_phases": 5, "completed_phases": 0, "failed_phases": 0, "overall_success": false}
}
EOF

    local workflow_success=true
    local completed_phases=0
    local failed_phases=0
    
    # Phase 1: Baseline health assessment
    log "Phase 1: Baseline health assessment"
    local phase1_start=$(date -Iseconds)
    jq --arg start "$phase1_start" '.phases.baseline_health.status = "running" | .phases.baseline_health.start_time = $start' \
       "$workflow_file" > "${workflow_file}.tmp" && mv "${workflow_file}.tmp" "$workflow_file"
    
    local phase1_exit_code=0
    if "$HEALTH_MONITORING_SCRIPT" collect; then
        log "✅ Phase 1: Baseline health assessment completed"
        completed_phases=$((completed_phases + 1))
    else
        phase1_exit_code=$?
        log "❌ Phase 1: Baseline health assessment failed (exit code: $phase1_exit_code)"
        workflow_success=false
        failed_phases=$((failed_phases + 1))
    fi
    
    local phase1_end=$(date -Iseconds)
    jq --arg end "$phase1_end" --arg exit_code "$phase1_exit_code" \
       '.phases.baseline_health.status = "completed" | .phases.baseline_health.end_time = $end | .phases.baseline_health.exit_code = ($exit_code|tonumber)' \
       "$workflow_file" > "${workflow_file}.tmp" && mv "${workflow_file}.tmp" "$workflow_file"
    
    # Phase 2: Comprehensive redundancy analysis
    log "Phase 2: Comprehensive redundancy analysis"
    local phase2_start=$(date -Iseconds)
    jq --arg start "$phase2_start" '.phases.redundancy_analysis.status = "running" | .phases.redundancy_analysis.start_time = $start' \
       "$workflow_file" > "${workflow_file}.tmp" && mv "${workflow_file}.tmp" "$workflow_file"
    
    local phase2_exit_code=0
    if "$REDUNDANCY_ANALYSIS_SCRIPT" analyze; then
        log "✅ Phase 2: Redundancy analysis completed"
        completed_phases=$((completed_phases + 1))
    else
        phase2_exit_code=$?
        log "❌ Phase 2: Redundancy analysis failed (exit code: $phase2_exit_code)"
        workflow_success=false
        failed_phases=$((failed_phases + 1))
    fi
    
    local phase2_end=$(date -Iseconds)
    jq --arg end "$phase2_end" --arg exit_code "$phase2_exit_code" \
       '.phases.redundancy_analysis.status = "completed" | .phases.redundancy_analysis.end_time = $end | .phases.redundancy_analysis.exit_code = ($exit_code|tonumber)' \
       "$workflow_file" > "${workflow_file}.tmp" && mv "${workflow_file}.tmp" "$workflow_file"
    
    # Phase 3: Intelligent deduplication
    log "Phase 3: Intelligent deduplication"
    local phase3_start=$(date -Iseconds)
    jq --arg start "$phase3_start" '.phases.intelligent_deduplication.status = "running" | .phases.intelligent_deduplication.start_time = $start' \
       "$workflow_file" > "${workflow_file}.tmp" && mv "${workflow_file}.tmp" "$workflow_file"
    
    local dedup_confidence=85
    case "$analysis_mode" in
        "quick") dedup_confidence=90 ;;
        "comprehensive") dedup_confidence=85 ;;
        "focused") dedup_confidence=80 ;;
    esac
    
    local phase3_exit_code=0
    if "$DEDUPLICATION_SCRIPT" deduplicate "$cleanup_mode" "$dedup_confidence"; then
        log "✅ Phase 3: Intelligent deduplication completed"
        completed_phases=$((completed_phases + 1))
    else
        phase3_exit_code=$?
        log "❌ Phase 3: Intelligent deduplication failed (exit code: $phase3_exit_code)"
        workflow_success=false
        failed_phases=$((failed_phases + 1))
    fi
    
    local phase3_end=$(date -Iseconds)
    jq --arg end "$phase3_end" --arg exit_code "$phase3_exit_code" \
       '.phases.intelligent_deduplication.status = "completed" | .phases.intelligent_deduplication.end_time = $end | .phases.intelligent_deduplication.exit_code = ($exit_code|tonumber)' \
       "$workflow_file" > "${workflow_file}.tmp" && mv "${workflow_file}.tmp" "$workflow_file"
    
    # Phase 4: Post-analysis health assessment
    log "Phase 4: Post-analysis health assessment"
    local phase4_start=$(date -Iseconds)
    jq --arg start "$phase4_start" '.phases.post_analysis_health.status = "running" | .phases.post_analysis_health.start_time = $start' \
       "$workflow_file" > "${workflow_file}.tmp" && mv "${workflow_file}.tmp" "$workflow_file"
    
    local phase4_exit_code=0
    if "$HEALTH_MONITORING_SCRIPT" monitor; then
        log "✅ Phase 4: Post-analysis health assessment completed"
        completed_phases=$((completed_phases + 1))
    else
        phase4_exit_code=$?
        log "❌ Phase 4: Post-analysis health assessment failed (exit code: $phase4_exit_code)"
        workflow_success=false
        failed_phases=$((failed_phases + 1))
    fi
    
    local phase4_end=$(date -Iseconds)
    jq --arg end "$phase4_end" --arg exit_code "$phase4_exit_code" \
       '.phases.post_analysis_health.status = "completed" | .phases.post_analysis_health.end_time = $end | .phases.post_analysis_health.exit_code = ($exit_code|tonumber)' \
       "$workflow_file" > "${workflow_file}.tmp" && mv "${workflow_file}.tmp" "$workflow_file"
    
    # Phase 5: Effectiveness monitoring
    log "Phase 5: Effectiveness monitoring"
    local phase5_start=$(date -Iseconds)
    jq --arg start "$phase5_start" '.phases.effectiveness_monitoring.status = "running" | .phases.effectiveness_monitoring.start_time = $start' \
       "$workflow_file" > "${workflow_file}.tmp" && mv "${workflow_file}.tmp" "$workflow_file"
    
    local phase5_exit_code=0
    if "$DEDUPLICATION_SCRIPT" monitor; then
        log "✅ Phase 5: Effectiveness monitoring completed"
        completed_phases=$((completed_phases + 1))
    else
        phase5_exit_code=$?
        log "❌ Phase 5: Effectiveness monitoring failed (exit code: $phase5_exit_code)"
        workflow_success=false
        failed_phases=$((failed_phases + 1))
    fi
    
    local phase5_end=$(date -Iseconds)
    jq --arg end "$phase5_end" --arg exit_code "$phase5_exit_code" \
       '.phases.effectiveness_monitoring.status = "completed" | .phases.effectiveness_monitoring.end_time = $end | .phases.effectiveness_monitoring.exit_code = ($exit_code|tonumber)' \
       "$workflow_file" > "${workflow_file}.tmp" && mv "${workflow_file}.tmp" "$workflow_file"
    
    # Update workflow summary
    jq --arg completed "$completed_phases" --arg failed "$failed_phases" --arg success "$workflow_success" \
       '.summary.completed_phases = ($completed|tonumber) | .summary.failed_phases = ($failed|tonumber) | .summary.overall_success = ($success == "true")' \
       "$workflow_file" > "${workflow_file}.tmp" && mv "${workflow_file}.tmp" "$workflow_file"
    
    # Generate workflow summary
    log "Complete redundancy analysis workflow finished:"
    log "  Completed phases: $completed_phases/5"
    log "  Failed phases: $failed_phases"
    log "  Overall success: $workflow_success"
    log "  Workflow log: $workflow_file"
    
    if $workflow_success; then
        log "✅ All redundancy analysis phases completed successfully"
        return 0
    else
        log "❌ Redundancy analysis workflow completed with failures"
        return 1
    fi
}

# Quick redundancy scan
quick_redundancy_scan() {
    log "Starting quick redundancy scan"
    
    local scan_file="$INTEGRATION_DIR/quick_scan_${TIMESTAMP}.json"
    
    cat > "$scan_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "scan_type": "quick_redundancy",
    "findings": {
        "function_duplicates": 0,
        "documentation_duplicates": 0,
        "health_score": 0,
        "recommendations": []
    },
    "summary": {"scan_duration": 0, "issues_found": 0}
}
EOF

    local scan_start=$(date +%s)
    
    # Quick function redundancy check
    log "Quick function redundancy check"
    local py_functions=$(find "$REPO_ROOT" -name "*.py" -not -path "*/venv/*" -not -path "*/.git/*" | head -10 | xargs grep -l "^def " 2>/dev/null | wc -l)
    local js_functions=$(find "$REPO_ROOT" -name "*.js" -o -name "*.jsx" -not -path "*/node_modules/*" -not -path "*/.git/*" | head -10 | xargs grep -l "function\|const.*=>" 2>/dev/null | wc -l)
    
    # Estimate function duplicates (simplified)
    local total_functions=$((py_functions + js_functions))
    local estimated_duplicates=$((total_functions / 20))  # Rough estimate
    
    # Quick documentation check
    log "Quick documentation redundancy check"
    local md_files=$(find "$REPO_ROOT" -name "*.md" -not -path "*/.git/*" | wc -l)
    local duplicate_headers=$(find "$REPO_ROOT" -name "*.md" -not -path "*/.git/*" | xargs grep "^#" 2>/dev/null | cut -d: -f2- | sort | uniq -d | wc -l)
    
    # Quick health estimate
    local health_score=85  # Base estimate
    if [[ $estimated_duplicates -gt 5 ]]; then
        health_score=$((health_score - 10))
    fi
    if [[ $duplicate_headers -gt 3 ]]; then
        health_score=$((health_score - 5))
    fi
    
    local scan_end=$(date +%s)
    local scan_duration=$((scan_end - scan_start))
    local total_issues=$((estimated_duplicates + duplicate_headers))
    
    # Generate recommendations
    local recommendations=()
    if [[ $estimated_duplicates -gt 3 ]]; then
        recommendations+=("\"Run comprehensive redundancy analysis for function deduplication\"")
    fi
    if [[ $duplicate_headers -gt 2 ]]; then
        recommendations+=("\"Review documentation for duplicate sections\"")
    fi
    if [[ $health_score -lt 80 ]]; then
        recommendations+=("\"Consider running full analysis and cleanup workflow\"")
    fi
    if [[ ${#recommendations[@]} -eq 0 ]]; then
        recommendations+=("\"Repository appears healthy - continue regular monitoring\"")
    fi
    
    # Update scan results
    local recommendations_json=$(printf '%s\n' "${recommendations[@]}" | jq -s . 2>/dev/null || echo "[]")
    
    jq --arg function_duplicates "$estimated_duplicates" --arg doc_duplicates "$duplicate_headers" \
       --arg health_score "$health_score" --argjson recommendations "$recommendations_json" \
       --arg scan_duration "$scan_duration" --arg issues_found "$total_issues" \
       '.findings.function_duplicates = ($function_duplicates|tonumber) |
        .findings.documentation_duplicates = ($doc_duplicates|tonumber) |
        .findings.health_score = ($health_score|tonumber) |
        .findings.recommendations = $recommendations |
        .summary.scan_duration = ($scan_duration|tonumber) |
        .summary.issues_found = ($issues_found|tonumber)' \
       "$scan_file" > "${scan_file}.tmp" && mv "${scan_file}.tmp" "$scan_file"
    
    log "Quick redundancy scan completed in ${scan_duration}s"
    log "  Function duplicates (estimated): $estimated_duplicates"
    log "  Documentation duplicates: $duplicate_headers"
    log "  Health score (estimated): $health_score/100"
    log "  Total issues: $total_issues"
    log "  Scan results: $scan_file"
    
    return $([[ $total_issues -le 5 ]])
}

# Focused analysis on specific areas
focused_redundancy_analysis() {
    local focus_area="${1:-functions}"  # functions, documentation, security, all
    log "Starting focused redundancy analysis on: $focus_area"
    
    local focused_file="$INTEGRATION_DIR/focused_analysis_${focus_area}_${TIMESTAMP}.json"
    
    cat > "$focused_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "analysis_type": "focused_redundancy",
    "focus_area": "$focus_area",
    "results": {},
    "summary": {"analysis_duration": 0, "issues_found": 0, "actions_recommended": 0}
}
EOF

    local analysis_start=$(date +%s)
    local issues_found=0
    local actions_recommended=0
    
    case "$focus_area" in
        "functions")
            log "Focused analysis on function redundancy"
            if "$REDUNDANCY_ANALYSIS_SCRIPT" analyze > /dev/null 2>&1; then
                local latest_func_analysis=$(find "$REPO_ROOT/logs/redundancy_analysis" -name "function_redundancy_*.json" | sort | tail -1)
                if [[ -f "$latest_func_analysis" ]]; then
                    local func_redundancies=$(jq '.summary.redundant_functions // 0' "$latest_func_analysis")
                    issues_found=$func_redundancies
                    if [[ $func_redundancies -gt 3 ]]; then
                        actions_recommended=$((func_redundancies / 2))
                    fi
                    
                    jq --argjson func_analysis "$(cat "$latest_func_analysis")" \
                       '.results.function_analysis = $func_analysis' \
                       "$focused_file" > "${focused_file}.tmp" && mv "${focused_file}.tmp" "$focused_file"
                fi
            fi
            ;;
        "documentation")
            log "Focused analysis on documentation redundancy"
            if "$REDUNDANCY_ANALYSIS_SCRIPT" analyze > /dev/null 2>&1; then
                local latest_doc_analysis=$(find "$REPO_ROOT/logs/redundancy_analysis" -name "documentation_redundancy_*.json" | sort | tail -1)
                if [[ -f "$latest_doc_analysis" ]]; then
                    local doc_redundancies=$(jq '.summary.redundant_content // 0' "$latest_doc_analysis")
                    issues_found=$doc_redundancies
                    if [[ $doc_redundancies -gt 2 ]]; then
                        actions_recommended=$doc_redundancies
                    fi
                    
                    jq --argjson doc_analysis "$(cat "$latest_doc_analysis")" \
                       '.results.documentation_analysis = $doc_analysis' \
                       "$focused_file" > "${focused_file}.tmp" && mv "${focused_file}.tmp" "$focused_file"
                fi
            fi
            ;;
        "security")
            log "Focused analysis on security redundancy"
            if "$HEALTH_MONITORING_SCRIPT" collect > /dev/null 2>&1; then
                local latest_health=$(find "$REPO_ROOT/logs/metrics" -name "health_metrics_*.json" | sort | tail -1)
                if [[ -f "$latest_health" ]]; then
                    local security_issues=$(jq '.metrics.security.security_issues // 0' "$latest_health")
                    local security_score=$(jq '.metrics.security.overall_score // 0' "$latest_health")
                    issues_found=$security_issues
                    if [[ $security_score -lt 80 ]]; then
                        actions_recommended=$((security_issues / 2 + 1))
                    fi
                    
                    jq --argjson security_analysis "$(jq '.metrics.security' "$latest_health")" \
                       '.results.security_analysis = $security_analysis' \
                       "$focused_file" > "${focused_file}.tmp" && mv "${focused_file}.tmp" "$focused_file"
                fi
            fi
            ;;
        "all")
            log "Comprehensive focused analysis on all areas"
            complete_redundancy_analysis "focused" "preview"
            issues_found=10  # Placeholder
            actions_recommended=5
            ;;
    esac
    
    local analysis_end=$(date +%s)
    local analysis_duration=$((analysis_end - analysis_start))
    
    jq --arg duration "$analysis_duration" --arg issues "$issues_found" --arg actions "$actions_recommended" \
       '.summary.analysis_duration = ($duration|tonumber) |
        .summary.issues_found = ($issues|tonumber) |
        .summary.actions_recommended = ($actions|tonumber)' \
       "$focused_file" > "${focused_file}.tmp" && mv "${focused_file}.tmp" "$focused_file"
    
    log "Focused analysis on $focus_area completed in ${analysis_duration}s"
    log "  Issues found: $issues_found"
    log "  Actions recommended: $actions_recommended"
    log "  Analysis results: $focused_file"
    
    return $([[ $issues_found -le 3 ]])
}

# Generate integration status report
generate_integration_status() {
    log "Generating integration status report"
    
    local status_file="$INTEGRATION_DIR/integration_status_${TIMESTAMP}.md"
    
    cat > "$status_file" << EOF
# Repository Redundancy Analysis Integration Status

**Generated**: $(date)  
**Repository**: $(basename "$REPO_ROOT")  
**Integration Timestamp**: $TIMESTAMP

## 🔧 Component Status

### Available Components
EOF

    # Check component availability
    if [[ -x "$REDUNDANCY_ANALYSIS_SCRIPT" ]]; then
        echo "- ✅ **Repository Redundancy Analysis**: Available and executable" >> "$status_file"
    else
        echo "- ❌ **Repository Redundancy Analysis**: Not available or not executable" >> "$status_file"
    fi
    
    if [[ -x "$DEDUPLICATION_SCRIPT" ]]; then
        echo "- ✅ **Intelligent Deduplication**: Available and executable" >> "$status_file"
    else
        echo "- ❌ **Intelligent Deduplication**: Not available or not executable" >> "$status_file"
    fi
    
    if [[ -x "$HEALTH_MONITORING_SCRIPT" ]]; then
        echo "- ✅ **Repository Health Monitoring**: Available and executable" >> "$status_file"
    else
        echo "- ❌ **Repository Health Monitoring**: Not available or not executable" >> "$status_file"
    fi
    
    cat >> "$status_file" << EOF

## 📊 Recent Analysis Results

### Latest Workflow Runs
EOF

    # Check for recent workflow runs
    local recent_workflows=($(find "$INTEGRATION_DIR" -name "redundancy_workflow_*.json" | sort | tail -3))
    
    if [[ ${#recent_workflows[@]} -gt 0 ]]; then
        for workflow in "${recent_workflows[@]}"; do
            if [[ -f "$workflow" ]]; then
                local workflow_timestamp=$(jq -r '.timestamp' "$workflow")
                local workflow_success=$(jq -r '.summary.overall_success' "$workflow")
                local completed_phases=$(jq -r '.summary.completed_phases' "$workflow")
                local total_phases=$(jq -r '.summary.total_phases' "$workflow")
                
                if [[ "$workflow_success" == "true" ]]; then
                    echo "- ✅ **$workflow_timestamp**: $completed_phases/$total_phases phases completed successfully" >> "$status_file"
                else
                    echo "- ❌ **$workflow_timestamp**: $completed_phases/$total_phases phases completed (with failures)" >> "$status_file"
                fi
            fi
        done
    else
        echo "- ℹ️ No recent workflow runs found" >> "$status_file"
    fi
    
    cat >> "$status_file" << EOF

### Quick Scan Results
EOF

    # Check for recent quick scans
    local recent_scans=($(find "$INTEGRATION_DIR" -name "quick_scan_*.json" | sort | tail -3))
    
    if [[ ${#recent_scans[@]} -gt 0 ]]; then
        for scan in "${recent_scans[@]}"; do
            if [[ -f "$scan" ]]; then
                local scan_timestamp=$(basename "$scan" | sed 's/quick_scan_//;s/.json//')
                local issues_found=$(jq -r '.summary.issues_found' "$scan")
                local health_score=$(jq -r '.findings.health_score' "$scan")
                
                if [[ $issues_found -le 3 ]]; then
                    echo "- ✅ **$scan_timestamp**: $issues_found issues, health score $health_score/100" >> "$status_file"
                else
                    echo "- ⚠️ **$scan_timestamp**: $issues_found issues, health score $health_score/100" >> "$status_file"
                fi
            fi
        done
    else
        echo "- ℹ️ No recent quick scans found" >> "$status_file"
    fi
    
    cat >> "$status_file" << EOF

## 🎯 Integration Capabilities

### Available Workflows
- **Complete Analysis**: Full redundancy analysis with all phases
- **Quick Scan**: Fast overview of potential redundancy issues
- **Focused Analysis**: Targeted analysis on specific areas
- **Health Monitoring**: Continuous repository health tracking
- **Intelligent Deduplication**: Advanced consolidation with templates

### Workflow Modes
- **Comprehensive**: Full analysis with detailed reporting
- **Quick**: Fast scan for immediate insights
- **Focused**: Targeted analysis on specific components
- **Preview**: Show what would be done without making changes
- **Safe**: Conservative cleanup with backups
- **Aggressive**: More extensive automated cleanup

## 📈 Recommended Usage

### Daily Operations
\`\`\`bash
# Quick health check
$0 quick

# Focused analysis on functions
$0 focused functions
\`\`\`

### Weekly Maintenance
\`\`\`bash
# Complete analysis with preview
$0 complete comprehensive preview

# Health monitoring
$0 monitor
\`\`\`

### Monthly Cleanup
\`\`\`bash
# Complete analysis with safe cleanup
$0 complete comprehensive safe

# Generate status report
$0 status
\`\`\`

---

**Status Report Location**: \`$status_file\`  
*Generated by Repository Redundancy Analysis Integration Hub*
EOF

    log "✅ Integration status report generated: $status_file"
    echo "$status_file"
}

# Main execution
main() {
    local action="${1:-help}"
    local mode="${2:-comprehensive}"
    local cleanup="${3:-preview}"
    
    log "Repository Redundancy Analysis Integration Hub"
    log "Action: $action, Mode: $mode, Cleanup: $cleanup"
    
    # Validate components before executing
    if ! validate_components; then
        log "❌ Component validation failed - cannot proceed"
        return 1
    fi
    
    case "$action" in
        "complete")
            complete_redundancy_analysis "$mode" "$cleanup"
            ;;
        "quick")
            quick_redundancy_scan
            ;;
        "focused")
            local focus_area="${mode:-functions}"
            focused_redundancy_analysis "$focus_area"
            ;;
        "monitor")
            "$HEALTH_MONITORING_SCRIPT" monitor
            ;;
        "status")
            generate_integration_status
            ;;
        "validate")
            validate_components
            ;;
        "help"|*)
            cat << EOF
Repository Redundancy Analysis Integration Hub

Usage: $0 <action> [mode] [cleanup]

Actions:
  complete <mode> <cleanup>    Run complete redundancy analysis workflow
  quick                        Run quick redundancy scan
  focused <area>              Run focused analysis on specific area
  monitor                     Run health monitoring
  status                      Generate integration status report
  validate                    Validate component availability
  help                        Show this help

Modes for complete:
  comprehensive               Full detailed analysis (default)
  quick                       Fast analysis with reduced scope
  focused                     Targeted analysis

Areas for focused:
  functions                   Focus on function redundancy
  documentation               Focus on documentation redundancy
  security                    Focus on security-related redundancy
  all                         Comprehensive focused analysis

Cleanup modes:
  preview                     Show what would be done (default)
  safe                        Safe cleanup with backups
  aggressive                  More extensive automated cleanup

Examples:
  $0 complete                         # Complete analysis with preview
  $0 complete comprehensive safe      # Complete analysis with safe cleanup
  $0 quick                           # Quick redundancy scan
  $0 focused functions               # Focus on function redundancy
  $0 monitor                         # Health monitoring
  $0 status                          # Generate status report

Integration Features:
  - Orchestrates all redundancy analysis components
  - Provides unified workflow management
  - Generates comprehensive status reports
  - Supports various analysis modes and cleanup strategies
  - Includes effectiveness monitoring and trend analysis

EOF
            ;;
    esac
}

main "$@"