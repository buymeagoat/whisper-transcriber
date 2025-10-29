#!/bin/bash
"""
FILE ORGANIZATION PLAN
======================

This script systematically organizes all the analysis and testing files 
created during the testing phase into proper directories.
"""

set -e

echo "🧹 ORGANIZING REPOSITORY FILE SPRAWL"
echo "======================================"

# Documentation files - move to docs/
echo "📚 Moving documentation files..."

# Analysis reports -> docs/analysis/
mv APPLICATION_INSPECTION_REPORT.md docs/analysis/ 2>/dev/null || true
mv ARCHITECTURE_ANALYSIS.md docs/analysis/ 2>/dev/null || true
mv CODEX_REVIEW_PACKAGE.md docs/analysis/ 2>/dev/null || true
mv CODE_QUALITY_REPORT.md docs/analysis/ 2>/dev/null || true
mv REVIEW_GUIDE.md docs/analysis/ 2>/dev/null || true

# Testing reports -> docs/testing/
mv COMPREHENSIVE_TESTING_ASSESSMENT.md docs/testing/ 2>/dev/null || true
mv COMPREHENSIVE_TESTING_FRAMEWORK_COMPLETE.md docs/testing/ 2>/dev/null || true
mv COMPREHENSIVE_TESTING_STRATEGY.md docs/testing/ 2>/dev/null || true
mv ITERATIVE_TESTING_SUCCESS.md docs/testing/ 2>/dev/null || true
mv TESTING_ASSESSMENT_REPORT.md docs/testing/ 2>/dev/null || true
mv TESTING_CHECKLIST.md docs/testing/ 2>/dev/null || true
mv TESTING_GAP_ANALYSIS.md docs/testing/ 2>/dev/null || true
mv TESTING_REBUILD_SUCCESS_REPORT.md docs/testing/ 2>/dev/null || true
mv TEST_CHANGE_PIPELINE.md docs/testing/ 2>/dev/null || true

# Operational reports -> docs/operations/
mkdir -p docs/operations
mv REAL_TIME_MONITORING.md docs/operations/ 2>/dev/null || true
mv REBUILD_SUCCESS_REPORT.md docs/operations/ 2>/dev/null || true
mv REMEDIATION_COMPLETE.md docs/operations/ 2>/dev/null || true
mv STARTUP_STATUS.md docs/operations/ 2>/dev/null || true

# Tools and scripts
echo "🔧 Moving analysis and testing tools..."

# Analysis tools -> tools/analysis/
mv comprehensive_analysis.py tools/analysis/ 2>/dev/null || true

# Testing tools -> tools/testing/
mv critical_tests.py tools/testing/ 2>/dev/null || true
mv test_runner.py tools/testing/ 2>/dev/null || true
mv user_workflow_tests.py tools/testing/ 2>/dev/null || true

# Simulation scripts -> tools/testing/simulation/
mkdir -p tools/testing/simulation
mv test_browser_simulation.js tools/testing/simulation/ 2>/dev/null || true
mv test_comprehensive_simulation.js tools/testing/simulation/ 2>/dev/null || true
mv test_frontend_simulation.js tools/testing/simulation/ 2>/dev/null || true
mv test_final_validation.js tools/testing/simulation/ 2>/dev/null || true
mv test_frontend_direct.html tools/testing/simulation/ 2>/dev/null || true

# Operational scripts -> scripts/
mv emergency_rebuild.sh scripts/ 2>/dev/null || true
mv monitor_errors.sh scripts/ 2>/dev/null || true
mv verify_all_fixes.sh scripts/ 2>/dev/null || true

# Temporary/obsolete files -> temp/analysis-files/
echo "🗑️ Moving temporary files..."
mv test_auth.db temp/analysis-files/ 2>/dev/null || true

# Remove obsolete files that are no longer needed
echo "🗑️ Removing obsolete files..."
rm -f .build_validation_config 2>/dev/null || true
rm -f .testing_integration_config 2>/dev/null || true
rm -f .repo_hygiene.conf 2>/dev/null || true
rm -f security_scan_report.json 2>/dev/null || true
rm -f security_scan_report.md 2>/dev/null || true

echo "✅ File organization complete!"
echo ""
echo "📁 New structure:"
echo "  docs/analysis/ - Code and architecture analysis reports"
echo "  docs/testing/ - Testing strategy and results"
echo "  docs/operations/ - Operational monitoring and status"
echo "  tools/analysis/ - Analysis utilities and scripts"
echo "  tools/testing/ - Testing utilities and frameworks"
echo "  tools/testing/simulation/ - Browser and frontend simulation"
echo "  scripts/ - Operational maintenance scripts"
echo "  temp/analysis-files/ - Temporary analysis artifacts"