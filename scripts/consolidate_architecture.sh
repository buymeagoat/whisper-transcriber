#!/bin/bash
# Architecture Consolidation Script
# Project Manager Critical Path Implementation

set -e

echo "🚨 CRITICAL: Starting Architecture Consolidation"
echo "================================================"

# Phase 1: Assessment
echo "📊 Phase 1: Architecture Assessment"

echo "  1. Analyzing app/main.py structure..."
APP_LINES=$(wc -l < app/main.py)
echo "     - app/main.py: $APP_LINES lines"

echo "  2. Analyzing api/main.py structure..."
API_LINES=$(wc -l < api/main.py) 
echo "     - api/main.py: $API_LINES lines"

echo "  3. Checking route overlaps..."
# Extract route definitions from both files
grep -n "@app\." app/main.py > /tmp/app_routes.txt || true
grep -n "@app\." api/main.py > /tmp/api_routes.txt || true

echo "     - app/main.py routes: $(wc -l < /tmp/app_routes.txt)"
echo "     - api/main.py routes: $(wc -l < /tmp/api_routes.txt)"

# Phase 2: Backup Current State
echo ""
echo "💾 Phase 2: Creating Backup"
BACKUP_DIR="archive/development-artifacts/architecture-consolidation-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "  1. Backing up current architecture..."
cp app/main.py "$BACKUP_DIR/app_main_backup.py"
cp api/main.py "$BACKUP_DIR/api_main_backup.py"
echo "     - Backup created in: $BACKUP_DIR"

# Phase 3: Analysis Report
echo ""
echo "📋 Phase 3: Consolidation Analysis"

cat > "$BACKUP_DIR/consolidation_analysis.md" << 'EOF'
# Architecture Consolidation Analysis

## Current State
- **app/main.py**: Primary application (1400+ lines)
- **api/main.py**: Secondary application (391+ lines)

## Identified Issues
1. **Duplicate FastAPI Applications**: Two complete apps with overlapping functionality
2. **Route Conflicts**: Potential conflicts in endpoint definitions
3. **Middleware Duplication**: Security middleware in both applications
4. **Database Connections**: Multiple connection management systems
5. **Import Confusion**: Conflicting import paths

## Consolidation Strategy
1. **Primary Application**: Use api/main.py as foundation (cleaner structure)
2. **Feature Migration**: Move unique features from app/main.py to api/main.py
3. **Middleware Unification**: Consolidate to single security middleware
4. **Route Consolidation**: Merge all unique routes into single application
5. **Import Cleanup**: Update all references to use unified structure

## Risk Assessment
- **High Risk**: Breaking existing functionality
- **Medium Risk**: Import reference conflicts
- **Low Risk**: Performance impact

## Mitigation Plan
- Comprehensive testing before and after
- Incremental migration approach
- Backup and rollback procedures
- Route-by-route validation
EOF

echo "     - Analysis report created"

# Phase 4: Validation Setup
echo ""
echo "✅ Phase 4: Pre-Consolidation Validation"

echo "  1. Running existing tests..."
if python -m pytest tests/ -v --tb=short > "$BACKUP_DIR/pre_consolidation_tests.log" 2>&1; then
    echo "     ✅ All tests passing before consolidation"
else
    echo "     ⚠️  Some tests failing - logged for review"
fi

echo "  2. Checking import dependencies..."
# Check which files import from app vs api
find . -name "*.py" -exec grep -l "from app\." {} \; > "$BACKUP_DIR/app_imports.txt" 2>/dev/null || true
find . -name "*.py" -exec grep -l "from api\." {} \; > "$BACKUP_DIR/api_imports.txt" 2>/dev/null || true

APP_IMPORTS=$(wc -l < "$BACKUP_DIR/app_imports.txt")
API_IMPORTS=$(wc -l < "$BACKUP_DIR/api_imports.txt")

echo "     - Files importing from app/: $APP_IMPORTS"
echo "     - Files importing from api/: $API_IMPORTS"

# Phase 5: Consolidation Recommendation
echo ""
echo "🎯 Phase 5: Consolidation Recommendation"

cat > "CONSOLIDATION_PLAN.md" << EOF
# URGENT: Architecture Consolidation Required

## Project Manager Decision
**CRITICAL BLOCKER**: Dual FastAPI applications must be consolidated before continued development.

## Recommended Approach
1. **Target Architecture**: Single FastAPI application in api/ directory
2. **Migration Strategy**: Incremental feature migration with testing
3. **Timeline**: 1 week for consolidation, 1 week for validation

## Immediate Next Steps
1. **Manual Review Required**: Compare unique features in both applications
2. **Route Mapping**: Create comprehensive route comparison
3. **Feature Migration**: Move unique app/ features to api/
4. **Testing Validation**: Comprehensive test suite execution
5. **Import Updates**: Update all references throughout codebase

## Automation Ready
- Backup system: ✅ Implemented
- Test validation: ✅ Ready
- Analysis tools: ✅ Available
- Rollback plan: ✅ Prepared

## Status
**READY FOR MANUAL CONSOLIDATION**

Run this script completed pre-consolidation assessment.
Manual developer intervention required for safe consolidation.

Generated: $(date)
Backup Location: $BACKUP_DIR
EOF

echo "📋 CONSOLIDATION ASSESSMENT COMPLETE"
echo "================================================"
echo "✅ Status: Ready for manual consolidation"
echo "📁 Backup: $BACKUP_DIR"
echo "📋 Plan: CONSOLIDATION_PLAN.md"
echo ""
echo "⚠️  NEXT STEP: Manual developer review required"
echo "   Review CONSOLIDATION_PLAN.md for detailed next steps"
echo "================================================"