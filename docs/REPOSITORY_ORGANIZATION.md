# Repository Organization

This document describes the current repository structure and organization.

## Directory Structure

```
/
├── api/                    # FastAPI backend application
│   ├── middlewares/        # Custom middleware (security, rate limiting, etc.)
│   ├── routes/            # API route handlers
│   ├── services/          # Business logic services
│   ├── migrations/        # Database migrations
│   ├── utils/             # Utility functions
│   └── worker.py          # Celery worker for background tasks
├── frontend/              # React frontend application
├── scripts/               # Operational and deployment scripts
│   └── dev/               # Development and testing utilities
├── tests/                 # Unit and integration tests
├── docs/                  # Documentation and guides
├── reports/               # Generated test reports and analysis
├── cache/                 # Application cache directory
├── logs/                  # Application logs
├── uploads/               # File upload storage
└── models/                # AI model files
```

## Key Changes Made

### Development Scripts Reorganization
- Moved development utilities from root to `scripts/dev/`:
  - `auth_dev_bypass.py`
  - `comprehensive_integration_test.py`
  - `fix_authentication.py`
  - `init_sqlite_dev.py`
  - `test_all_functions.py`
  - `full_stack_function_mapper.py`

### Documentation Consolidation
- Moved all documentation from root to `docs/`:
  - `APPLICATION_REVIEW_RECOMMENDATIONS.md`
  - `COMPLETE_INTERACTION_FLOWS.md`
  - `FRONTEND_FUNCTION_TEST_MAP.md`
  - `FUNCTION_TEST_REPORT.md`
  - `MISSION_ACCOMPLISHED.md`
  - `QUICK_START_FUNCTIONAL.md`

### Core Application Structure
- Moved `worker.py` from root to `api/worker.py` for better organization
- Created `reports/` directory for test results and generated analysis
- Removed temporary and generated files from repository

### Benefits
1. **Cleaner Root Directory**: Essential files only at top level
2. **Logical Grouping**: Related files organized together
3. **Easier Navigation**: Clear separation between code, docs, and utilities
4. **Better Maintainability**: Predictable file locations
5. **Reduced Clutter**: Generated files excluded from repository

## File Location Guide

| File Type | Location | Purpose |
|-----------|----------|---------|
| API Code | `/api/` | Backend application logic |
| Frontend Code | `/frontend/` | React UI application |
| Documentation | `/docs/` | Guides, specifications, reports |
| Tests | `/tests/` | Unit and integration tests |
| Dev Scripts | `/scripts/dev/` | Development utilities |
| Ops Scripts | `/scripts/` | Deployment and operations |
| Reports | `/reports/` | Generated test and analysis reports |

This organization follows modern software development best practices and makes the repository more maintainable.
