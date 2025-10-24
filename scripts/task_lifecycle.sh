#!/bin/bash

# Task Lifecycle Management Script
# Automatically manages task completion and archival in TASKS.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TASKS_FILE="$PROJECT_ROOT/TASKS.md"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] $*${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] WARN: $*${NC}"
}

error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ERROR: $*${NC}" >&2
}

info() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')] INFO: $*${NC}"
}

# Function to complete a task
complete_task() {
    local task_id="$1"
    local completion_note="${2:-}"
    
    log "Completing task: $task_id"
    
    if [[ ! -f "$TASKS_FILE" ]]; then
        error "TASKS.md not found at $TASKS_FILE"
        return 1
    fi
    
    # Check if task exists
    if ! grep -q "$task_id" "$TASKS_FILE"; then
        error "Task $task_id not found in TASKS.md"
        return 1
    fi
    
    # Check if task is already completed
    if grep -q "^\s*-\s*\[x\].*$task_id.*✅.*COMPLETED" "$TASKS_FILE"; then
        warn "Task $task_id is already marked as completed"
        return 0
    fi
    
    # Mark task as completed
    local completion_text="✅ **COMPLETED**"
    if [[ -n "$completion_note" ]]; then
        completion_text="$completion_text - $completion_note"
    fi
    completion_text="$completion_text ($(date '+%Y-%m-%d'))"
    
    # Update the task in TASKS.md
    if grep -q "^\s*-\s*\[\s*\]\s*.*$task_id" "$TASKS_FILE"; then
        # Mark uncompleted task as completed
        sed -i "s/^\(\s*-\s*\)\[\s*\]\(\s*.*$task_id.*\)/\1[x]\2 $completion_text/" "$TASKS_FILE"
        log "Task $task_id marked as completed"
    elif grep -q "^\s*-\s*\[x\]\s*.*$task_id" "$TASKS_FILE"; then
        # Add completion marker to already checked task
        sed -i "s/^\(\s*-\s*\[x\]\s*.*$task_id.*\)$/\1 $completion_text/" "$TASKS_FILE"
        log "Added completion marker to task $task_id"
    else
        error "Could not find task $task_id in proper format"
        return 1
    fi
    
    return 0
}

# Function to archive completed tasks
archive_completed_tasks() {
    local max_active_completed="${1:-10}"
    
    log "Archiving completed tasks (keeping last $max_active_completed active)"
    
    if [[ ! -f "$TASKS_FILE" ]]; then
        error "TASKS.md not found at $TASKS_FILE"
        return 1
    fi
    
    # Create temporary files
    local temp_file=$(mktemp)
    local archive_temp=$(mktemp)
    local completed_temp=$(mktemp)
    
    # Find completed tasks
    grep -n "^\s*-\s*\[x\].*✅.*COMPLETED" "$TASKS_FILE" > "$completed_temp" || true
    
    local completed_count=$(wc -l < "$completed_temp")
    
    if [[ $completed_count -le $max_active_completed ]]; then
        info "Only $completed_count completed tasks found, no archival needed"
        rm -f "$temp_file" "$archive_temp" "$completed_temp"
        return 0
    fi
    
    log "Found $completed_count completed tasks, archiving $(($completed_count - $max_active_completed))"
    
    # Get tasks to archive (all but the last max_active_completed)
    local tasks_to_archive=$(($completed_count - $max_active_completed))
    head -n $tasks_to_archive "$completed_temp" > "$archive_temp"
    
    # Ensure archive section exists
    if ! grep -q "## 📝 ARCHIVED COMPLETED TASKS" "$TASKS_FILE"; then
        echo "" >> "$TASKS_FILE"
        echo "---" >> "$TASKS_FILE"
        echo "" >> "$TASKS_FILE"
        echo "## 📝 ARCHIVED COMPLETED TASKS" >> "$TASKS_FILE"
        echo "" >> "$TASKS_FILE"
        echo "*Tasks completed and verified - moved from active list for better organization*" >> "$TASKS_FILE"
        echo "" >> "$TASKS_FILE"
    fi
    
    # Find the archive section line
    local archive_line=$(grep -n "## 📝 ARCHIVED COMPLETED TASKS" "$TASKS_FILE" | cut -d: -f1)
    
    # Process each task to archive
    while IFS= read -r line; do
        local line_num=$(echo "$line" | cut -d: -f1)
        local task_text=$(echo "$line" | cut -d: -f2-)
        
        # Add to archive section
        sed -i "${archive_line}a\\$task_text" "$TASKS_FILE"
        
        log "Archived: $(echo "$task_text" | head -c 60)..."
    done < "$archive_temp"
    
    # Remove archived tasks from active sections (in reverse order to maintain line numbers)
    tac "$archive_temp" | while IFS= read -r line; do
        local line_num=$(echo "$line" | cut -d: -f1)
        sed -i "${line_num}d" "$TASKS_FILE"
    done
    
    # Clean up
    rm -f "$temp_file" "$archive_temp" "$completed_temp"
    
    log "Completed task archival - $tasks_to_archive tasks moved to archive"
    return 0
}

# Function to validate task format
validate_task_format() {
    local task_id="$1"
    
    if [[ ! -f "$TASKS_FILE" ]]; then
        error "TASKS.md not found at $TASKS_FILE"
        return 1
    fi
    
    # Check if task exists and is properly formatted
    if grep -q "^\s*-\s*\[\s*[x ]\s*\].*$task_id" "$TASKS_FILE"; then
        log "Task $task_id found and properly formatted"
        return 0
    else
        error "Task $task_id not found or improperly formatted"
        error "Expected format: - [ ] or - [x] TaskID: Description"
        return 1
    fi
}

# Function to list active tasks
list_active_tasks() {
    local status_filter="${1:-all}"
    
    if [[ ! -f "$TASKS_FILE" ]]; then
        error "TASKS.md not found at $TASKS_FILE"
        return 1
    fi
    
    log "Listing active tasks (filter: $status_filter)"
    
    case "$status_filter" in
        "pending"|"incomplete")
            grep "^\s*-\s*\[\s*\]\s*" "$TASKS_FILE" | head -20
            ;;
        "completed")
            grep "^\s*-\s*\[x\].*✅.*COMPLETED" "$TASKS_FILE" | head -20
            ;;
        "all"|*)
            grep "^\s*-\s*\[\s*[x ]\s*\]" "$TASKS_FILE" | head -30
            ;;
    esac
}

# Function to generate task completion report
generate_completion_report() {
    local report_file="$PROJECT_ROOT/reports/task_completion_$(date '+%Y%m%d_%H%M%S').md"
    mkdir -p "$(dirname "$report_file")"
    
    log "Generating task completion report: $report_file"
    
    if [[ ! -f "$TASKS_FILE" ]]; then
        error "TASKS.md not found at $TASKS_FILE"
        return 1
    fi
    
    local total_tasks=$(grep -c "^\s*-\s*\[\s*[x ]\s*\]" "$TASKS_FILE" || echo "0")
    local completed_tasks=$(grep -c "^\s*-\s*\[x\]" "$TASKS_FILE" || echo "0")
    local pending_tasks=$(grep -c "^\s*-\s*\[\s*\]\s*" "$TASKS_FILE" || echo "0")
    local completion_rate=0
    
    if [[ $total_tasks -gt 0 ]]; then
        completion_rate=$(echo "scale=1; $completed_tasks * 100 / $total_tasks" | bc -l 2>/dev/null || echo "0")
    fi
    
    cat > "$report_file" << EOF
# Task Completion Report

**Generated**: $(date '+%Y-%m-%d %H:%M:%S')
**Report Type**: Task Lifecycle Management

## Summary Statistics

- **Total Tasks**: $total_tasks
- **Completed Tasks**: $completed_tasks
- **Pending Tasks**: $pending_tasks
- **Completion Rate**: ${completion_rate}%

## Recently Completed Tasks

$(grep "^\s*-\s*\[x\].*✅.*COMPLETED" "$TASKS_FILE" | tail -10 | sed 's/^//')

## Active Pending Tasks

$(grep "^\s*-\s*\[\s*\]\s*" "$TASKS_FILE" | head -10 | sed 's/^//')

## Task Management Health

$(if [[ $pending_tasks -gt 20 ]]; then
    echo "⚠️  **High task load**: $pending_tasks pending tasks may need prioritization"
elif [[ $pending_tasks -lt 5 ]]; then
    echo "✅ **Low task load**: $pending_tasks pending tasks - good management"
else
    echo "✅ **Normal task load**: $pending_tasks pending tasks - manageable level"
fi)

## Recommendations

$(if [[ $completion_rate -lt 50 ]]; then
    echo "- Focus on completing existing tasks before adding new ones"
    echo "- Consider breaking down large tasks into smaller ones"
elif [[ $completion_rate -gt 80 ]]; then
    echo "- Good completion rate - consider adding more strategic tasks"
    echo "- Archive completed tasks if list is getting long"
else
    echo "- Balanced task completion - maintain current pace"
    echo "- Regular archival of completed tasks recommended"
fi)

---
*Generated by Task Lifecycle Management System*
EOF

    echo "$report_file"
}

# Main function
main() {
    local action="${1:-help}"
    
    case "$action" in
        "complete")
            local task_id="${2:-}"
            local note="${3:-}"
            if [[ -z "$task_id" ]]; then
                error "Task ID required for completion"
                error "Usage: $0 complete <task_id> [note]"
                return 1
            fi
            complete_task "$task_id" "$note"
            ;;
        "archive")
            local max_active="${2:-10}"
            archive_completed_tasks "$max_active"
            ;;
        "validate")
            local task_id="${2:-}"
            if [[ -z "$task_id" ]]; then
                error "Task ID required for validation"
                error "Usage: $0 validate <task_id>"
                return 1
            fi
            validate_task_format "$task_id"
            ;;
        "list")
            local filter="${2:-all}"
            list_active_tasks "$filter"
            ;;
        "report")
            generate_completion_report
            ;;
        "help"|*)
            echo "Task Lifecycle Management System"
            echo ""
            echo "Usage: $0 <action> [arguments...]"
            echo ""
            echo "Actions:"
            echo "  complete <task_id> [note]  - Mark task as completed"
            echo "  archive [max_active]       - Archive old completed tasks (default: keep 10)"
            echo "  validate <task_id>         - Validate task format"
            echo "  list [filter]              - List tasks (all|pending|completed)"
            echo "  report                     - Generate completion report"
            echo "  help                       - Show this help"
            echo ""
            echo "Examples:"
            echo "  $0 complete S001 'Authentication security implemented'"
            echo "  $0 archive 5"
            echo "  $0 list pending"
            ;;
    esac
}

main "$@"