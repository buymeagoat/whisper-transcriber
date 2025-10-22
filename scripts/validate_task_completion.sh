#!/bin/bash
# Task Completion Validation Script
# Validates that TASKS.md is updated and comprehensive testing is performed

set -e

REPO_ROOT="/home/buymeagoat/dev/whisper-transcriber"
TASKS_FILE="$REPO_ROOT/TASKS.md"
TESTS_DIR="$REPO_ROOT/tests"
TEMP_DIR="$REPO_ROOT/temp"

echo "🔍 Task Completion Validation"
echo "============================="
echo ""

# Ensure we're in the repository
cd "$REPO_ROOT"

# Function to check if TASKS.md has been updated recently
check_tasks_md_updated() {
    echo "1. Checking TASKS.md updates..."
    
    if [[ ! -f "$TASKS_FILE" ]]; then
        echo "❌ TASKS.md file not found!"
        echo "   Create TASKS.md with current task status"
        return 1
    fi
    
    # Check if TASKS.md is staged for commit
    if git diff --cached --name-only | grep -q "TASKS.md"; then
        echo "✅ TASKS.md is staged for commit"
        
        # Check for completed task markers in the staged changes
        if git diff --cached TASKS.md | grep -q "✅ \*\*COMPLETED\*\*"; then
            echo "✅ Task completion marker found in TASKS.md"
        else
            echo "⚠️  No task completion markers found in staged TASKS.md changes"
            echo "   Expected pattern: ✅ **COMPLETED**"
            echo "   Please mark the completed task appropriately"
            return 1
        fi
    else
        # Check if TASKS.md was modified recently (within last hour)
        if [[ -f "$TASKS_FILE" ]]; then
            TASKS_MOD_TIME=$(stat -c %Y "$TASKS_FILE" 2>/dev/null || stat -f %m "$TASKS_FILE" 2>/dev/null)
            CURRENT_TIME=$(date +%s)
            TIME_DIFF=$((CURRENT_TIME - TASKS_MOD_TIME))
            
            if [[ $TIME_DIFF -lt 3600 ]]; then
                echo "✅ TASKS.md was modified within the last hour"
            else
                echo "❌ TASKS.md has not been updated recently"
                echo "   Please update TASKS.md to reflect task completion"
                echo "   Expected: Mark completed task with ✅ **COMPLETED**"
                return 1
            fi
        fi
    fi
    
    return 0
}

# Function to validate comprehensive testing
check_comprehensive_testing() {
    echo ""
    echo "2. Checking comprehensive testing requirements..."
    
    if [[ ! -d "$TESTS_DIR" ]]; then
        echo "❌ Tests directory not found!"
        echo "   Create tests/ directory with test files"
        return 1
    fi
    
    # Count test files
    TEST_FILES=$(find "$TESTS_DIR" -name "test_*.py" | wc -l)
    echo "   Found $TEST_FILES test files"
    
    if [[ $TEST_FILES -eq 0 ]]; then
        echo "❌ No test files found in tests/ directory"
        echo "   Create test files following pattern: test_*.py"
        return 1
    fi
    
    # Check for recent test additions or modifications
    RECENT_TESTS=$(find "$TESTS_DIR" -name "test_*.py" -newermt "1 hour ago" | wc -l)
    
    if git diff --cached --name-only | grep -q "^tests/"; then
        echo "✅ Test files are staged for commit"
    elif [[ $RECENT_TESTS -gt 0 ]]; then
        echo "✅ Test files modified within the last hour: $RECENT_TESTS"
    else
        echo "⚠️  No recent test file modifications detected"
        echo "   When completing a task, update or add relevant tests"
        echo "   Consider adding tests for:"
        echo "     - New functionality"
        echo "     - Bug fixes"
        echo "     - API endpoints"
        echo "     - Edge cases"
    fi
    
    # Check for test coverage information
    if [[ -f "$REPO_ROOT/coverage.xml" ]] || [[ -f "$REPO_ROOT/.coverage" ]]; then
        echo "✅ Test coverage files found"
    else
        echo "⚠️  No test coverage files found"
        echo "   Run tests with coverage: pytest --cov=api tests/"
    fi
    
    return 0
}

# Function to check for proper documentation of testing
check_test_documentation() {
    echo ""
    echo "3. Checking test documentation..."
    
    # Look for test documentation in change logs
    CHANGE_FILES=$(find "$REPO_ROOT/logs/changes" -name "change_*.md" -newermt "1 hour ago" 2>/dev/null || true)
    
    if [[ -n "$CHANGE_FILES" ]]; then
        for CHANGE_FILE in $CHANGE_FILES; do
            if grep -q "## Tests" "$CHANGE_FILE" && grep -q -v "placeholder" "$CHANGE_FILE"; then
                echo "✅ Test documentation found in $CHANGE_FILE"
                return 0
            fi
        done
        echo "⚠️  Change log found but lacks test documentation"
        echo "   Please document testing in logs/changes/change_*.md"
    else
        echo "⚠️  No recent change logs found"
        echo "   Change logs should document testing performed"
    fi
    
    return 0
}

# Function to check for test execution evidence
check_test_execution() {
    echo ""
    echo "4. Checking test execution evidence..."
    
    # Look for recent test execution in various forms
    TEST_EVIDENCE=false
    
    # Check for pytest cache (indicates recent test runs)
    if [[ -d "$REPO_ROOT/.pytest_cache" ]]; then
        CACHE_MOD_TIME=$(stat -c %Y "$REPO_ROOT/.pytest_cache" 2>/dev/null || stat -f %m "$REPO_ROOT/.pytest_cache" 2>/dev/null)
        CURRENT_TIME=$(date +%s)
        TIME_DIFF=$((CURRENT_TIME - CACHE_MOD_TIME))
        
        if [[ $TIME_DIFF -lt 3600 ]]; then
            echo "✅ Recent pytest execution detected (cache updated within 1 hour)"
            TEST_EVIDENCE=true
        fi
    fi
    
    # Check for test output files in temp directory
    if [[ -d "$TEMP_DIR" ]]; then
        TEST_OUTPUT=$(find "$TEMP_DIR" -name "*test*" -o -name "*coverage*" -newermt "1 hour ago" 2>/dev/null | head -3)
        if [[ -n "$TEST_OUTPUT" ]]; then
            echo "✅ Recent test output files found in temp/"
            echo "$TEST_OUTPUT" | sed 's/^/   /'
            TEST_EVIDENCE=true
        fi
    fi
    
    if [[ "$TEST_EVIDENCE" == false ]]; then
        echo "⚠️  No evidence of recent test execution found"
        echo "   Please run tests before completing task:"
        echo "     pytest tests/"
        echo "     pytest --cov=api tests/"
        echo "     npm test (for frontend)"
    fi
    
    return 0
}

# Function to provide actionable recommendations
provide_recommendations() {
    echo ""
    echo "📋 Task Completion Checklist"
    echo "============================"
    echo ""
    echo "Before marking a task complete, ensure:"
    echo ""
    echo "✓ TASKS.md Requirements:"
    echo "  - Mark completed task with: ✅ **COMPLETED**"
    echo "  - Add detailed description of what was implemented"
    echo "  - Update task status from [ ] to [x]"
    echo ""
    echo "✓ Testing Requirements:"
    echo "  - Add tests for new functionality: test_<feature>.py"
    echo "  - Run comprehensive test suite: pytest tests/"
    echo "  - Generate coverage report: pytest --cov=api tests/"
    echo "  - Test frontend components: npm test"
    echo "  - Document test results in change log"
    echo ""
    echo "✓ Documentation Requirements:"
    echo "  - Update relevant documentation in docs/"
    echo "  - Create change log: logs/changes/change_<timestamp>.md"
    echo "  - Document testing performed and results"
    echo "  - Update CHANGELOG.md with feature description"
    echo ""
    echo "✓ Quality Assurance:"
    echo "  - Code follows project standards"
    echo "  - All tests pass"
    echo "  - No temporary files in repository root"
    echo "  - Proper error handling implemented"
    echo ""
}

# Main validation execution
echo "Starting validation for task completion requirements..."
echo ""

VALIDATION_PASSED=true

# Run all validation checks
if ! check_tasks_md_updated; then
    VALIDATION_PASSED=false
fi

if ! check_comprehensive_testing; then
    VALIDATION_PASSED=false
fi

check_test_documentation
check_test_execution

echo ""
echo "🎯 Validation Summary"
echo "===================="

if [[ "$VALIDATION_PASSED" == true ]]; then
    echo "✅ Task completion validation PASSED"
    echo "   - TASKS.md has been properly updated"
    echo "   - Testing requirements are satisfied"
    echo "   - Ready for task completion"
    echo ""
    echo "Proceed with: ./scripts/ai_task_complete.sh"
    exit 0
else
    echo "❌ Task completion validation FAILED"
    echo "   - Address the issues above before completing task"
    echo ""
    provide_recommendations
    exit 1
fi