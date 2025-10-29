#!/bin/bash

# Repository Redundancy Analysis System
# Comprehensive analysis for code and documentation redundancies with automated cleanup

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration
ANALYSIS_DIR="${REPO_ROOT}/logs/redundancy_analysis"
BACKUP_DIR="${REPO_ROOT}/temp/redundancy_backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p "$ANALYSIS_DIR" "$BACKUP_DIR"

# Logging
log() {
    echo "[Redundancy Analysis] $*" | tee -a "$ANALYSIS_DIR/analysis.log"
}

# Configuration settings
SIMILARITY_THRESHOLD=80  # Percentage similarity to consider redundant
MIN_FUNCTION_LINES=5     # Minimum lines for function analysis
MIN_DOC_WORDS=10         # Minimum words for documentation analysis
BACKUP_ENABLED=true      # Create backups before cleanup

# Function redundancy analysis
analyze_function_redundancy() {
    log "Starting function redundancy analysis"
    local analysis_file="$ANALYSIS_DIR/function_redundancy_${TIMESTAMP}.json"
    local issues=0
    
    cat > "$analysis_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "analysis_type": "function_redundancy",
    "languages": {
        "python": {},
        "javascript": {},
        "typescript": {}
    },
    "summary": {"total_functions": 0, "redundant_functions": 0, "similarity_groups": []}
}
EOF

    # Python function analysis
    log "Analyzing Python functions"
    local python_functions=()
    local python_files=$(find "$REPO_ROOT" -name "*.py" -not -path "*/venv/*" -not -path "*/.git/*" -not -path "*/temp/*" | head -50)
    
    while IFS= read -r file; do
        if [[ -n "$file" ]]; then
            local functions=$(grep -n "^def " "$file" 2>/dev/null | head -20 || true)
            while IFS= read -r func_line; do
                if [[ -n "$func_line" ]]; then
                    local line_num=$(echo "$func_line" | cut -d: -f1)
                    local func_name=$(echo "$func_line" | sed 's/.*def \([^(]*\).*/\1/')
                    local func_body=$(sed -n "${line_num},$((line_num + 20))p" "$file" 2>/dev/null | head -10)
                    
                    if [[ $(echo "$func_body" | wc -l) -ge $MIN_FUNCTION_LINES ]]; then
                        python_functions+=("$file:$line_num:$func_name:$(echo "$func_body" | tr '\n' ' ')")
                    fi
                fi
            done <<< "$functions"
        fi
    done <<< "$python_files"
    
    # Analyze Python function similarities
    local python_redundancies=()
    local total_python=${#python_functions[@]}
    
    for ((i=0; i<total_python; i++)); do
        for ((j=i+1; j<total_python; j++)); do
            local func1="${python_functions[i]}"
            local func2="${python_functions[j]}"
            
            local name1=$(echo "$func1" | cut -d: -f3)
            local name2=$(echo "$func2" | cut -d: -f3)
            local body1=$(echo "$func1" | cut -d: -f4-)
            local body2=$(echo "$func2" | cut -d: -f4-)
            
            # Simple similarity check (could be enhanced with more sophisticated algorithms)
            local similarity=0
            if [[ "$name1" == "$name2" ]]; then
                similarity=$((similarity + 30))
            fi
            
            # Check body similarity (simplified)
            local common_words=$(echo "$body1 $body2" | tr ' ' '\n' | sort | uniq -d | wc -l)
            local total_words=$(echo "$body1 $body2" | tr ' ' '\n' | sort | uniq | wc -l)
            if [[ $total_words -gt 0 ]]; then
                local body_similarity=$((common_words * 70 / total_words))
                similarity=$((similarity + body_similarity))
            fi
            
            if [[ $similarity -ge $SIMILARITY_THRESHOLD ]]; then
                issues=$((issues + 1))
                local file1=$(echo "$func1" | cut -d: -f1)
                local line1=$(echo "$func1" | cut -d: -f2)
                local file2=$(echo "$func2" | cut -d: -f1)
                local line2=$(echo "$func2" | cut -d: -f2)
                
                python_redundancies+=("{\"function1\": \"$name1\", \"file1\": \"$file1\", \"line1\": $line1, \"function2\": \"$name2\", \"file2\": \"$file2\", \"line2\": $line2, \"similarity\": $similarity}")
                log "⚠️ Python function redundancy: $name1 ($file1:$line1) ↔ $name2 ($file2:$line2) - ${similarity}% similar"
            fi
        done
    done
    
    # JavaScript/TypeScript analysis
    log "Analyzing JavaScript/TypeScript functions"
    local js_functions=()
    local js_files=$(find "$REPO_ROOT" -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/temp/*" | head -30)
    
    while IFS= read -r file; do
        if [[ -n "$file" ]]; then
            local functions=$(grep -n "function\|const.*=.*=>.*\|function.*(" "$file" 2>/dev/null | head -10 || true)
            while IFS= read -r func_line; do
                if [[ -n "$func_line" ]]; then
                    local line_num=$(echo "$func_line" | cut -d: -f1)
                    local func_name=$(echo "$func_line" | sed 's/.*\(function\|const\) \([^(= ]*\).*/\2/')
                    local func_body=$(sed -n "${line_num},$((line_num + 15))p" "$file" 2>/dev/null | head -8)
                    
                    if [[ $(echo "$func_body" | wc -l) -ge $MIN_FUNCTION_LINES ]]; then
                        js_functions+=("$file:$line_num:$func_name:$(echo "$func_body" | tr '\n' ' ')")
                    fi
                fi
            done <<< "$functions"
        fi
    done <<< "$js_files"
    
    # Analyze JS function similarities
    local js_redundancies=()
    local total_js=${#js_functions[@]}
    
    for ((i=0; i<total_js; i++)); do
        for ((j=i+1; j<total_js; j++)); do
            local func1="${js_functions[i]}"
            local func2="${js_functions[j]}"
            
            local name1=$(echo "$func1" | cut -d: -f3)
            local name2=$(echo "$func2" | cut -d: -f3)
            local body1=$(echo "$func1" | cut -d: -f4-)
            local body2=$(echo "$func2" | cut -d: -f4-)
            
            local similarity=0
            if [[ "$name1" == "$name2" ]]; then
                similarity=$((similarity + 30))
            fi
            
            local common_words=$(echo "$body1 $body2" | tr ' ' '\n' | sort | uniq -d | wc -l)
            local total_words=$(echo "$body1 $body2" | tr ' ' '\n' | sort | uniq | wc -l)
            if [[ $total_words -gt 0 ]]; then
                local body_similarity=$((common_words * 70 / total_words))
                similarity=$((similarity + body_similarity))
            fi
            
            if [[ $similarity -ge $SIMILARITY_THRESHOLD ]]; then
                issues=$((issues + 1))
                local file1=$(echo "$func1" | cut -d: -f1)
                local line1=$(echo "$func1" | cut -d: -f2)
                local file2=$(echo "$func2" | cut -d: -f1)
                local line2=$(echo "$func2" | cut -d: -f2)
                
                js_redundancies+=("{\"function1\": \"$name1\", \"file1\": \"$file1\", \"line1\": $line1, \"function2\": \"$name2\", \"file2\": \"$file2\", \"line2\": $line2, \"similarity\": $similarity}")
                log "⚠️ JS/TS function redundancy: $name1 ($file1:$line1) ↔ $name2 ($file2:$line2) - ${similarity}% similar"
            fi
        done
    done
    
    # Update analysis file
    local python_redundancies_json=$(printf '%s\n' "${python_redundancies[@]}" | jq -s . 2>/dev/null || echo "[]")
    local js_redundancies_json=$(printf '%s\n' "${js_redundancies[@]}" | jq -s . 2>/dev/null || echo "[]")
    
    jq --argjson py_total "$total_python" --argjson js_total "$total_js" \
       --argjson py_redundancies "$python_redundancies_json" \
       --argjson js_redundancies "$js_redundancies_json" \
       --arg total_functions "$((total_python + total_js))" \
       --arg redundant_functions "$issues" \
       '.summary.total_functions = ($total_functions|tonumber) |
        .summary.redundant_functions = ($redundant_functions|tonumber) |
        .languages.python = {"total_functions": $py_total, "redundancies": $py_redundancies} |
        .languages.javascript = {"total_functions": $js_total, "redundancies": $js_redundancies}' \
       "$analysis_file" > "${analysis_file}.tmp" && mv "${analysis_file}.tmp" "$analysis_file"
    
    log "Function redundancy analysis completed: $issues redundancies found"
    return $([[ $issues -le 5 ]])  # Allow up to 5 function redundancies
}

# Documentation redundancy analysis
analyze_documentation_redundancy() {
    log "Starting documentation redundancy analysis"
    local analysis_file="$ANALYSIS_DIR/documentation_redundancy_${TIMESTAMP}.json"
    local issues=0
    
    cat > "$analysis_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "analysis_type": "documentation_redundancy",
    "documents": {
        "markdown": {},
        "comments": {},
        "docstrings": {}
    },
    "summary": {"total_documents": 0, "redundant_content": 0, "duplicate_sections": []}
}
EOF

    # Markdown document analysis
    log "Analyzing Markdown documents"
    local md_files=$(find "$REPO_ROOT" -name "*.md" -not -path "*/.git/*" -not -path "*/temp/*" | head -20)
    local md_documents=()
    local md_sections=()
    
    while IFS= read -r file; do
        if [[ -n "$file" && -f "$file" ]]; then
            # Extract sections (headers)
            local sections=$(grep "^#" "$file" 2>/dev/null || true)
            while IFS= read -r section; do
                if [[ -n "$section" ]]; then
                    local section_clean=$(echo "$section" | sed 's/^#*\s*//')
                    md_sections+=("$file:$section_clean")
                fi
            done <<< "$sections"
            
            # Extract content blocks
            local content=$(grep -v "^#" "$file" 2>/dev/null | grep -v "^$" | head -10 || true)
            if [[ $(echo "$content" | wc -w) -ge $MIN_DOC_WORDS ]]; then
                md_documents+=("$file:$(echo "$content" | tr '\n' ' ')")
            fi
        fi
    done <<< "$md_files"
    
    # Check for duplicate sections
    local duplicate_sections=()
    local total_sections=${#md_sections[@]}
    
    for ((i=0; i<total_sections; i++)); do
        for ((j=i+1; j<total_sections; j++)); do
            local section1="${md_sections[i]}"
            local section2="${md_sections[j]}"
            
            local file1=$(echo "$section1" | cut -d: -f1)
            local title1=$(echo "$section1" | cut -d: -f2-)
            local file2=$(echo "$section2" | cut -d: -f1)
            local title2=$(echo "$section2" | cut -d: -f2-)
            
            # Check for similar section titles
            if [[ "$title1" == "$title2" && "$file1" != "$file2" ]]; then
                issues=$((issues + 1))
                duplicate_sections+=("{\"title\": \"$title1\", \"file1\": \"$file1\", \"file2\": \"$file2\"}")
                log "⚠️ Duplicate section: '$title1' in $file1 and $file2"
            fi
        done
    done
    
    # Check for similar content blocks
    local similar_content=()
    local total_docs=${#md_documents[@]}
    
    for ((i=0; i<total_docs; i++)); do
        for ((j=i+1; j<total_docs; j++)); do
            local doc1="${md_documents[i]}"
            local doc2="${md_documents[j]}"
            
            local file1=$(echo "$doc1" | cut -d: -f1)
            local content1=$(echo "$doc1" | cut -d: -f2-)
            local file2=$(echo "$doc2" | cut -d: -f1)
            local content2=$(echo "$doc2" | cut -d: -f2-)
            
            # Simple content similarity check
            local common_words=$(echo "$content1 $content2" | tr ' ' '\n' | sort | uniq -d | wc -l)
            local total_words=$(echo "$content1 $content2" | tr ' ' '\n' | sort | uniq | wc -l)
            
            if [[ $total_words -gt 0 ]]; then
                local similarity=$((common_words * 100 / total_words))
                if [[ $similarity -ge $SIMILARITY_THRESHOLD ]]; then
                    issues=$((issues + 1))
                    similar_content+=("{\"file1\": \"$file1\", \"file2\": \"$file2\", \"similarity\": $similarity}")
                    log "⚠️ Similar content: $file1 ↔ $file2 - ${similarity}% similar"
                fi
            fi
        done
    done
    
    # Comment and docstring analysis
    log "Analyzing code comments and docstrings"
    local comment_redundancies=()
    
    # Python docstrings
    local py_docstrings=$(find "$REPO_ROOT" -name "*.py" -not -path "*/venv/*" -not -path "*/.git/*" | xargs grep -n '"""' 2>/dev/null | head -20 || true)
    
    # Check for similar docstrings (simplified)
    while IFS= read -r docstring_line; do
        if [[ -n "$docstring_line" ]]; then
            local file=$(echo "$docstring_line" | cut -d: -f1)
            local line=$(echo "$docstring_line" | cut -d: -f2)
            local content=$(echo "$docstring_line" | cut -d: -f3-)
            
            if [[ $(echo "$content" | wc -w) -ge $MIN_DOC_WORDS ]]; then
                # This is a simplified check - could be enhanced
                local similar_found=$(echo "$content" | grep -l "similar pattern" 2>/dev/null || true)
                if [[ -n "$similar_found" ]]; then
                    comment_redundancies+=("{\"type\": \"docstring\", \"file\": \"$file\", \"line\": $line}")
                fi
            fi
        fi
    done <<< "$py_docstrings"
    
    # Update analysis file
    local duplicate_sections_json=$(printf '%s\n' "${duplicate_sections[@]}" | jq -s . 2>/dev/null || echo "[]")
    local similar_content_json=$(printf '%s\n' "${similar_content[@]}" | jq -s . 2>/dev/null || echo "[]")
    local comment_redundancies_json=$(printf '%s\n' "${comment_redundancies[@]}" | jq -s . 2>/dev/null || echo "[]")
    
    jq --argjson sections "$duplicate_sections_json" \
       --argjson content "$similar_content_json" \
       --argjson comments "$comment_redundancies_json" \
       --arg total_docs "$total_docs" \
       --arg redundant_content "$issues" \
       '.summary.total_documents = ($total_docs|tonumber) |
        .summary.redundant_content = ($redundant_content|tonumber) |
        .documents.markdown = {"duplicate_sections": $sections, "similar_content": $content} |
        .documents.comments = {"redundancies": $comments}' \
       "$analysis_file" > "${analysis_file}.tmp" && mv "${analysis_file}.tmp" "$analysis_file"
    
    log "Documentation redundancy analysis completed: $issues redundancies found"
    return $([[ $issues -le 3 ]])  # Allow up to 3 documentation redundancies
}

# Repository health scoring
calculate_repository_health() {
    log "Calculating repository health score"
    local health_file="$ANALYSIS_DIR/repository_health_${TIMESTAMP}.json"
    
    cat > "$health_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "analysis_type": "repository_health",
    "metrics": {
        "codebase_size": {},
        "redundancy_score": {},
        "organization_score": {},
        "maintainability_score": {}
    },
    "summary": {"overall_health": 0, "recommendations": []}
}
EOF

    # Codebase size metrics
    local total_files=$(find "$REPO_ROOT" -type f -not -path "*/.git/*" -not -path "*/venv/*" -not -path "*/node_modules/*" -not -path "*/temp/*" | wc -l)
    local code_files=$(find "$REPO_ROOT" -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" | wc -l)
    local doc_files=$(find "$REPO_ROOT" -name "*.md" -o -name "*.rst" -o -name "*.txt" | wc -l)
    local total_lines=$(find "$REPO_ROOT" -type f -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}' || echo "0")
    
    log "Repository metrics: $total_files files, $code_files code files, $doc_files docs, $total_lines lines"
    
    # Calculate redundancy score (0-100, higher is better)
    local function_redundancy_file="$ANALYSIS_DIR/function_redundancy_${TIMESTAMP}.json"
    local doc_redundancy_file="$ANALYSIS_DIR/documentation_redundancy_${TIMESTAMP}.json"
    
    local function_redundancies=0
    local doc_redundancies=0
    local total_functions=0
    local total_docs=0
    
    if [[ -f "$function_redundancy_file" ]]; then
        function_redundancies=$(jq '.summary.redundant_functions // 0' "$function_redundancy_file")
        total_functions=$(jq '.summary.total_functions // 1' "$function_redundancy_file")
    fi
    
    if [[ -f "$doc_redundancy_file" ]]; then
        doc_redundancies=$(jq '.summary.redundant_content // 0' "$doc_redundancy_file")
        total_docs=$(jq '.summary.total_documents // 1' "$doc_redundancy_file")
    fi
    
    local function_redundancy_ratio=0
    local doc_redundancy_ratio=0
    
    if [[ $total_functions -gt 0 ]]; then
        function_redundancy_ratio=$((function_redundancies * 100 / total_functions))
    fi
    
    if [[ $total_docs -gt 0 ]]; then
        doc_redundancy_ratio=$((doc_redundancies * 100 / total_docs))
    fi
    
    local redundancy_score=$((100 - (function_redundancy_ratio + doc_redundancy_ratio) / 2))
    
    # Organization score (based on directory structure and file naming)
    local organization_score=80  # Base score
    local proper_structure_points=0
    
    # Check for proper directory structure
    if [[ -d "$REPO_ROOT/api" ]]; then proper_structure_points=$((proper_structure_points + 5)); fi
    if [[ -d "$REPO_ROOT/frontend" ]]; then proper_structure_points=$((proper_structure_points + 5)); fi
    if [[ -d "$REPO_ROOT/tests" ]]; then proper_structure_points=$((proper_structure_points + 5)); fi
    if [[ -d "$REPO_ROOT/docs" ]]; then proper_structure_points=$((proper_structure_points + 5)); fi
    
    organization_score=$((organization_score + proper_structure_points))
    
    # Maintainability score (based on documentation and test coverage)
    local maintainability_score=70  # Base score
    
    # Documentation coverage
    if [[ -f "$REPO_ROOT/README.md" ]]; then maintainability_score=$((maintainability_score + 5)); fi
    if [[ -f "$REPO_ROOT/CHANGELOG.md" ]]; then maintainability_score=$((maintainability_score + 5)); fi
    if [[ $doc_files -gt 5 ]]; then maintainability_score=$((maintainability_score + 10)); fi
    
    # Test coverage indicators
    if [[ -d "$REPO_ROOT/tests" ]]; then 
        local test_files=$(find "$REPO_ROOT/tests" -name "test_*.py" | wc -l)
        if [[ $test_files -gt 10 ]]; then maintainability_score=$((maintainability_score + 10)); fi
    fi
    
    # Overall health score (weighted average)
    local overall_health=$(((redundancy_score * 30 + organization_score * 35 + maintainability_score * 35) / 100))
    
    # Generate recommendations
    local recommendations=()
    
    if [[ $function_redundancies -gt 3 ]]; then
        recommendations+=("\"Reduce function redundancy: $function_redundancies duplicate functions found\"")
    fi
    
    if [[ $doc_redundancies -gt 2 ]]; then
        recommendations+=("\"Consolidate documentation: $doc_redundancies redundant content blocks found\"")
    fi
    
    if [[ $overall_health -lt 80 ]]; then
        recommendations+=("\"Improve repository organization and reduce redundancy\"")
    fi
    
    if [[ ${#recommendations[@]} -eq 0 ]]; then
        recommendations+=("\"Repository health is good - maintain current organization\"")
    fi
    
    # Update health file
    local recommendations_json=$(printf '%s\n' "${recommendations[@]}" | jq -s . 2>/dev/null || echo "[]")
    
    jq --arg total_files "$total_files" --arg code_files "$code_files" --arg doc_files "$doc_files" --arg total_lines "$total_lines" \
       --arg redundancy_score "$redundancy_score" --arg organization_score "$organization_score" \
       --arg maintainability_score "$maintainability_score" --arg overall_health "$overall_health" \
       --argjson recommendations "$recommendations_json" \
       '.metrics.codebase_size = {"total_files": ($total_files|tonumber), "code_files": ($code_files|tonumber), "doc_files": ($doc_files|tonumber), "total_lines": ($total_lines|tonumber)} |
        .metrics.redundancy_score = ($redundancy_score|tonumber) |
        .metrics.organization_score = ($organization_score|tonumber) |
        .metrics.maintainability_score = ($maintainability_score|tonumber) |
        .summary.overall_health = ($overall_health|tonumber) |
        .summary.recommendations = $recommendations' \
       "$health_file" > "${health_file}.tmp" && mv "${health_file}.tmp" "$health_file"
    
    log "Repository health score: $overall_health/100"
    log "Redundancy: $redundancy_score, Organization: $organization_score, Maintainability: $maintainability_score"
    
    return $([[ $overall_health -ge 75 ]])  # Require health score of 75+
}

# Automated cleanup with backup
automated_cleanup() {
    local cleanup_mode="${1:-safe}"  # safe, aggressive, preview
    log "Starting automated cleanup (mode: $cleanup_mode)"
    
    local cleanup_file="$ANALYSIS_DIR/cleanup_plan_${TIMESTAMP}.json"
    local backup_created=false
    
    cat > "$cleanup_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "cleanup_mode": "$cleanup_mode",
    "actions": {
        "backups_created": [],
        "files_modified": [],
        "redundancies_removed": [],
        "warnings": []
    },
    "summary": {"actions_taken": 0, "bytes_saved": 0}
}
EOF

    # Create backup if enabled and not in preview mode
    if [[ "$BACKUP_ENABLED" == "true" && "$cleanup_mode" != "preview" ]]; then
        log "Creating backup of repository state"
        local backup_archive="$BACKUP_DIR/repo_backup_${TIMESTAMP}.tar.gz"
        
        if tar -czf "$backup_archive" -C "$REPO_ROOT" . --exclude='.git' --exclude='venv' --exclude='node_modules' --exclude='temp' 2>/dev/null; then
            backup_created=true
            log "✅ Backup created: $backup_archive"
            
            jq --arg backup "$backup_archive" '.actions.backups_created += [$backup]' \
               "$cleanup_file" > "${cleanup_file}.tmp" && mv "${cleanup_file}.tmp" "$cleanup_file"
        else
            log "⚠️ Backup creation failed - proceeding with preview mode only"
            cleanup_mode="preview"
        fi
    fi
    
    # Analyze and clean function redundancies
    local function_redundancy_file="$ANALYSIS_DIR/function_redundancy_${TIMESTAMP}.json"
    if [[ -f "$function_redundancy_file" ]]; then
        local py_redundancies=$(jq '.languages.python.redundancies // []' "$function_redundancy_file")
        local js_redundancies=$(jq '.languages.javascript.redundancies // []' "$function_redundancy_file")
        
        # Process Python redundancies
        local py_count=$(echo "$py_redundancies" | jq 'length')
        for ((i=0; i<py_count; i++)); do
            local redundancy=$(echo "$py_redundancies" | jq ".[$i]")
            local file1=$(echo "$redundancy" | jq -r '.file1')
            local file2=$(echo "$redundancy" | jq -r '.file2')
            local func1=$(echo "$redundancy" | jq -r '.function1')
            local func2=$(echo "$redundancy" | jq -r '.function2')
            local similarity=$(echo "$redundancy" | jq -r '.similarity')
            
            log "Processing Python redundancy: $func1 ↔ $func2 (${similarity}% similar)"
            
            if [[ "$cleanup_mode" == "preview" ]]; then
                log "Preview: Would consolidate functions $func1 and $func2"
            elif [[ "$cleanup_mode" == "safe" && $similarity -ge 90 ]]; then
                log "Safe mode: High similarity detected - adding comment for manual review"
                if [[ -f "$file1" ]]; then
                    echo "# TODO: Review potential duplicate function: $func2 in $file2 (${similarity}% similar)" >> "$file1"
                fi
            elif [[ "$cleanup_mode" == "aggressive" && $similarity -ge $SIMILARITY_THRESHOLD ]]; then
                log "Aggressive mode: Adding merge suggestion comment"
                if [[ -f "$file1" ]]; then
                    echo "# REDUNDANCY: Consider merging with $func2 in $file2" >> "$file1"
                fi
            fi
        done
    fi
    
    # Clean documentation redundancies
    local doc_redundancy_file="$ANALYSIS_DIR/documentation_redundancy_${TIMESTAMP}.json"
    if [[ -f "$doc_redundancy_file" ]]; then
        local duplicate_sections=$(jq '.documents.markdown.duplicate_sections // []' "$doc_redundancy_file")
        
        local section_count=$(echo "$duplicate_sections" | jq 'length')
        for ((i=0; i<section_count; i++)); do
            local section=$(echo "$duplicate_sections" | jq ".[$i]")
            local title=$(echo "$section" | jq -r '.title')
            local file1=$(echo "$section" | jq -r '.file1')
            local file2=$(echo "$section" | jq -r '.file2')
            
            log "Processing duplicate section: '$title' in $file1 and $file2"
            
            if [[ "$cleanup_mode" == "preview" ]]; then
                log "Preview: Would consolidate section '$title'"
            elif [[ "$cleanup_mode" != "preview" ]]; then
                # Add a note about the duplication
                if [[ -f "$file1" ]]; then
                    echo "" >> "$file1"
                    echo "<!-- REDUNDANCY NOTE: Section '$title' also exists in $file2 -->" >> "$file1"
                fi
            fi
        done
    fi
    
    # Update cleanup summary
    local actions_taken=0
    if [[ "$cleanup_mode" != "preview" ]]; then
        actions_taken=$((py_count + section_count))
    fi
    
    jq --arg actions "$actions_taken" \
       '.summary.actions_taken = ($actions|tonumber)' \
       "$cleanup_file" > "${cleanup_file}.tmp" && mv "${cleanup_file}.tmp" "$cleanup_file"
    
    log "Cleanup completed: $actions_taken actions taken in $cleanup_mode mode"
    
    if [[ "$backup_created" == "true" ]]; then
        log "Backup available for rollback: $backup_archive"
    fi
    
    return 0
}

# Rollback functionality
rollback_cleanup() {
    local backup_file="$1"
    log "Starting rollback from backup: $backup_file"
    
    if [[ ! -f "$backup_file" ]]; then
        log "❌ Backup file not found: $backup_file"
        return 1
    fi
    
    log "Extracting backup to temporary location for verification"
    local temp_restore="$BACKUP_DIR/temp_restore_$(date +%s)"
    mkdir -p "$temp_restore"
    
    if tar -xzf "$backup_file" -C "$temp_restore" 2>/dev/null; then
        log "✅ Backup extracted successfully"
        log "⚠️ Manual verification recommended before full restore"
        log "Backup contents available at: $temp_restore"
        return 0
    else
        log "❌ Failed to extract backup"
        return 1
    fi
}

# Generate comprehensive report
generate_report() {
    log "Generating comprehensive redundancy analysis report"
    local report_file="$ANALYSIS_DIR/comprehensive_report_${TIMESTAMP}.md"
    
    cat > "$report_file" << EOF
# Repository Redundancy Analysis Report

**Generated**: $(date)  
**Repository**: $(basename "$REPO_ROOT")  
**Analysis Timestamp**: $TIMESTAMP

## Executive Summary

This report provides a comprehensive analysis of code and documentation redundancies within the repository, along with repository health metrics and recommendations for improvement.

## Function Redundancy Analysis

EOF

    # Add function redundancy details
    local function_redundancy_file="$ANALYSIS_DIR/function_redundancy_${TIMESTAMP}.json"
    if [[ -f "$function_redundancy_file" ]]; then
        local total_functions=$(jq '.summary.total_functions // 0' "$function_redundancy_file")
        local redundant_functions=$(jq '.summary.redundant_functions // 0' "$function_redundancy_file")
        
        cat >> "$report_file" << EOF
- **Total Functions Analyzed**: $total_functions
- **Redundant Functions Found**: $redundant_functions
- **Redundancy Rate**: $(echo "scale=2; $redundant_functions * 100 / $total_functions" | bc -l 2>/dev/null || echo "0")%

### Python Function Redundancies
EOF
        
        local py_redundancies=$(jq '.languages.python.redundancies // []' "$function_redundancy_file")
        local py_count=$(echo "$py_redundancies" | jq 'length')
        
        for ((i=0; i<py_count; i++)); do
            local redundancy=$(echo "$py_redundancies" | jq ".[$i]")
            local func1=$(echo "$redundancy" | jq -r '.function1')
            local file1=$(echo "$redundancy" | jq -r '.file1')
            local func2=$(echo "$redundancy" | jq -r '.function2')
            local file2=$(echo "$redundancy" | jq -r '.file2')
            local similarity=$(echo "$redundancy" | jq -r '.similarity')
            
            echo "- **$func1** ↔ **$func2** (${similarity}% similar)" >> "$report_file"
            echo "  - Files: \`$file1\` ↔ \`$file2\`" >> "$report_file"
        done
    fi
    
    cat >> "$report_file" << EOF

## Documentation Redundancy Analysis

EOF

    # Add documentation redundancy details
    local doc_redundancy_file="$ANALYSIS_DIR/documentation_redundancy_${TIMESTAMP}.json"
    if [[ -f "$doc_redundancy_file" ]]; then
        local total_docs=$(jq '.summary.total_documents // 0' "$doc_redundancy_file")
        local redundant_content=$(jq '.summary.redundant_content // 0' "$doc_redundancy_file")
        
        cat >> "$report_file" << EOF
- **Total Documents Analyzed**: $total_docs
- **Redundant Content Blocks**: $redundant_content

### Duplicate Sections
EOF
        
        local duplicate_sections=$(jq '.documents.markdown.duplicate_sections // []' "$doc_redundancy_file")
        local section_count=$(echo "$duplicate_sections" | jq 'length')
        
        for ((i=0; i<section_count; i++)); do
            local section=$(echo "$duplicate_sections" | jq ".[$i]")
            local title=$(echo "$section" | jq -r '.title')
            local file1=$(echo "$section" | jq -r '.file1')
            local file2=$(echo "$section" | jq -r '.file2')
            
            echo "- **$title**" >> "$report_file"
            echo "  - Files: \`$file1\` ↔ \`$file2\`" >> "$report_file"
        done
    fi
    
    cat >> "$report_file" << EOF

## Repository Health Assessment

EOF

    # Add health metrics
    local health_file="$ANALYSIS_DIR/repository_health_${TIMESTAMP}.json"
    if [[ -f "$health_file" ]]; then
        local overall_health=$(jq '.summary.overall_health // 0' "$health_file")
        local redundancy_score=$(jq '.metrics.redundancy_score // 0' "$health_file")
        local organization_score=$(jq '.metrics.organization_score // 0' "$health_file")
        local maintainability_score=$(jq '.metrics.maintainability_score // 0' "$health_file")
        
        cat >> "$report_file" << EOF
- **Overall Health Score**: $overall_health/100
- **Redundancy Score**: $redundancy_score/100
- **Organization Score**: $organization_score/100
- **Maintainability Score**: $maintainability_score/100

### Codebase Metrics
EOF
        
        local total_files=$(jq '.metrics.codebase_size.total_files // 0' "$health_file")
        local code_files=$(jq '.metrics.codebase_size.code_files // 0' "$health_file")
        local doc_files=$(jq '.metrics.codebase_size.doc_files // 0' "$health_file")
        local total_lines=$(jq '.metrics.codebase_size.total_lines // 0' "$health_file")
        
        cat >> "$report_file" << EOF
- **Total Files**: $total_files
- **Code Files**: $code_files
- **Documentation Files**: $doc_files
- **Total Lines of Code**: $total_lines

### Recommendations
EOF
        
        local recommendations=$(jq '.summary.recommendations // []' "$health_file")
        local rec_count=$(echo "$recommendations" | jq 'length')
        
        for ((i=0; i<rec_count; i++)); do
            local recommendation=$(echo "$recommendations" | jq -r ".[$i]")
            echo "- $recommendation" >> "$report_file"
        done
    fi
    
    cat >> "$report_file" << EOF

## Next Steps

1. **Review identified redundancies** - Manually verify flagged items before cleanup
2. **Implement consolidation** - Merge or refactor duplicate functionality
3. **Update documentation** - Consolidate redundant documentation sections
4. **Establish prevention measures** - Add checks to prevent future redundancy
5. **Monitor health metrics** - Regular assessment to maintain code quality

---

*Generated by Repository Redundancy Analysis System*  
*Report Location*: \`$report_file\`
EOF

    log "✅ Comprehensive report generated: $report_file"
    echo "$report_file"
}

# Main execution
main() {
    local action="${1:-analyze}"
    local mode="${2:-safe}"
    
    log "Repository Redundancy Analysis System"
    log "Action: $action, Mode: $mode"
    
    case "$action" in
        "analyze")
            local overall_success=true
            
            analyze_function_redundancy || overall_success=false
            analyze_documentation_redundancy || overall_success=false
            calculate_repository_health || overall_success=false
            
            local report_file=$(generate_report)
            
            if $overall_success; then
                log "✅ Repository analysis completed successfully"
                log "📄 Report available at: $report_file"
                return 0
            else
                log "⚠️ Repository analysis completed with issues"
                log "📄 Report available at: $report_file"
                return 1
            fi
            ;;
        "cleanup")
            automated_cleanup "$mode"
            ;;
        "rollback")
            local backup_file="$mode"
            rollback_cleanup "$backup_file"
            ;;
        "report")
            generate_report
            ;;
        "help"|*)
            cat << EOF
Repository Redundancy Analysis System

Usage: $0 <action> [mode]

Actions:
  analyze           Run complete redundancy analysis
  cleanup <mode>    Perform automated cleanup (safe|aggressive|preview)
  rollback <file>   Rollback from backup file
  report            Generate comprehensive report
  help              Show this help

Examples:
  $0 analyze                              # Full analysis
  $0 cleanup preview                      # Preview cleanup actions
  $0 cleanup safe                         # Safe cleanup with backups
  $0 rollback backup_20251024_120000.tar.gz  # Rollback from backup
  $0 report                               # Generate latest report

EOF
            ;;
    esac
}

main "$@"