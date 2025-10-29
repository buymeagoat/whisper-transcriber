#!/bin/bash

# Repository Health Monitoring System
# Continuous monitoring and alerting for repository health metrics

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration
HEALTH_DIR="${REPO_ROOT}/logs/health_monitoring"
METRICS_DIR="${REPO_ROOT}/logs/metrics"
ALERTS_DIR="${REPO_ROOT}/logs/alerts"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p "$HEALTH_DIR" "$METRICS_DIR" "$ALERTS_DIR"

# Logging
log() {
    echo "[Health Monitor] $*" | tee -a "$HEALTH_DIR/monitoring.log"
}

# Health thresholds
CRITICAL_HEALTH_THRESHOLD=50
WARNING_HEALTH_THRESHOLD=70
REDUNDANCY_WARNING_THRESHOLD=20
REDUNDANCY_CRITICAL_THRESHOLD=40

# Collect comprehensive health metrics
collect_health_metrics() {
    log "Collecting comprehensive health metrics"
    
    local metrics_file="$METRICS_DIR/health_metrics_${TIMESTAMP}.json"
    
    cat > "$metrics_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "collection_type": "comprehensive_health",
    "metrics": {
        "codebase": {},
        "redundancy": {},
        "quality": {},
        "security": {},
        "performance": {},
        "maintainability": {}
    },
    "trends": {},
    "alerts": []
}
EOF

    # Codebase metrics
    log "Collecting codebase metrics"
    local total_files=$(find "$REPO_ROOT" -type f -not -path "*/.git/*" -not -path "*/venv/*" -not -path "*/node_modules/*" -not -path "*/temp/*" | wc -l)
    local code_files=$(find "$REPO_ROOT" -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" | wc -l)
    local test_files=$(find "$REPO_ROOT" -name "test_*.py" -o -name "*.test.js" -o -name "*.spec.js" | wc -l)
    local doc_files=$(find "$REPO_ROOT" -name "*.md" -o -name "*.rst" | wc -l)
    local config_files=$(find "$REPO_ROOT" -name "*.json" -o -name "*.yml" -o -name "*.yaml" -o -name "*.toml" -o -name "*.ini" | wc -l)
    
    local total_lines=0
    local code_lines=0
    local comment_lines=0
    local blank_lines=0
    
    # Calculate line metrics for Python files
    local py_files=$(find "$REPO_ROOT" -name "*.py" -not -path "*/venv/*" | head -20)
    while IFS= read -r file; do
        if [[ -n "$file" && -f "$file" ]]; then
            local file_total=$(wc -l < "$file" 2>/dev/null || echo "0")
            local file_comments=$(grep -c "^\s*#" "$file" 2>/dev/null || echo "0")
            local file_blanks=$(grep -c "^\s*$" "$file" 2>/dev/null || echo "0")
            local file_code=$((file_total - file_comments - file_blanks))
            
            total_lines=$((total_lines + file_total))
            code_lines=$((code_lines + file_code))
            comment_lines=$((comment_lines + file_comments))
            blank_lines=$((blank_lines + file_blanks))
        fi
    done <<< "$py_files"
    
    # Code density metrics
    local code_density=0
    local comment_ratio=0
    if [[ $total_lines -gt 0 ]]; then
        code_density=$((code_lines * 100 / total_lines))
        comment_ratio=$((comment_lines * 100 / total_lines))
    fi
    
    # Test coverage estimation
    local test_coverage_estimate=0
    if [[ $code_files -gt 0 ]]; then
        test_coverage_estimate=$((test_files * 100 / code_files))
        if [[ $test_coverage_estimate -gt 100 ]]; then
            test_coverage_estimate=100
        fi
    fi
    
    # Update codebase metrics
    jq --arg total_files "$total_files" --arg code_files "$code_files" --arg test_files "$test_files" \
       --arg doc_files "$doc_files" --arg config_files "$config_files" \
       --arg total_lines "$total_lines" --arg code_lines "$code_lines" \
       --arg comment_lines "$comment_lines" --arg blank_lines "$blank_lines" \
       --arg code_density "$code_density" --arg comment_ratio "$comment_ratio" \
       --arg test_coverage "$test_coverage_estimate" \
       '.metrics.codebase = {
          "total_files": ($total_files|tonumber),
          "code_files": ($code_files|tonumber),
          "test_files": ($test_files|tonumber),
          "doc_files": ($doc_files|tonumber),
          "config_files": ($config_files|tonumber),
          "total_lines": ($total_lines|tonumber),
          "code_lines": ($code_lines|tonumber),
          "comment_lines": ($comment_lines|tonumber),
          "blank_lines": ($blank_lines|tonumber),
          "code_density": ($code_density|tonumber),
          "comment_ratio": ($comment_ratio|tonumber),
          "test_coverage_estimate": ($test_coverage|tonumber)
        }' "$metrics_file" > "${metrics_file}.tmp" && mv "${metrics_file}.tmp" "$metrics_file"
    
    # Redundancy metrics from latest analysis
    log "Collecting redundancy metrics"
    local latest_redundancy=$(find "$REPO_ROOT/logs/redundancy_analysis" -name "repository_health_*.json" | sort | tail -1)
    local redundancy_score=80  # Default
    local function_redundancies=0
    local doc_redundancies=0
    
    if [[ -f "$latest_redundancy" ]]; then
        redundancy_score=$(jq '.metrics.redundancy_score // 80' "$latest_redundancy")
        
        # Get detailed redundancy counts
        local latest_func_analysis=$(find "$REPO_ROOT/logs/redundancy_analysis" -name "function_redundancy_*.json" | sort | tail -1)
        local latest_doc_analysis=$(find "$REPO_ROOT/logs/redundancy_analysis" -name "documentation_redundancy_*.json" | sort | tail -1)
        
        if [[ -f "$latest_func_analysis" ]]; then
            function_redundancies=$(jq '.summary.redundant_functions // 0' "$latest_func_analysis")
        fi
        
        if [[ -f "$latest_doc_analysis" ]]; then
            doc_redundancies=$(jq '.summary.redundant_content // 0' "$latest_doc_analysis")
        fi
    fi
    
    jq --arg redundancy_score "$redundancy_score" --arg function_redundancies "$function_redundancies" \
       --arg doc_redundancies "$doc_redundancies" \
       '.metrics.redundancy = {
          "overall_score": ($redundancy_score|tonumber),
          "function_redundancies": ($function_redundancies|tonumber),
          "documentation_redundancies": ($doc_redundancies|tonumber)
        }' "$metrics_file" > "${metrics_file}.tmp" && mv "${metrics_file}.tmp" "$metrics_file"
    
    # Quality metrics
    log "Collecting quality metrics"
    local complexity_score=75  # Base score
    local maintainability_score=75
    
    # Calculate complexity based on file size distribution
    local large_files=$(find "$REPO_ROOT" -name "*.py" -size +1000c | wc -l)
    local very_large_files=$(find "$REPO_ROOT" -name "*.py" -size +5000c | wc -l)
    
    if [[ $code_files -gt 0 ]]; then
        local large_file_ratio=$((large_files * 100 / code_files))
        local very_large_ratio=$((very_large_files * 100 / code_files))
        
        # Penalize high ratios of large files
        complexity_score=$((complexity_score - large_file_ratio / 2 - very_large_ratio))
        if [[ $complexity_score -lt 0 ]]; then
            complexity_score=0
        fi
    fi
    
    # Maintainability based on documentation and structure
    if [[ $comment_ratio -gt 15 ]]; then
        maintainability_score=$((maintainability_score + 10))
    elif [[ $comment_ratio -lt 5 ]]; then
        maintainability_score=$((maintainability_score - 15))
    fi
    
    if [[ $doc_files -gt 5 ]]; then
        maintainability_score=$((maintainability_score + 10))
    elif [[ $doc_files -lt 2 ]]; then
        maintainability_score=$((maintainability_score - 10))
    fi
    
    if [[ $test_coverage_estimate -gt 50 ]]; then
        maintainability_score=$((maintainability_score + 15))
    elif [[ $test_coverage_estimate -lt 20 ]]; then
        maintainability_score=$((maintainability_score - 20))
    fi
    
    # Cap maintainability score
    if [[ $maintainability_score -gt 100 ]]; then
        maintainability_score=100
    elif [[ $maintainability_score -lt 0 ]]; then
        maintainability_score=0
    fi
    
    jq --arg complexity_score "$complexity_score" --arg maintainability_score "$maintainability_score" \
       '.metrics.quality = {
          "complexity_score": ($complexity_score|tonumber),
          "maintainability_score": ($maintainability_score|tonumber),
          "large_files": '$large_files',
          "very_large_files": '$very_large_files'
        }' "$metrics_file" > "${metrics_file}.tmp" && mv "${metrics_file}.tmp" "$metrics_file"
    
    # Security metrics
    log "Collecting security metrics"
    local security_score=85  # Base score
    local security_issues=0
    
    # Check for common security patterns
    local hardcoded_secrets=$(grep -r "password\|secret\|key.*=" "$REPO_ROOT" --include="*.py" --include="*.js" | grep -v ".git" | wc -l)
    local sql_patterns=$(grep -r "SELECT\|INSERT\|UPDATE.*%" "$REPO_ROOT" --include="*.py" | wc -l)
    local unsafe_imports=$(grep -r "import.*subprocess\|import.*os\|exec\|eval" "$REPO_ROOT" --include="*.py" | wc -l)
    
    security_issues=$((hardcoded_secrets + sql_patterns + unsafe_imports))
    
    # Adjust security score based on issues
    if [[ $security_issues -gt 10 ]]; then
        security_score=$((security_score - 30))
    elif [[ $security_issues -gt 5 ]]; then
        security_score=$((security_score - 15))
    elif [[ $security_issues -gt 0 ]]; then
        security_score=$((security_score - 5))
    fi
    
    jq --arg security_score "$security_score" --arg security_issues "$security_issues" \
       --arg hardcoded_secrets "$hardcoded_secrets" --arg sql_patterns "$sql_patterns" \
       --arg unsafe_imports "$unsafe_imports" \
       '.metrics.security = {
          "overall_score": ($security_score|tonumber),
          "security_issues": ($security_issues|tonumber),
          "hardcoded_secrets": ($hardcoded_secrets|tonumber),
          "sql_patterns": ($sql_patterns|tonumber),
          "unsafe_imports": ($unsafe_imports|tonumber)
        }' "$metrics_file" > "${metrics_file}.tmp" && mv "${metrics_file}.tmp" "$metrics_file"
    
    # Performance metrics
    log "Collecting performance metrics"
    local performance_score=80  # Base score
    
    # Check for performance anti-patterns
    local sync_db_calls=$(grep -r "session\.query\|db\.session" "$REPO_ROOT" --include="*.py" | wc -l)
    local nested_loops=$(grep -r "for.*for" "$REPO_ROOT" --include="*.py" | wc -l)
    local large_imports=$(grep -r "import \*" "$REPO_ROOT" --include="*.py" | wc -l)
    
    # Adjust performance score
    if [[ $sync_db_calls -gt 20 ]]; then
        performance_score=$((performance_score - 10))
    fi
    
    if [[ $nested_loops -gt 5 ]]; then
        performance_score=$((performance_score - 10))
    fi
    
    if [[ $large_imports -gt 10 ]]; then
        performance_score=$((performance_score - 5))
    fi
    
    jq --arg performance_score "$performance_score" --arg sync_db_calls "$sync_db_calls" \
       --arg nested_loops "$nested_loops" --arg large_imports "$large_imports" \
       '.metrics.performance = {
          "overall_score": ($performance_score|tonumber),
          "sync_db_calls": ($sync_db_calls|tonumber),
          "nested_loops": ($nested_loops|tonumber),
          "large_imports": ($large_imports|tonumber)
        }' "$metrics_file" > "${metrics_file}.tmp" && mv "${metrics_file}.tmp" "$metrics_file"
    
    # Calculate overall health score
    local overall_health=$(((redundancy_score * 25 + complexity_score * 20 + maintainability_score * 25 + security_score * 20 + performance_score * 10) / 100))
    
    jq --arg overall_health "$overall_health" \
       '.metrics.overall_health = ($overall_health|tonumber)' \
       "$metrics_file" > "${metrics_file}.tmp" && mv "${metrics_file}.tmp" "$metrics_file"
    
    log "Health metrics collected: Overall health $overall_health/100"
    echo "$metrics_file"
}

# Analyze health trends
analyze_health_trends() {
    log "Analyzing health trends"
    
    local trends_file="$HEALTH_DIR/health_trends_${TIMESTAMP}.json"
    
    # Get recent health metrics files
    local recent_metrics=($(find "$METRICS_DIR" -name "health_metrics_*.json" | sort | tail -5))
    
    if [[ ${#recent_metrics[@]} -lt 2 ]]; then
        log "⚠️ Insufficient data for trend analysis (need at least 2 data points)"
        return 1
    fi
    
    cat > "$trends_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "analysis_type": "health_trends",
    "timeframe": "${#recent_metrics[@]} recent measurements",
    "trends": {
        "overall_health": {},
        "redundancy": {},
        "quality": {},
        "security": {},
        "performance": {}
    },
    "predictions": {},
    "recommendations": []
}
EOF

    # Analyze overall health trend
    local health_values=()
    local redundancy_values=()
    local quality_values=()
    local security_values=()
    local performance_values=()
    
    for metrics_file in "${recent_metrics[@]}"; do
        if [[ -f "$metrics_file" ]]; then
            local health=$(jq '.metrics.overall_health // 0' "$metrics_file")
            local redundancy=$(jq '.metrics.redundancy.overall_score // 0' "$metrics_file")
            local quality=$(jq '.metrics.quality.maintainability_score // 0' "$metrics_file")
            local security=$(jq '.metrics.security.overall_score // 0' "$metrics_file")
            local performance=$(jq '.metrics.performance.overall_score // 0' "$metrics_file")
            
            health_values+=($health)
            redundancy_values+=($redundancy)
            quality_values+=($quality)
            security_values+=($security)
            performance_values+=($performance)
        fi
    done
    
    # Calculate trends (simple linear trend)
    calculate_trend() {
        local values=("$@")
        local n=${#values[@]}
        if [[ $n -lt 2 ]]; then
            echo "0"
            return
        fi
        
        local first=${values[0]}
        local last=${values[$((n-1))]}
        local trend=$((last - first))
        echo "$trend"
    }
    
    local health_trend=$(calculate_trend "${health_values[@]}")
    local redundancy_trend=$(calculate_trend "${redundancy_values[@]}")
    local quality_trend=$(calculate_trend "${quality_values[@]}")
    local security_trend=$(calculate_trend "${security_values[@]}")
    local performance_trend=$(calculate_trend "${performance_values[@]}")
    
    # Determine trend direction
    trend_direction() {
        local trend=$1
        if [[ $trend -gt 5 ]]; then
            echo "improving"
        elif [[ $trend -lt -5 ]]; then
            echo "declining"
        else
            echo "stable"
        fi
    }
    
    local health_direction=$(trend_direction $health_trend)
    local redundancy_direction=$(trend_direction $redundancy_trend)
    local quality_direction=$(trend_direction $quality_trend)
    local security_direction=$(trend_direction $security_trend)
    local performance_direction=$(trend_direction $performance_trend)
    
    # Update trends
    jq --arg health_trend "$health_trend" --arg health_direction "$health_direction" \
       --arg redundancy_trend "$redundancy_trend" --arg redundancy_direction "$redundancy_direction" \
       --arg quality_trend "$quality_trend" --arg quality_direction "$quality_direction" \
       --arg security_trend "$security_trend" --arg security_direction "$security_direction" \
       --arg performance_trend "$performance_trend" --arg performance_direction "$performance_direction" \
       '.trends.overall_health = {"change": ($health_trend|tonumber), "direction": $health_direction} |
        .trends.redundancy = {"change": ($redundancy_trend|tonumber), "direction": $redundancy_direction} |
        .trends.quality = {"change": ($quality_trend|tonumber), "direction": $quality_direction} |
        .trends.security = {"change": ($security_trend|tonumber), "direction": $security_direction} |
        .trends.performance = {"change": ($performance_trend|tonumber), "direction": $performance_direction}' \
       "$trends_file" > "${trends_file}.tmp" && mv "${trends_file}.tmp" "$trends_file"
    
    # Generate recommendations based on trends
    local recommendations=()
    
    if [[ "$health_direction" == "declining" ]]; then
        recommendations+=("\"Overall repository health is declining - investigate specific metrics\"")
    fi
    
    if [[ "$redundancy_direction" == "declining" ]]; then
        recommendations+=("\"Redundancy increasing - run deduplication analysis\"")
    fi
    
    if [[ "$quality_direction" == "declining" ]]; then
        recommendations+=("\"Code quality declining - review complexity and maintainability\"")
    fi
    
    if [[ "$security_direction" == "declining" ]]; then
        recommendations+=("\"Security metrics declining - audit security patterns\"")
    fi
    
    if [[ "$performance_direction" == "declining" ]]; then
        recommendations+=("\"Performance metrics declining - review performance anti-patterns\"")
    fi
    
    if [[ ${#recommendations[@]} -eq 0 ]]; then
        recommendations+=("\"Repository health trends are stable or improving\"")
    fi
    
    local recommendations_json=$(printf '%s\n' "${recommendations[@]}" | jq -s . 2>/dev/null || echo "[]")
    
    jq --argjson recommendations "$recommendations_json" \
       '.recommendations = $recommendations' \
       "$trends_file" > "${trends_file}.tmp" && mv "${trends_file}.tmp" "$trends_file"
    
    log "✅ Health trends analyzed: $trends_file"
    echo "$trends_file"
}

# Generate health alerts
generate_health_alerts() {
    local metrics_file="$1"
    log "Generating health alerts from $metrics_file"
    
    if [[ ! -f "$metrics_file" ]]; then
        log "❌ Metrics file not found: $metrics_file"
        return 1
    fi
    
    local alerts_file="$ALERTS_DIR/health_alerts_${TIMESTAMP}.json"
    
    cat > "$alerts_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "alert_type": "repository_health",
    "alerts": {
        "critical": [],
        "warning": [],
        "info": []
    },
    "summary": {"total_alerts": 0, "critical_count": 0, "warning_count": 0}
}
EOF

    local critical_alerts=()
    local warning_alerts=()
    local info_alerts=()
    
    # Get metrics
    local overall_health=$(jq '.metrics.overall_health // 0' "$metrics_file")
    local redundancy_score=$(jq '.metrics.redundancy.overall_score // 0' "$metrics_file")
    local security_score=$(jq '.metrics.security.overall_score // 0' "$metrics_file")
    local function_redundancies=$(jq '.metrics.redundancy.function_redundancies // 0' "$metrics_file")
    local doc_redundancies=$(jq '.metrics.redundancy.documentation_redundancies // 0' "$metrics_file")
    local security_issues=$(jq '.metrics.security.security_issues // 0' "$metrics_file")
    local test_coverage=$(jq '.metrics.codebase.test_coverage_estimate // 0' "$metrics_file")
    local comment_ratio=$(jq '.metrics.codebase.comment_ratio // 0' "$metrics_file")
    
    # Critical alerts
    if [[ $overall_health -lt $CRITICAL_HEALTH_THRESHOLD ]]; then
        critical_alerts+=("{\"type\": \"critical_health\", \"message\": \"Overall repository health is critically low: $overall_health/100\", \"metric\": \"overall_health\", \"value\": $overall_health, \"threshold\": $CRITICAL_HEALTH_THRESHOLD}")
    fi
    
    if [[ $function_redundancies -gt 10 ]]; then
        critical_alerts+=("{\"type\": \"high_redundancy\", \"message\": \"Excessive function redundancies detected: $function_redundancies functions\", \"metric\": \"function_redundancies\", \"value\": $function_redundancies, \"threshold\": 10}")
    fi
    
    if [[ $security_score -lt 60 ]]; then
        critical_alerts+=("{\"type\": \"security_risk\", \"message\": \"Security score is critically low: $security_score/100\", \"metric\": \"security_score\", \"value\": $security_score, \"threshold\": 60}")
    fi
    
    if [[ $security_issues -gt 15 ]]; then
        critical_alerts+=("{\"type\": \"security_issues\", \"message\": \"High number of security issues detected: $security_issues issues\", \"metric\": \"security_issues\", \"value\": $security_issues, \"threshold\": 15}")
    fi
    
    # Warning alerts
    if [[ $overall_health -lt $WARNING_HEALTH_THRESHOLD && $overall_health -ge $CRITICAL_HEALTH_THRESHOLD ]]; then
        warning_alerts+=("{\"type\": \"health_warning\", \"message\": \"Repository health below warning threshold: $overall_health/100\", \"metric\": \"overall_health\", \"value\": $overall_health, \"threshold\": $WARNING_HEALTH_THRESHOLD}")
    fi
    
    if [[ $redundancy_score -lt $REDUNDANCY_WARNING_THRESHOLD ]]; then
        warning_alerts+=("{\"type\": \"redundancy_warning\", \"message\": \"Redundancy score below threshold: $redundancy_score/100\", \"metric\": \"redundancy_score\", \"value\": $redundancy_score, \"threshold\": $REDUNDANCY_WARNING_THRESHOLD}")
    fi
    
    if [[ $function_redundancies -gt 5 && $function_redundancies -le 10 ]]; then
        warning_alerts+=("{\"type\": \"function_redundancy\", \"message\": \"Moderate function redundancies detected: $function_redundancies functions\", \"metric\": \"function_redundancies\", \"value\": $function_redundancies, \"threshold\": 5}")
    fi
    
    if [[ $doc_redundancies -gt 3 ]]; then
        warning_alerts+=("{\"type\": \"doc_redundancy\", \"message\": \"Documentation redundancies detected: $doc_redundancies sections\", \"metric\": \"doc_redundancies\", \"value\": $doc_redundancies, \"threshold\": 3}")
    fi
    
    if [[ $test_coverage -lt 30 ]]; then
        warning_alerts+=("{\"type\": \"low_test_coverage\", \"message\": \"Test coverage is low: $test_coverage%\", \"metric\": \"test_coverage\", \"value\": $test_coverage, \"threshold\": 30}")
    fi
    
    if [[ $comment_ratio -lt 10 ]]; then
        warning_alerts+=("{\"type\": \"low_documentation\", \"message\": \"Comment ratio is low: $comment_ratio%\", \"metric\": \"comment_ratio\", \"value\": $comment_ratio, \"threshold\": 10}")
    fi
    
    # Info alerts
    if [[ $overall_health -ge 90 ]]; then
        info_alerts+=("{\"type\": \"excellent_health\", \"message\": \"Repository health is excellent: $overall_health/100\", \"metric\": \"overall_health\", \"value\": $overall_health}")
    fi
    
    if [[ $redundancy_score -ge 90 ]]; then
        info_alerts+=("{\"type\": \"low_redundancy\", \"message\": \"Redundancy levels are optimal: $redundancy_score/100\", \"metric\": \"redundancy_score\", \"value\": $redundancy_score}")
    fi
    
    if [[ $test_coverage -ge 70 ]]; then
        info_alerts+=("{\"type\": \"good_test_coverage\", \"message\": \"Test coverage is good: $test_coverage%\", \"metric\": \"test_coverage\", \"value\": $test_coverage}")
    fi
    
    # Update alerts file
    local critical_json=$(printf '%s\n' "${critical_alerts[@]}" | jq -s . 2>/dev/null || echo "[]")
    local warning_json=$(printf '%s\n' "${warning_alerts[@]}" | jq -s . 2>/dev/null || echo "[]")
    local info_json=$(printf '%s\n' "${info_alerts[@]}" | jq -s . 2>/dev/null || echo "[]")
    
    local critical_count=${#critical_alerts[@]}
    local warning_count=${#warning_alerts[@]}
    local total_alerts=$((critical_count + warning_count + ${#info_alerts[@]}))
    
    jq --argjson critical "$critical_json" --argjson warning "$warning_json" --argjson info "$info_json" \
       --arg total_alerts "$total_alerts" --arg critical_count "$critical_count" --arg warning_count "$warning_count" \
       '.alerts.critical = $critical |
        .alerts.warning = $warning |
        .alerts.info = $info |
        .summary.total_alerts = ($total_alerts|tonumber) |
        .summary.critical_count = ($critical_count|tonumber) |
        .summary.warning_count = ($warning_count|tonumber)' \
       "$alerts_file" > "${alerts_file}.tmp" && mv "${alerts_file}.tmp" "$alerts_file"
    
    # Log alert summary
    log "Health alerts generated:"
    log "  Critical: $critical_count"
    log "  Warning: $warning_count"
    log "  Info: ${#info_alerts[@]}"
    log "  Total: $total_alerts"
    
    # Return alert status
    if [[ $critical_count -gt 0 ]]; then
        log "🚨 CRITICAL alerts detected - immediate attention required"
        return 2
    elif [[ $warning_count -gt 0 ]]; then
        log "⚠️ WARNING alerts detected - review recommended"
        return 1
    else
        log "✅ No critical issues detected"
        return 0
    fi
}

# Generate comprehensive health dashboard
generate_health_dashboard() {
    local metrics_file="$1"
    local trends_file="$2"
    local alerts_file="$3"
    
    log "Generating comprehensive health dashboard"
    
    local dashboard_file="$HEALTH_DIR/health_dashboard_${TIMESTAMP}.md"
    
    cat > "$dashboard_file" << EOF
# Repository Health Dashboard

**Generated**: $(date)  
**Repository**: $(basename "$REPO_ROOT")  
**Analysis Timestamp**: $TIMESTAMP

## 🎯 Overall Health Summary

EOF

    if [[ -f "$metrics_file" ]]; then
        local overall_health=$(jq '.metrics.overall_health // 0' "$metrics_file")
        local health_status=""
        local health_emoji=""
        
        if [[ $overall_health -ge 90 ]]; then
            health_status="Excellent"
            health_emoji="🟢"
        elif [[ $overall_health -ge 75 ]]; then
            health_status="Good"
            health_emoji="🟡"
        elif [[ $overall_health -ge 60 ]]; then
            health_status="Fair"
            health_emoji="🟠"
        else
            health_status="Poor"
            health_emoji="🔴"
        fi
        
        cat >> "$dashboard_file" << EOF
**Overall Health Score**: $health_emoji **$overall_health/100** ($health_status)

## 📊 Key Metrics

### Codebase Metrics
EOF

        local total_files=$(jq '.metrics.codebase.total_files // 0' "$metrics_file")
        local code_files=$(jq '.metrics.codebase.code_files // 0' "$metrics_file")
        local test_files=$(jq '.metrics.codebase.test_files // 0' "$metrics_file")
        local doc_files=$(jq '.metrics.codebase.doc_files // 0' "$metrics_file")
        local total_lines=$(jq '.metrics.codebase.total_lines // 0' "$metrics_file")
        local comment_ratio=$(jq '.metrics.codebase.comment_ratio // 0' "$metrics_file")
        local test_coverage=$(jq '.metrics.codebase.test_coverage_estimate // 0' "$metrics_file")
        
        cat >> "$dashboard_file" << EOF
- **Total Files**: $total_files
- **Code Files**: $code_files
- **Test Files**: $test_files
- **Documentation Files**: $doc_files
- **Total Lines of Code**: $total_lines
- **Comment Ratio**: $comment_ratio%
- **Test Coverage Estimate**: $test_coverage%

### Quality Metrics
EOF

        local redundancy_score=$(jq '.metrics.redundancy.overall_score // 0' "$metrics_file")
        local complexity_score=$(jq '.metrics.quality.complexity_score // 0' "$metrics_file")
        local maintainability_score=$(jq '.metrics.quality.maintainability_score // 0' "$metrics_file")
        local security_score=$(jq '.metrics.security.overall_score // 0' "$metrics_file")
        local performance_score=$(jq '.metrics.performance.overall_score // 0' "$metrics_file")
        
        cat >> "$dashboard_file" << EOF
- **Redundancy Score**: $redundancy_score/100
- **Complexity Score**: $complexity_score/100
- **Maintainability Score**: $maintainability_score/100
- **Security Score**: $security_score/100
- **Performance Score**: $performance_score/100

### Redundancy Analysis
EOF

        local function_redundancies=$(jq '.metrics.redundancy.function_redundancies // 0' "$metrics_file")
        local doc_redundancies=$(jq '.metrics.redundancy.documentation_redundancies // 0' "$metrics_file")
        
        cat >> "$dashboard_file" << EOF
- **Function Redundancies**: $function_redundancies
- **Documentation Redundancies**: $doc_redundancies

### Security Analysis
EOF

        local security_issues=$(jq '.metrics.security.security_issues // 0' "$metrics_file")
        local hardcoded_secrets=$(jq '.metrics.security.hardcoded_secrets // 0' "$metrics_file")
        local sql_patterns=$(jq '.metrics.security.sql_patterns // 0' "$metrics_file")
        local unsafe_imports=$(jq '.metrics.security.unsafe_imports // 0' "$metrics_file")
        
        cat >> "$dashboard_file" << EOF
- **Total Security Issues**: $security_issues
- **Hardcoded Secrets**: $hardcoded_secrets
- **SQL Patterns**: $sql_patterns
- **Unsafe Imports**: $unsafe_imports
EOF
    fi
    
    # Add trends section
    if [[ -f "$trends_file" ]]; then
        cat >> "$dashboard_file" << EOF

## 📈 Health Trends

EOF

        local health_direction=$(jq -r '.trends.overall_health.direction // "unknown"' "$trends_file")
        local health_change=$(jq '.trends.overall_health.change // 0' "$trends_file")
        local redundancy_direction=$(jq -r '.trends.redundancy.direction // "unknown"' "$trends_file")
        local quality_direction=$(jq -r '.trends.quality.direction // "unknown"' "$trends_file")
        local security_direction=$(jq -r '.trends.security.direction // "unknown"' "$trends_file")
        local performance_direction=$(jq -r '.trends.performance.direction // "unknown"' "$trends_file")
        
        # Convert direction to emoji
        direction_emoji() {
            case "$1" in
                "improving") echo "📈" ;;
                "declining") echo "📉" ;;
                "stable") echo "➡️" ;;
                *) echo "❓" ;;
            esac
        }
        
        cat >> "$dashboard_file" << EOF
- **Overall Health**: $(direction_emoji "$health_direction") $health_direction (${health_change:+0} points)
- **Redundancy**: $(direction_emoji "$redundancy_direction") $redundancy_direction
- **Quality**: $(direction_emoji "$quality_direction") $quality_direction
- **Security**: $(direction_emoji "$security_direction") $security_direction
- **Performance**: $(direction_emoji "$performance_direction") $performance_direction
EOF

        # Add trend recommendations
        local recommendations=$(jq -r '.recommendations[]' "$trends_file" 2>/dev/null || echo "")
        if [[ -n "$recommendations" ]]; then
            cat >> "$dashboard_file" << EOF

### Trend Recommendations
EOF
            while IFS= read -r recommendation; do
                if [[ -n "$recommendation" ]]; then
                    echo "- $recommendation" >> "$dashboard_file"
                fi
            done <<< "$recommendations"
        fi
    fi
    
    # Add alerts section
    if [[ -f "$alerts_file" ]]; then
        cat >> "$dashboard_file" << EOF

## 🚨 Health Alerts

EOF

        local critical_count=$(jq '.summary.critical_count // 0' "$alerts_file")
        local warning_count=$(jq '.summary.warning_count // 0' "$alerts_file")
        local total_alerts=$(jq '.summary.total_alerts // 0' "$alerts_file")
        
        cat >> "$dashboard_file" << EOF
**Alert Summary**: $total_alerts total alerts ($critical_count critical, $warning_count warnings)

EOF

        # Critical alerts
        if [[ $critical_count -gt 0 ]]; then
            cat >> "$dashboard_file" << EOF
### 🔴 Critical Alerts
EOF
            local critical_alerts=$(jq -r '.alerts.critical[].message' "$alerts_file" 2>/dev/null || echo "")
            while IFS= read -r alert; do
                if [[ -n "$alert" ]]; then
                    echo "- 🚨 $alert" >> "$dashboard_file"
                fi
            done <<< "$critical_alerts"
            echo "" >> "$dashboard_file"
        fi
        
        # Warning alerts
        if [[ $warning_count -gt 0 ]]; then
            cat >> "$dashboard_file" << EOF
### 🟡 Warning Alerts
EOF
            local warning_alerts=$(jq -r '.alerts.warning[].message' "$alerts_file" 2>/dev/null || echo "")
            while IFS= read -r alert; do
                if [[ -n "$alert" ]]; then
                    echo "- ⚠️ $alert" >> "$dashboard_file"
                fi
            done <<< "$warning_alerts"
            echo "" >> "$dashboard_file"
        fi
        
        # Info alerts
        local info_alerts=$(jq -r '.alerts.info[].message' "$alerts_file" 2>/dev/null || echo "")
        if [[ -n "$info_alerts" ]]; then
            cat >> "$dashboard_file" << EOF
### ℹ️ Information
EOF
            while IFS= read -r alert; do
                if [[ -n "$alert" ]]; then
                    echo "- ✅ $alert" >> "$dashboard_file"
                fi
            done <<< "$info_alerts"
            echo "" >> "$dashboard_file"
        fi
    fi
    
    cat >> "$dashboard_file" << EOF

## 🎯 Action Items

### Immediate Actions Required
- Review critical alerts and address high-priority issues
- Run deduplication analysis if redundancy levels are high
- Address security vulnerabilities if security score is low

### Regular Maintenance
- Monitor health trends weekly
- Run comprehensive analysis monthly
- Update documentation and improve test coverage
- Review and refactor code with high complexity scores

### Optimization Opportunities
- Consolidate redundant functions and documentation
- Improve code documentation and comments
- Enhance test coverage for better maintainability
- Optimize performance bottlenecks

---

**Dashboard Location**: \`$dashboard_file\`  
**Next Update**: $(date -d '+1 week')  
*Generated by Repository Health Monitoring System*
EOF

    log "✅ Health dashboard generated: $dashboard_file"
    echo "$dashboard_file"
}

# Main execution
main() {
    local action="${1:-monitor}"
    local interval="${2:-3600}"  # Default 1 hour
    
    log "Repository Health Monitoring System"
    log "Action: $action, Interval: $interval seconds"
    
    case "$action" in
        "monitor")
            log "Starting comprehensive health monitoring"
            
            local metrics_file=$(collect_health_metrics)
            local trends_file=$(analyze_health_trends)
            local alerts_exit_code=0
            
            generate_health_alerts "$metrics_file" || alerts_exit_code=$?
            
            local alerts_file="$ALERTS_DIR/health_alerts_${TIMESTAMP}.json"
            local dashboard_file=$(generate_health_dashboard "$metrics_file" "$trends_file" "$alerts_file")
            
            log "✅ Health monitoring completed"
            log "📄 Dashboard: $dashboard_file"
            
            return $alerts_exit_code
            ;;
        "watch")
            log "Starting continuous health monitoring (interval: ${interval}s)"
            while true; do
                log "Running health check..."
                main "monitor"
                log "Waiting $interval seconds until next check..."
                sleep "$interval"
            done
            ;;
        "collect")
            collect_health_metrics
            ;;
        "trends")
            analyze_health_trends
            ;;
        "alerts")
            local metrics_file="${2:-$(find "$METRICS_DIR" -name "health_metrics_*.json" | sort | tail -1)}"
            generate_health_alerts "$metrics_file"
            ;;
        "dashboard")
            local metrics_file="${2:-$(find "$METRICS_DIR" -name "health_metrics_*.json" | sort | tail -1)}"
            local trends_file="${3:-$(find "$HEALTH_DIR" -name "health_trends_*.json" | sort | tail -1)}"
            local alerts_file="${4:-$(find "$ALERTS_DIR" -name "health_alerts_*.json" | sort | tail -1)}"
            generate_health_dashboard "$metrics_file" "$trends_file" "$alerts_file"
            ;;
        "help"|*)
            cat << EOF
Repository Health Monitoring System

Usage: $0 <action> [options]

Actions:
  monitor                         Run complete health monitoring cycle
  watch [interval]               Continuous monitoring (default: 3600s)
  collect                        Collect health metrics only
  trends                         Analyze health trends only
  alerts [metrics_file]          Generate alerts from metrics
  dashboard [metrics] [trends] [alerts]  Generate dashboard
  help                           Show this help

Examples:
  $0 monitor                     # Complete health check
  $0 watch 1800                  # Monitor every 30 minutes
  $0 collect                     # Collect metrics only
  $0 dashboard                   # Generate dashboard with latest data

EOF
            ;;
    esac
}

main "$@"