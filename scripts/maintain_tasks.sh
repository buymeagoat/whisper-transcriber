#!/bin/bash
# TASKS.md Maintenance System
# Keeps task tracking current and accurate

set -e

echo "📋 TASKS.md Maintenance System"
echo "==============================="

# Check if running from project root
if [ ! -f "TASKS.md" ]; then
    echo "❌ Error: Must run from project root (TASKS.md not found)"
    exit 1
fi

# Function to update last modified timestamp
update_timestamp() {
    local current_time=$(date '+%Y-%m-%d %H:%M')
    sed -i "s/> \*\*Last Updated\*\*: [^(]*/> **Last Updated**: $current_time/" TASKS.md
    echo "✅ Updated timestamp to: $current_time"
}

# Function to count task statuses
count_task_status() {
    local completed=$(grep -c "✅ \*\*COMPLETED\*\*\|~~.*~~.*✅" TASKS.md || echo "0")
    local in_progress=$(grep -c "🟡 \*\*IN PROGRESS\*\*" TASKS.md || echo "0")
    local critical_total=$(grep -c "#### \*\*I00[12]:" TASKS.md || echo "0")
    local high_total=$(grep -c "#### \*\*I00[345]:" TASKS.md || echo "0")
    local medium_total=$(grep -c "#### \*\*I00[67]:" TASKS.md || echo "0")
    local low_total=$(grep -c "#### \*\*I008:" TASKS.md || echo "0")
    
    echo "📊 Task Status Summary:"
    echo "   Critical: $completed Complete, $in_progress In-Progress (of $critical_total total)"
    echo "   High: $high_total active"
    echo "   Medium: $medium_total active" 
    echo "   Low: $low_total active"
    
    # Update status line in TASKS.md
    local status_line="> **Status**: $completed Critical Complete ✅, $in_progress Critical In-Progress 🟡, $((high_total + medium_total + low_total)) Active Issues"
    sed -i "s/> \*\*Status\*\*: .*/$status_line/" TASKS.md
}

# Function to validate task format
validate_format() {
    echo "🔍 Validating TASKS.md format..."
    
    local issues=0
    
    # Check for required sections
    if ! grep -q "## 🚨 \*\*ISSUES" TASKS.md; then
        echo "   ❌ Missing Issues section"
        issues=$((issues + 1))
    fi
    
    if ! grep -q "## 📈 \*\*ENHANCEMENTS" TASKS.md; then
        echo "   ❌ Missing Enhancements section"
        issues=$((issues + 1))
    fi
    
    # Check for consistent task numbering
    local expected_issue=1
    while [ $expected_issue -le 8 ]; do
        local padded=$(printf "%03d" $expected_issue)
        if ! grep -q "#### \*\*I$padded:" TASKS.md; then
            echo "   ⚠️  Issue I$padded not found (may be completed)"
        fi
        expected_issue=$((expected_issue + 1))
    done
    
    if [ $issues -eq 0 ]; then
        echo "   ✅ Format validation passed"
    else
        echo "   ❌ Found $issues format issues"
    fi
    
    return $issues
}

# Function to check for completed tasks that need archiving
check_completed_tasks() {
    echo "🗄️ Checking for tasks ready to archive..."
    
    local completed_tasks=$(grep -n "✅ \*\*COMPLETED\*\*\|~~.*~~.*✅" TASKS.md || echo "")
    
    if [ -n "$completed_tasks" ]; then
        echo "   📦 Found completed tasks:"
        echo "$completed_tasks" | sed 's/^/      /'
        echo "   💡 Consider moving to archive section when section gets large"
    else
        echo "   ✅ No completed tasks found"
    fi
}

# Function to suggest next actions
suggest_next_actions() {
    echo ""
    echo "🎯 NEXT ACTION RECOMMENDATIONS"
    echo "=============================="
    
    # Check for in-progress tasks
    if grep -q "🟡 \*\*IN PROGRESS\*\*" TASKS.md; then
        echo "📌 CURRENT FOCUS:"
        grep -A1 "🟡 \*\*IN PROGRESS\*\*" TASKS.md | head -1 | sed 's/#### \*\*/   /'
        echo ""
    fi
    
    # Find next critical task
    local next_critical=$(grep -n "### \*\*🔴 CRITICAL\*\*" -A 50 TASKS.md | grep "#### \*\*I" | grep -v "✅\|🟡" | head -1)
    if [ -n "$next_critical" ]; then
        echo "🚨 NEXT CRITICAL:"
        echo "$next_critical" | sed 's/.*#### \*\*/   /' | sed 's/\*\*//'
        echo ""
    fi
    
    # Find next high priority task  
    local next_high=$(grep -n "### \*\*🟡 HIGH\*\*" -A 50 TASKS.md | grep "#### \*\*I" | grep -v "✅\|🟡" | head -1)
    if [ -n "$next_high" ]; then
        echo "⚡ NEXT HIGH PRIORITY:"
        echo "$next_high" | sed 's/.*#### \*\*/   /' | sed 's/\*\*//'
        echo ""
    fi
}

# Main execution
case "${1:-update}" in
    "update")
        echo "🔄 Performing routine update..."
        update_timestamp
        count_task_status
        validate_format
        check_completed_tasks
        suggest_next_actions
        echo ""
        echo "✅ TASKS.md maintenance complete"
        ;;
    "validate")
        echo "🔍 Performing validation only..."
        validate_format
        if [ $? -eq 0 ]; then
            echo "✅ TASKS.md validation passed"
        else
            echo "❌ TASKS.md validation failed"
            exit 1
        fi
        ;;
    "status")
        echo "📊 Checking task status..."
        count_task_status
        suggest_next_actions
        ;;
    "help")
        echo "📋 TASKS.md Maintenance Commands:"
        echo "   ./scripts/maintain_tasks.sh update    - Update timestamps and status (default)"
        echo "   ./scripts/maintain_tasks.sh validate  - Validate format only"
        echo "   ./scripts/maintain_tasks.sh status    - Show current status"
        echo "   ./scripts/maintain_tasks.sh help      - Show this help"
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo "Run './scripts/maintain_tasks.sh help' for usage"
        exit 1
        ;;
esac