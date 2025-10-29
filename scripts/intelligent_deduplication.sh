#!/bin/bash

# Intelligent Deduplication Service
# Advanced consolidation system for code and documentation redundancies

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration
DEDUP_DIR="${REPO_ROOT}/logs/deduplication"
BACKUP_DIR="${REPO_ROOT}/temp/deduplication_backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p "$DEDUP_DIR" "$BACKUP_DIR"

# Logging
log() {
    echo "[Deduplication] $*" | tee -a "$DEDUP_DIR/deduplication.log"
}

# Advanced similarity algorithm with semantic analysis
calculate_semantic_similarity() {
    local text1="$1"
    local text2="$2"
    local similarity_type="${3:-code}"  # code, documentation, structure
    
    # Normalize text for comparison
    local norm1=$(echo "$text1" | tr '[:upper:]' '[:lower:]' | sed 's/[[:space:]]\+/ /g' | tr -d '[:punct:]')
    local norm2=$(echo "$text2" | tr '[:upper:]' '[:lower:]' | sed 's/[[:space:]]\+/ /g' | tr -d '[:punct:]')
    
    # Calculate different similarity metrics
    local lexical_similarity=0
    local structural_similarity=0
    local semantic_similarity=0
    
    # Lexical similarity (word overlap)
    local words1=($(echo "$norm1" | tr ' ' '\n'))
    local words2=($(echo "$norm2" | tr ' ' '\n'))
    local common_words=0
    local total_unique_words=0
    
    # Create word frequency maps
    declare -A freq1 freq2 all_words
    for word in "${words1[@]}"; do
        freq1["$word"]=$((${freq1["$word"]:-0} + 1))
        all_words["$word"]=1
    done
    
    for word in "${words2[@]}"; do
        freq2["$word"]=$((${freq2["$word"]:-0} + 1))
        all_words["$word"]=1
    done
    
    total_unique_words=${#all_words[@]}
    
    # Calculate common words weighted by frequency
    for word in "${!all_words[@]}"; do
        local freq_1=${freq1["$word"]:-0}
        local freq_2=${freq2["$word"]:-0}
        if [[ $freq_1 -gt 0 && $freq_2 -gt 0 ]]; then
            common_words=$((common_words + 1))
        fi
    done
    
    if [[ $total_unique_words -gt 0 ]]; then
        lexical_similarity=$((common_words * 100 / total_unique_words))
    fi
    
    # Structural similarity (for code)
    if [[ "$similarity_type" == "code" ]]; then
        # Extract structural elements
        local structure1=$(echo "$text1" | grep -o '\(def\|class\|function\|if\|for\|while\|try\|catch\)' | sort | uniq -c | tr '\n' ' ')
        local structure2=$(echo "$text2" | grep -o '\(def\|class\|function\|if\|for\|while\|try\|catch\)' | sort | uniq -c | tr '\n' ' ')
        
        if [[ "$structure1" == "$structure2" ]]; then
            structural_similarity=100
        elif [[ -n "$structure1" && -n "$structure2" ]]; then
            # Calculate structural overlap
            local struct_words1=($(echo "$structure1"))
            local struct_words2=($(echo "$structure2"))
            local struct_common=0
            local struct_total=${#struct_words1[@]}
            
            if [[ ${#struct_words2[@]} -gt $struct_total ]]; then
                struct_total=${#struct_words2[@]}
            fi
            
            for word in "${struct_words1[@]}"; do
                if [[ " ${struct_words2[*]} " =~ " $word " ]]; then
                    struct_common=$((struct_common + 1))
                fi
            done
            
            if [[ $struct_total -gt 0 ]]; then
                structural_similarity=$((struct_common * 100 / struct_total))
            fi
        fi
    fi
    
    # Semantic similarity (context-based)
    if [[ "$similarity_type" == "documentation" ]]; then
        # Look for common documentation patterns
        local doc_patterns1=$(echo "$text1" | grep -o '\(TODO\|FIXME\|NOTE\|WARNING\|DEPRECATED\|Example\|Usage\|Parameters\|Returns\)' | sort | uniq | tr '\n' ' ')
        local doc_patterns2=$(echo "$text2" | grep -o '\(TODO\|FIXME\|NOTE\|WARNING\|DEPRECATED\|Example\|Usage\|Parameters\|Returns\)' | sort | uniq | tr '\n' ' ')
        
        if [[ -n "$doc_patterns1" && -n "$doc_patterns2" ]]; then
            local pattern_words1=($doc_patterns1)
            local pattern_words2=($doc_patterns2)
            local pattern_common=0
            local pattern_total=${#pattern_words1[@]}
            
            if [[ ${#pattern_words2[@]} -gt $pattern_total ]]; then
                pattern_total=${#pattern_words2[@]}
            fi
            
            for pattern in "${pattern_words1[@]}"; do
                if [[ " ${pattern_words2[*]} " =~ " $pattern " ]]; then
                    pattern_common=$((pattern_common + 1))
                fi
            done
            
            if [[ $pattern_total -gt 0 ]]; then
                semantic_similarity=$((pattern_common * 100 / pattern_total))
            fi
        fi
    fi
    
    # Calculate weighted final similarity
    local final_similarity=0
    case "$similarity_type" in
        "code")
            final_similarity=$(((lexical_similarity * 40 + structural_similarity * 50 + semantic_similarity * 10) / 100))
            ;;
        "documentation")
            final_similarity=$(((lexical_similarity * 50 + semantic_similarity * 40 + structural_similarity * 10) / 100))
            ;;
        "structure")
            final_similarity=$(((structural_similarity * 60 + lexical_similarity * 30 + semantic_similarity * 10) / 100))
            ;;
        *)
            final_similarity=$lexical_similarity
            ;;
    esac
    
    echo "$final_similarity"
}

# Create merge template for duplicate functions
create_function_merge_template() {
    local func1_file="$1"
    local func1_line="$2"
    local func1_name="$3"
    local func2_file="$4"
    local func2_line="$5"
    local func2_name="$6"
    local similarity="$7"
    
    local template_file="$DEDUP_DIR/merge_template_${func1_name}_${TIMESTAMP}.md"
    
    cat > "$template_file" << EOF
# Function Merge Template

## Duplicate Functions Detected

**Similarity Score**: ${similarity}%
**Merge Recommendation**: $([[ $similarity -gt 90 ]] && echo "HIGH PRIORITY" || echo "REVIEW REQUIRED")

### Function 1: \`$func1_name\`
- **File**: \`$func1_file\`
- **Line**: $func1_line
- **Content**:
\`\`\`python
$(sed -n "${func1_line},$((func1_line + 20))p" "$func1_file" 2>/dev/null | head -15)
\`\`\`

### Function 2: \`$func2_name\`
- **File**: \`$func2_file\`
- **Line**: $func2_line
- **Content**:
\`\`\`python
$(sed -n "${func2_line},$((func2_line + 20))p" "$func2_file" 2>/dev/null | head -15)
\`\`\`

## Merge Strategy

### Option 1: Extract to Common Module
Create a shared utility function in \`api/utils/\` or appropriate module.

### Option 2: Consolidate to Primary Location
Keep the more comprehensive implementation and redirect the other.

### Option 3: Create Generic Version
Merge both implementations into a more generic, parameterized function.

## Implementation Steps

1. **Create backup**: 
   \`\`\`bash
   cp "$func1_file" "${func1_file}.backup_${TIMESTAMP}"
   cp "$func2_file" "${func2_file}.backup_${TIMESTAMP}"
   \`\`\`

2. **Implement merged function**:
   - Choose optimal location
   - Combine best features from both functions
   - Add comprehensive documentation
   - Include parameter validation

3. **Update references**:
   - Replace calls to old functions
   - Add import statements where needed
   - Update tests to use new function

4. **Validate**:
   - Run existing tests
   - Verify functionality matches original behavior
   - Check for any breaking changes

## Quality Checklist

- [ ] Function behavior preserved
- [ ] All edge cases handled
- [ ] Documentation updated
- [ ] Tests pass
- [ ] No breaking changes
- [ ] Import statements updated
- [ ] Old function references removed

---
*Generated by Intelligent Deduplication Service*
EOF

    echo "$template_file"
}

# Create documentation consolidation template
create_documentation_merge_template() {
    local doc1_file="$1"
    local doc2_file="$2"
    local section_title="$3"
    local similarity="$4"
    
    local template_file="$DEDUP_DIR/doc_merge_template_${TIMESTAMP}.md"
    
    cat > "$template_file" << EOF
# Documentation Merge Template

## Duplicate Documentation Section Detected

**Section Title**: "$section_title"
**Similarity Score**: ${similarity}%
**Files**: \`$doc1_file\` ↔ \`$doc2_file\`

### Content from $doc1_file
\`\`\`markdown
$(grep -A 10 "$section_title" "$doc1_file" 2>/dev/null || echo "Content not found")
\`\`\`

### Content from $doc2_file
\`\`\`markdown
$(grep -A 10 "$section_title" "$doc2_file" 2>/dev/null || echo "Content not found")
\`\`\`

## Consolidation Strategy

### Option 1: Create Master Reference
- Keep most comprehensive version
- Add cross-references in other locations
- Use "See [Master Section]" links

### Option 2: Merge Content
- Combine unique information from both sources
- Remove redundant information
- Create single authoritative section

### Option 3: Split by Audience
- Keep user-focused content in user docs
- Keep technical content in developer docs
- Add appropriate cross-references

## Implementation Steps

1. **Analyze content differences**:
   - Identify unique information in each version
   - Note different perspectives or audiences
   - Check for contradictory information

2. **Choose primary location**:
   - Consider audience and context
   - Select most logical location
   - Plan redirect strategy

3. **Create consolidated content**:
   - Merge unique information
   - Maintain consistent tone and style
   - Add comprehensive cross-references

4. **Update references**:
   - Add "See also" sections
   - Update internal links
   - Create redirect notices

## Quality Checklist

- [ ] All unique information preserved
- [ ] Consistent tone and style
- [ ] Appropriate cross-references added
- [ ] No broken internal links
- [ ] Clear redirect notices
- [ ] Audience-appropriate content level

---
*Generated by Intelligent Deduplication Service*
EOF

    echo "$template_file"
}

# Intelligent automated deduplication
intelligent_deduplication() {
    local mode="${1:-preview}"  # preview, semi-automatic, automatic
    local confidence_threshold="${2:-85}"  # Minimum confidence for automatic actions
    
    log "Starting intelligent deduplication (mode: $mode, threshold: $confidence_threshold)"
    
    local dedup_file="$DEDUP_DIR/intelligent_deduplication_${TIMESTAMP}.json"
    
    cat > "$dedup_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "mode": "$mode",
    "confidence_threshold": $confidence_threshold,
    "actions": {
        "function_merges": [],
        "documentation_merges": [],
        "templates_created": [],
        "automatic_actions": []
    },
    "summary": {"candidates_found": 0, "actions_taken": 0, "templates_created": 0}
}
EOF

    # Load redundancy analysis results
    local function_analysis=$(find "$REPO_ROOT/logs/redundancy_analysis" -name "function_redundancy_*.json" | sort | tail -1)
    local doc_analysis=$(find "$REPO_ROOT/logs/redundancy_analysis" -name "documentation_redundancy_*.json" | sort | tail -1)
    
    local candidates_found=0
    local actions_taken=0
    local templates_created=0
    
    # Process function redundancies
    if [[ -f "$function_analysis" ]]; then
        log "Processing function redundancies from $function_analysis"
        
        # Python functions
        local py_redundancies=$(jq '.languages.python.redundancies // []' "$function_analysis")
        local py_count=$(echo "$py_redundancies" | jq 'length')
        
        for ((i=0; i<py_count; i++)); do
            local redundancy=$(echo "$py_redundancies" | jq ".[$i]")
            local func1=$(echo "$redundancy" | jq -r '.function1')
            local file1=$(echo "$redundancy" | jq -r '.file1')
            local line1=$(echo "$redundancy" | jq -r '.line1')
            local func2=$(echo "$redundancy" | jq -r '.function2')
            local file2=$(echo "$redundancy" | jq -r '.file2')
            local line2=$(echo "$redundancy" | jq -r '.line2')
            local similarity=$(echo "$redundancy" | jq -r '.similarity')
            
            candidates_found=$((candidates_found + 1))
            
            log "Analyzing function redundancy: $func1 ↔ $func2 (${similarity}% similar)"
            
            # Get function content for more detailed analysis
            local func1_content=$(sed -n "${line1},$((line1 + 15))p" "$file1" 2>/dev/null | head -10)
            local func2_content=$(sed -n "${line2},$((line2 + 15))p" "$file2" 2>/dev/null | head -10)
            
            # Calculate enhanced similarity
            local enhanced_similarity=$(calculate_semantic_similarity "$func1_content" "$func2_content" "code")
            
            log "Enhanced similarity score: $enhanced_similarity%"
            
            if [[ $enhanced_similarity -ge $confidence_threshold ]]; then
                case "$mode" in
                    "preview")
                        log "Preview: Would merge $func1 and $func2 (confidence: $enhanced_similarity%)"
                        ;;
                    "semi-automatic")
                        log "Creating merge template for $func1 ↔ $func2"
                        local template=$(create_function_merge_template "$file1" "$line1" "$func1" "$file2" "$line2" "$func2" "$enhanced_similarity")
                        templates_created=$((templates_created + 1))
                        log "✅ Template created: $template"
                        ;;
                    "automatic")
                        if [[ $enhanced_similarity -ge 95 ]]; then
                            log "High confidence merge: Adding consolidation comments"
                            
                            # Add merge comments
                            local comment="# AUTO-DEDUP: High similarity ($enhanced_similarity%) with $func2 in $file2:$line2 - Consider consolidation"
                            if [[ -f "$file1" ]]; then
                                sed -i "${line1}i\\$comment" "$file1"
                                actions_taken=$((actions_taken + 1))
                            fi
                            
                            local reverse_comment="# AUTO-DEDUP: High similarity ($enhanced_similarity%) with $func1 in $file1:$line1 - Consider consolidation"
                            if [[ -f "$file2" ]]; then
                                sed -i "${line2}i\\$reverse_comment" "$file2"
                            fi
                        else
                            log "Creating template for manual review (confidence: $enhanced_similarity%)"
                            local template=$(create_function_merge_template "$file1" "$line1" "$func1" "$file2" "$line2" "$func2" "$enhanced_similarity")
                            templates_created=$((templates_created + 1))
                        fi
                        ;;
                esac
            else
                log "Below confidence threshold: $enhanced_similarity% < $confidence_threshold%"
            fi
        done
        
        # JavaScript functions
        local js_redundancies=$(jq '.languages.javascript.redundancies // []' "$function_analysis")
        local js_count=$(echo "$js_redundancies" | jq 'length')
        
        for ((i=0; i<js_count; i++)); do
            local redundancy=$(echo "$js_redundancies" | jq ".[$i]")
            local func1=$(echo "$redundancy" | jq -r '.function1')
            local file1=$(echo "$redundancy" | jq -r '.file1')
            local func2=$(echo "$redundancy" | jq -r '.function2')
            local file2=$(echo "$redundancy" | jq -r '.file2')
            local similarity=$(echo "$redundancy" | jq -r '.similarity')
            
            candidates_found=$((candidates_found + 1))
            log "JS/TS function redundancy: $func1 ↔ $func2 (${similarity}% similar)"
            
            if [[ $similarity -ge $confidence_threshold ]]; then
                case "$mode" in
                    "preview")
                        log "Preview: Would merge JS functions $func1 and $func2"
                        ;;
                    "semi-automatic"|"automatic")
                        log "Creating merge template for JS functions $func1 ↔ $func2"
                        # Note: Could create specialized JS templates here
                        templates_created=$((templates_created + 1))
                        ;;
                esac
            fi
        done
    fi
    
    # Process documentation redundancies
    if [[ -f "$doc_analysis" ]]; then
        log "Processing documentation redundancies from $doc_analysis"
        
        local duplicate_sections=$(jq '.documents.markdown.duplicate_sections // []' "$doc_analysis")
        local section_count=$(echo "$duplicate_sections" | jq 'length')
        
        for ((i=0; i<section_count; i++)); do
            local section=$(echo "$duplicate_sections" | jq ".[$i]")
            local title=$(echo "$section" | jq -r '.title')
            local file1=$(echo "$section" | jq -r '.file1')
            local file2=$(echo "$section" | jq -r '.file2')
            
            candidates_found=$((candidates_found + 1))
            
            log "Analyzing documentation redundancy: '$title' in $file1 ↔ $file2"
            
            # Get section content for detailed analysis
            local section1_content=$(grep -A 10 "$title" "$file1" 2>/dev/null || echo "")
            local section2_content=$(grep -A 10 "$title" "$file2" 2>/dev/null || echo "")
            
            local doc_similarity=$(calculate_semantic_similarity "$section1_content" "$section2_content" "documentation")
            
            log "Documentation similarity score: $doc_similarity%"
            
            if [[ $doc_similarity -ge $confidence_threshold ]]; then
                case "$mode" in
                    "preview")
                        log "Preview: Would consolidate section '$title' (confidence: $doc_similarity%)"
                        ;;
                    "semi-automatic")
                        log "Creating documentation merge template for '$title'"
                        local template=$(create_documentation_merge_template "$file1" "$file2" "$title" "$doc_similarity")
                        templates_created=$((templates_created + 1))
                        log "✅ Documentation template created: $template"
                        ;;
                    "automatic")
                        if [[ $doc_similarity -ge 90 ]]; then
                            log "High confidence documentation merge: Adding consolidation note"
                            
                            local note="<!-- AUTO-DEDUP: Section '$title' duplicated in $file2 (${doc_similarity}% similar) - Consider consolidation -->"
                            if [[ -f "$file1" ]]; then
                                echo "$note" >> "$file1"
                                actions_taken=$((actions_taken + 1))
                            fi
                        else
                            log "Creating template for manual review (confidence: $doc_similarity%)"
                            local template=$(create_documentation_merge_template "$file1" "$file2" "$title" "$doc_similarity")
                            templates_created=$((templates_created + 1))
                        fi
                        ;;
                esac
            fi
        done
        
        # Process similar content blocks
        local similar_content=$(jq '.documents.markdown.similar_content // []' "$doc_analysis")
        local content_count=$(echo "$similar_content" | jq 'length')
        
        for ((i=0; i<content_count; i++)); do
            local content=$(echo "$similar_content" | jq ".[$i]")
            local file1=$(echo "$content" | jq -r '.file1')
            local file2=$(echo "$content" | jq -r '.file2')
            local similarity=$(echo "$content" | jq -r '.similarity')
            
            candidates_found=$((candidates_found + 1))
            
            if [[ $similarity -ge $confidence_threshold ]]; then
                log "Similar content blocks: $file1 ↔ $file2 (${similarity}% similar)"
                
                case "$mode" in
                    "preview")
                        log "Preview: Would consolidate similar content blocks"
                        ;;
                    "semi-automatic"|"automatic")
                        if [[ $similarity -ge 90 ]]; then
                            log "Adding consolidation note for similar content"
                            local note="<!-- AUTO-DEDUP: Similar content in $file2 (${similarity}% similar) - Review for consolidation -->"
                            if [[ -f "$file1" ]]; then
                                echo "$note" >> "$file1"
                                actions_taken=$((actions_taken + 1))
                            fi
                        fi
                        ;;
                esac
            fi
        done
    fi
    
    # Update deduplication summary
    jq --arg candidates "$candidates_found" --arg actions "$actions_taken" --arg templates "$templates_created" \
       '.summary.candidates_found = ($candidates|tonumber) |
        .summary.actions_taken = ($actions|tonumber) |
        .summary.templates_created = ($templates|tonumber)' \
       "$dedup_file" > "${dedup_file}.tmp" && mv "${dedup_file}.tmp" "$dedup_file"
    
    log "Intelligent deduplication completed:"
    log "  Candidates found: $candidates_found"
    log "  Actions taken: $actions_taken"
    log "  Templates created: $templates_created"
    
    return 0
}

# Monitor deduplication effectiveness
monitor_deduplication_effectiveness() {
    log "Monitoring deduplication effectiveness"
    
    local monitoring_file="$DEDUP_DIR/effectiveness_monitoring_${TIMESTAMP}.json"
    
    # Compare before/after metrics
    local before_analysis=$(find "$REPO_ROOT/logs/redundancy_analysis" -name "repository_health_*.json" | sort | tail -2 | head -1)
    local after_analysis=$(find "$REPO_ROOT/logs/redundancy_analysis" -name "repository_health_*.json" | sort | tail -1)
    
    local health_improvement=0
    local redundancy_reduction=0
    
    if [[ -f "$before_analysis" && -f "$after_analysis" ]]; then
        local before_health=$(jq '.summary.overall_health // 0' "$before_analysis")
        local after_health=$(jq '.summary.overall_health // 0' "$after_analysis")
        local before_redundancy=$(jq '.metrics.redundancy_score // 0' "$before_analysis")
        local after_redundancy=$(jq '.metrics.redundancy_score // 0' "$after_analysis")
        
        health_improvement=$((after_health - before_health))
        redundancy_reduction=$((after_redundancy - before_redundancy))
        
        log "Health score improvement: $health_improvement points"
        log "Redundancy score improvement: $redundancy_reduction points"
    fi
    
    cat > "$monitoring_file" << EOF
{
    "timestamp": "$TIMESTAMP",
    "monitoring_type": "deduplication_effectiveness",
    "metrics": {
        "health_improvement": $health_improvement,
        "redundancy_reduction": $redundancy_reduction,
        "templates_used": 0,
        "successful_merges": 0
    },
    "recommendations": []
}
EOF

    # Generate recommendations based on effectiveness
    local recommendations=()
    
    if [[ $health_improvement -lt 5 ]]; then
        recommendations+=("\"Consider more aggressive deduplication strategies\"")
    fi
    
    if [[ $redundancy_reduction -lt 10 ]]; then
        recommendations+=("\"Review template usage and manual consolidation efforts\"")
    fi
    
    if [[ $health_improvement -ge 10 ]]; then
        recommendations+=("\"Deduplication strategy is effective - maintain current approach\"")
    fi
    
    if [[ ${#recommendations[@]} -eq 0 ]]; then
        recommendations+=("\"Continue monitoring and incremental improvements\"")
    fi
    
    local recommendations_json=$(printf '%s\n' "${recommendations[@]}" | jq -s . 2>/dev/null || echo "[]")
    
    jq --argjson recommendations "$recommendations_json" \
       '.recommendations = $recommendations' \
       "$monitoring_file" > "${monitoring_file}.tmp" && mv "${monitoring_file}.tmp" "$monitoring_file"
    
    log "✅ Effectiveness monitoring completed: $monitoring_file"
}

# Main execution
main() {
    local action="${1:-analyze}"
    local mode="${2:-preview}"
    local threshold="${3:-85}"
    
    log "Intelligent Deduplication Service"
    log "Action: $action, Mode: $mode, Threshold: $threshold"
    
    case "$action" in
        "deduplicate")
            intelligent_deduplication "$mode" "$threshold"
            ;;
        "monitor")
            monitor_deduplication_effectiveness
            ;;
        "template")
            # Create specific template for given files
            local file1="$mode"
            local file2="$threshold"
            if [[ -f "$file1" && -f "$file2" ]]; then
                log "Creating merge template for $file1 and $file2"
                # Template creation logic here
            else
                log "❌ Invalid files provided for template creation"
                return 1
            fi
            ;;
        "help"|*)
            cat << EOF
Intelligent Deduplication Service

Usage: $0 <action> [mode] [threshold]

Actions:
  deduplicate <mode> <threshold>    Perform intelligent deduplication
  monitor                          Monitor deduplication effectiveness
  template <file1> <file2>         Create merge template for specific files
  help                            Show this help

Modes for deduplicate:
  preview                         Show what would be done (default)
  semi-automatic                  Create templates for manual review
  automatic                       Perform safe automatic actions

Threshold:
  Confidence percentage (0-100) for automatic actions (default: 85)

Examples:
  $0 deduplicate preview          # Preview deduplication actions
  $0 deduplicate semi-automatic 90  # Create templates with 90% threshold
  $0 deduplicate automatic 95     # Automatic actions with 95% confidence
  $0 monitor                      # Monitor effectiveness

EOF
            ;;
    esac
}

main "$@"