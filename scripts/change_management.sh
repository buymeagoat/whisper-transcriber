#!/bin/bash

# Change Management and Quality Enforcement System
# Enforces mandatory development-production parity and documentation updates

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REQUIRED_ENVIRONMENTS=("development" "production")
REQUIRED_DOCS=("README.md" "CHANGELOG.md" "TASKS.md")
CHANGE_LOG_DIR="$PROJECT_ROOT/logs/changes"
BUILD_LOG_DIR="$PROJECT_ROOT/logs/builds"

# Create necessary directories
mkdir -p "$CHANGE_LOG_DIR" "$BUILD_LOG_DIR"

log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "ERROR")
            echo -e "${RED}[$timestamp] ERROR: $message${NC}" >&2
            ;;
        "WARN")
            echo -e "${YELLOW}[$timestamp] WARN: $message${NC}" >&2
            ;;
        "INFO")
            echo -e "${GREEN}[$timestamp] INFO: $message${NC}"
            ;;
        "DEBUG")
            echo -e "${BLUE}[$timestamp] DEBUG: $message${NC}"
            ;;
    esac
}

# Function: Validate change request
validate_change_request() {
    local change_description="$1"
    local task_id="${2:-}"
    
    log "INFO" "🔍 Validating change request: $change_description"
    
    # Check if this is a valid change type
    if [[ -z "$change_description" ]]; then
        log "ERROR" "Change description cannot be empty"
        return 1
    fi
    
    # Check if TASKS.md has been updated
    if ! check_tasks_md_updated "$task_id"; then
        log "ERROR" "TASKS.md must be updated before implementing changes"
        return 1
    fi
    
    log "INFO" "✅ Change request validation passed"
    return 0
}

# Function: Check if TASKS.md has been updated
check_tasks_md_updated() {
    local task_id="$1"
    
    if [[ -z "$task_id" ]]; then
        log "WARN" "No task ID provided for TASKS.md validation"
        return 0  # Allow for non-task changes
    fi
    
    # Check if task exists in TASKS.md
    if ! grep -q "$task_id" "$PROJECT_ROOT/TASKS.md"; then
        log "ERROR" "Task $task_id not found in TASKS.md"
        return 1
    fi
    
    # Check if task is properly formatted
    if ! grep -q "^\s*-\s*\[\s*[x ]\s*\].*$task_id" "$PROJECT_ROOT/TASKS.md"; then
        log "ERROR" "Task $task_id is not properly formatted in TASKS.md"
        return 1
    fi
    
    return 0
}

# Function: Run development tests
run_development_tests() {
    local change_type="$1"
    
    log "INFO" "🧪 Running development environment tests"
    
    # Backend tests
    if [[ "$change_type" =~ backend|api|auth|security ]]; then
        log "INFO" "Running backend tests..."
        if ! "$SCRIPT_DIR/run_backend_tests.sh"; then
            log "ERROR" "Backend tests failed"
            return 1
        fi
    fi
    
    # Frontend tests  
    if [[ "$change_type" =~ frontend|ui|react ]]; then
        log "INFO" "Running frontend tests..."
        cd "$PROJECT_ROOT/frontend"
        if ! npm test; then
            log "ERROR" "Frontend tests failed"
            return 1
        fi
        cd "$PROJECT_ROOT"
    fi
    
    # Integration tests
    log "INFO" "Running integration tests..."
    if ! pytest "$PROJECT_ROOT/tests/" -v; then
        log "ERROR" "Integration tests failed"
        return 1
    fi
    
    log "INFO" "✅ Development tests passed"
    return 0
}

# Function: Validate production readiness
validate_production_readiness() {
    local change_type="$1"
    
    log "INFO" "🏭 Validating production readiness"
    
    # Check Docker build
    log "INFO" "Validating Docker build..."
    if ! docker-compose -f "$PROJECT_ROOT/docker-compose.yml" config > /dev/null; then
        log "ERROR" "Docker compose configuration invalid"
        return 1
    fi
    
    # Check environment variables
    log "INFO" "Checking production environment requirements..."
    if [[ ! -f "$PROJECT_ROOT/.env.production.template" ]]; then
        log "ERROR" "Production environment template missing"
        return 1
    fi
    
    # Security validation
    log "INFO" "Running security validation..."
    if ! "$SCRIPT_DIR/security_validation.sh"; then
        log "ERROR" "Security validation failed"
        return 1
    fi
    
    log "INFO" "✅ Production readiness validated"
    return 0
}

# Function: Create change log
create_change_log() {
    local change_description="$1"
    local task_id="${2:-N/A}"
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local change_log_file="$CHANGE_LOG_DIR/change_$timestamp.md"
    
    log "INFO" "📝 Creating change log: $change_log_file"
    
    cat > "$change_log_file" << EOF
# Change Log - $timestamp

## Summary
**Description**: $change_description
**Task ID**: $task_id
**Date**: $(date '+%Y-%m-%d %H:%M:%S')
**Author**: $(git config user.name)

## Files Changed
$(git diff --name-only HEAD~1..HEAD | while read -r file; do
    echo "- \`$file\`: $(git log -1 --format='%s' -- "$file" | head -c 80)..."
done)

## Tests
### Development Tests
- [ ] Backend tests passed
- [ ] Frontend tests passed  
- [ ] Integration tests passed

### Production Validation
- [ ] Docker build validated
- [ ] Security validation passed
- [ ] Environment configuration verified

## Build Notes
Build log: logs/builds/build_$timestamp.md

## Risk & Rollback
**Risk Level**: TBD
**Rollback Steps**:
1. \`git revert \$(git rev-parse HEAD)\`
2. Re-run validation pipeline
3. Update documentation

## Documentation Updates
- [ ] CHANGELOG.md updated
- [ ] API documentation updated (if applicable)
- [ ] README.md updated (if applicable)
- [ ] TASKS.md updated

## Approval
- [ ] Development testing complete
- [ ] Production validation complete
- [ ] Documentation updated
- [ ] Ready for deployment

---
*Generated by Change Management System - $(date)*
EOF

    echo "$change_log_file"
}

# Function: Update documentation
update_documentation() {
    local change_description="$1"
    local task_id="${2:-}"
    
    log "INFO" "📚 Updating documentation"
    
    # Update CHANGELOG.md
    local changelog_entry="- **$(date '+%Y-%m-%d')**: $change_description"
    if [[ -n "$task_id" ]]; then
        changelog_entry="$changelog_entry (Task: $task_id)"
    fi
    
    # Add to changelog
    if [[ -f "$PROJECT_ROOT/CHANGELOG.md" ]]; then
        # Add entry under ## [Unreleased] section
        if grep -q "## \[Unreleased\]" "$PROJECT_ROOT/CHANGELOG.md"; then
            sed -i "/## \[Unreleased\]/a\\$changelog_entry" "$PROJECT_ROOT/CHANGELOG.md"
        else
            # Create Unreleased section
            sed -i "1a\\## [Unreleased]\\n$changelog_entry\\n" "$PROJECT_ROOT/CHANGELOG.md"
        fi
        log "INFO" "✅ CHANGELOG.md updated"
    fi
    
    # Update task status if task_id provided
    if [[ -n "$task_id" ]] && [[ -f "$PROJECT_ROOT/TASKS.md" ]]; then
        # Mark task as completed if not already
        if grep -q "^\s*-\s*\[\s*\]\s*.*$task_id" "$PROJECT_ROOT/TASKS.md"; then
            sed -i "s/^\(\s*-\s*\)\[\s*\]\(\s*.*$task_id.*\)/\1[x]\2 ✅ **COMPLETED**/" "$PROJECT_ROOT/TASKS.md"
            log "INFO" "✅ Task $task_id marked as completed in TASKS.md"
        fi
    fi
}

# Function: Archive completed tasks
archive_completed_tasks() {
    log "INFO" "🗂️  Archiving completed tasks"
    
    # Create archive section if it doesn't exist
    if ! grep -q "## 📝 ARCHIVED COMPLETED TASKS" "$PROJECT_ROOT/TASKS.md"; then
        echo -e "\n---\n\n## 📝 ARCHIVED COMPLETED TASKS\n" >> "$PROJECT_ROOT/TASKS.md"
    fi
    
    # Find completed tasks and move them to archive
    local completed_tasks=$(grep -n "^\s*-\s*\[x\].*✅.*COMPLETED" "$PROJECT_ROOT/TASKS.md" | head -20)
    
    if [[ -n "$completed_tasks" ]]; then
        local archive_section_line=$(grep -n "## 📝 ARCHIVED COMPLETED TASKS" "$PROJECT_ROOT/TASKS.md" | cut -d: -f1)
        
        # Move completed tasks to archive (keeping last 20 for reference)
        while IFS= read -r completed_task; do
            local line_num=$(echo "$completed_task" | cut -d: -f1)
            local task_text=$(echo "$completed_task" | cut -d: -f2-)
            
            # Add to archive section
            sed -i "${archive_section_line}a\\$task_text" "$PROJECT_ROOT/TASKS.md"
            
            # Remove from active section
            sed -i "${line_num}d" "$PROJECT_ROOT/TASKS.md"
            
            log "INFO" "Archived completed task: $(echo "$task_text" | head -c 60)..."
        done <<< "$completed_tasks"
        
        log "INFO" "✅ Completed tasks archived"
    fi
}

# Function: Enforce mandatory workflow
enforce_workflow() {
    local change_description="$1"
    local task_id="${2:-}"
    
    log "INFO" "🔐 Enforcing mandatory change management workflow"
    
    # Step 1: Validate change request
    if ! validate_change_request "$change_description" "$task_id"; then
        log "ERROR" "❌ Change request validation failed"
        return 1
    fi
    
    # Step 2: Run development tests
    if ! run_development_tests "$change_description"; then
        log "ERROR" "❌ Development tests failed"
        return 1
    fi
    
    # Step 3: Validate production readiness  
    if ! validate_production_readiness "$change_description"; then
        log "ERROR" "❌ Production validation failed"
        return 1
    fi
    
    # Step 4: Create change log
    local change_log_file=$(create_change_log "$change_description" "$task_id")
    log "INFO" "Change log created: $change_log_file"
    
    # Step 5: Update documentation
    update_documentation "$change_description" "$task_id"
    
    # Step 6: Archive completed tasks
    archive_completed_tasks
    
    log "INFO" "✅ Mandatory workflow enforcement complete"
    return 0
}

# Main execution
main() {
    local action="${1:-help}"
    
    case "$action" in
        "validate")
            local change_description="${2:-}"
            local task_id="${3:-}"
            enforce_workflow "$change_description" "$task_id"
            ;;
        "archive-tasks")
            archive_completed_tasks
            ;;
        "update-docs")
            local change_description="${2:-}"
            local task_id="${3:-}"
            update_documentation "$change_description" "$task_id"
            ;;
        "help"|*)
            echo "Change Management System"
            echo ""
            echo "Usage: $0 <action> [args...]"
            echo ""
            echo "Actions:"
            echo "  validate <description> [task_id]  - Run full validation workflow"
            echo "  archive-tasks                     - Archive completed tasks"
            echo "  update-docs <description> [task_id] - Update documentation"
            echo "  help                              - Show this help"
            echo ""
            echo "Example:"
            echo "  $0 validate 'Implement authentication security hardening' S001"
            ;;
    esac
}

# Execute main function
main "$@"