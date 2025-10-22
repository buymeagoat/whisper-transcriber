#!/bin/bash

# T030 User Preferences Enhancement: Test Runner Script
# Comprehensive test runner for all T030 preference components

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
TEST_CONFIG="src/components/__tests__/jest.config.js"
COVERAGE_DIR="coverage"
RESULTS_DIR="test-results"

# Create required directories
mkdir -p "$COVERAGE_DIR"
mkdir -p "$RESULTS_DIR"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[T030]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[T030]${NC} ✅ $1"
}

print_warning() {
    echo -e "${YELLOW}[T030]${NC} ⚠️  $1"
}

print_error() {
    echo -e "${RED}[T030]${NC} ❌ $1"
}

# Function to run tests with timing
run_test_suite() {
    local name="$1"
    local pattern="$2"
    local start_time
    
    print_status "Running $name tests..."
    start_time=$(date +%s)
    
    if npm run jest -- --config="$TEST_CONFIG" --testPathPattern="$pattern" --verbose; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        print_success "$name tests completed in ${duration}s"
        return 0
    else
        print_error "$name tests failed"
        return 1
    fi
}

# Function to run performance tests
run_performance_tests() {
    print_status "Running performance tests..."
    
    if npm run jest -- --config="$TEST_CONFIG" --testTimeout=30000 --verbose --testPathPattern="performance|Performance"; then
        print_success "Performance tests completed"
        return 0
    else
        print_warning "Performance tests had issues"
        return 1
    fi
}

# Function to run accessibility tests
run_accessibility_tests() {
    print_status "Running accessibility tests..."
    
    if npm run jest -- --config="$TEST_CONFIG" --testPathPattern="accessibility|Accessibility|MobileAndAccessibility"; then
        print_success "Accessibility tests completed"
        return 0
    else
        print_error "Accessibility tests failed"
        return 1
    fi
}

# Function to generate coverage report
generate_coverage() {
    print_status "Generating coverage report..."
    
    if npm run jest -- --config="$TEST_CONFIG" --coverage --coverageDirectory="$COVERAGE_DIR" --watchAll=false; then
        print_success "Coverage report generated in $COVERAGE_DIR"
        
        # Check coverage thresholds
        if [ -f "$COVERAGE_DIR/coverage-summary.json" ]; then
            print_status "Coverage summary:"
            node -e "
                const summary = require('./$COVERAGE_DIR/coverage-summary.json');
                const total = summary.total;
                console.log(\`  Lines: \${total.lines.pct}%\`);
                console.log(\`  Functions: \${total.functions.pct}%\`);
                console.log(\`  Branches: \${total.branches.pct}%\`);
                console.log(\`  Statements: \${total.statements.pct}%\`);
                
                if (total.lines.pct < 85 || total.functions.pct < 85 || 
                    total.branches.pct < 85 || total.statements.pct < 85) {
                    console.log('⚠️  Coverage below threshold');
                    process.exit(1);
                }
            "
        fi
        return 0
    else
        print_error "Coverage generation failed"
        return 1
    fi
}

# Function to run integration tests
run_integration_tests() {
    print_status "Running integration tests..."
    
    if npm run jest -- --config="$TEST_CONFIG" --testPathPattern="T030Integration" --verbose; then
        print_success "Integration tests completed"
        return 0
    else
        print_error "Integration tests failed"
        return 1
    fi
}

# Main execution
main() {
    local test_mode="$1"
    local failed_tests=0
    
    print_status "Starting T030 User Preferences Enhancement test suite"
    print_status "Test mode: ${test_mode:-all}"
    
    case "$test_mode" in
        "theme")
            run_test_suite "Theme Preferences" "ThemePreferences" || ((failed_tests++))
            ;;
        "notifications")
            run_test_suite "Notification Preferences" "NotificationPreferences" || ((failed_tests++))
            ;;
        "upload")
            run_test_suite "Upload Preferences" "UploadPreferences" || ((failed_tests++))
            ;;
        "accessibility")
            run_accessibility_tests || ((failed_tests++))
            ;;
        "mobile")
            run_test_suite "Mobile Interface" "MobileAndAccessibility" || ((failed_tests++))
            ;;
        "migration")
            run_test_suite "Settings Migration" "SettingsMigration" || ((failed_tests++))
            ;;
        "integration")
            run_integration_tests || ((failed_tests++))
            ;;
        "performance")
            run_performance_tests || ((failed_tests++))
            ;;
        "coverage")
            generate_coverage || ((failed_tests++))
            ;;
        "ci")
            print_status "Running CI test suite..."
            
            # Run all component tests
            run_test_suite "Theme Preferences" "ThemePreferences" || ((failed_tests++))
            run_test_suite "Notification Preferences" "NotificationPreferences" || ((failed_tests++))
            run_test_suite "Upload Preferences" "UploadPreferences" || ((failed_tests++))
            run_test_suite "Accessibility Options" "AccessibilityOptions" || ((failed_tests++))
            run_test_suite "Mobile Interface" "MobileAndAccessibility" || ((failed_tests++))
            run_test_suite "Settings Migration" "SettingsMigration" || ((failed_tests++))
            
            # Run integration tests
            run_integration_tests || ((failed_tests++))
            
            # Generate coverage
            generate_coverage || ((failed_tests++))
            ;;
        "all"|"")
            print_status "Running complete test suite..."
            
            # Individual component tests
            run_test_suite "Theme Preferences" "ThemePreferences" || ((failed_tests++))
            run_test_suite "Notification Preferences" "NotificationPreferences" || ((failed_tests++))
            run_test_suite "Upload Preferences" "UploadPreferences" || ((failed_tests++))
            run_test_suite "Accessibility Options" "AccessibilityOptions" || ((failed_tests++))
            run_test_suite "Mobile Interface" "MobileAndAccessibility" || ((failed_tests++))
            run_test_suite "Settings Migration" "SettingsMigration" || ((failed_tests++))
            
            # Integration and performance tests
            run_integration_tests || ((failed_tests++))
            run_performance_tests || ((failed_tests++))
            
            # Generate coverage
            generate_coverage || ((failed_tests++))
            ;;
        *)
            print_error "Unknown test mode: $test_mode"
            echo "Available modes: theme, notifications, upload, accessibility, mobile, migration, integration, performance, coverage, ci, all"
            exit 1
            ;;
    esac
    
    # Summary
    print_status "Test execution completed"
    
    if [ $failed_tests -eq 0 ]; then
        print_success "All tests passed! 🎉"
        exit 0
    else
        print_error "$failed_tests test suite(s) failed"
        exit 1
    fi
}

# Check if Jest is available
if ! command -v npx jest &> /dev/null; then
    print_error "Jest is not installed. Please run: npm install"
    exit 1
fi

# Check if test configuration exists
if [ ! -f "$TEST_CONFIG" ]; then
    print_error "Test configuration not found: $TEST_CONFIG"
    exit 1
fi

# Run main function with arguments
main "$@"