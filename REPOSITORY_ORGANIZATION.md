# Repository Organization Guide

## 📁 Directory Structure

This repository follows modern best practices for Python web application organization:

```
whisper-transcriber/
├── 🏗️  api/                    # Backend API application
│   ├── middlewares/            # Custom middleware (security, rate limiting, etc.)
│   ├── routes/                 # API route handlers
│   ├── services/               # Business logic services
│   ├── migrations/             # Database migrations
│   ├── static/                 # Static assets
│   ├── utils/                  # Utility functions
│   ├── worker.py              # Celery worker (moved from root)
│   └── main.py                # FastAPI application entry point
│
├── 🎨 frontend/                # React frontend application
│   ├── src/                   # Source code
│   ├── public/                # Public assets
│   └── dist/                  # Built assets
│
├── 🔧 scripts/                 # Operational scripts
│   ├── dev/                   # Development utilities
│   │   ├── auth_dev_bypass.py
│   │   ├── comprehensive_integration_test.py
│   │   ├── fix_authentication.py
│   │   ├── init_sqlite_dev.py
│   │   ├── test_all_functions.py
│   │   └── full_stack_function_mapper.py
│   └── *.sh                   # Shell scripts for operations
│
├── 📚 docs/                    # All documentation
│   ├── api_reference.md
│   ├── architecture_diagram.md
│   ├── APPLICATION_REVIEW_RECOMMENDATIONS.md
│   ├── COMPLETE_INTERACTION_FLOWS.md
│   ├── FRONTEND_FUNCTION_TEST_MAP.md
│   ├── FUNCTION_TEST_REPORT.md
│   ├── MISSION_ACCOMPLISHED.md
│   └── QUICK_START_FUNCTIONAL.md
│
├── 🧪 tests/                   # Unit tests
├── 📊 reports/                 # Test reports and analysis
├── 🏗️  models/                 # ML model files
├── 📁 uploads/                 # Runtime upload directory
├── 📁 transcripts/             # Runtime transcript storage
├── 📁 logs/                    # Runtime log files
├── 🗂️  cache/                  # Runtime cache directory
└── 📋 Root configuration files
```

## 🚀 Recent Reorganization (October 2024)

### **Moved Files**

#### **Development Scripts** → `scripts/dev/`
- `auth_dev_bypass.py`
- `comprehensive_integration_test.py`
- `fix_authentication.py`
- `init_sqlite_dev.py`
- `test_all_functions.py`
- `full_stack_function_mapper.py`

#### **Documentation** → `docs/`
- `APPLICATION_REVIEW_RECOMMENDATIONS.md`
- `COMPLETE_INTERACTION_FLOWS.md`
- `FRONTEND_FUNCTION_TEST_MAP.md`
- `FUNCTION_TEST_REPORT.md`
- `MISSION_ACCOMPLISHED.md`
- `QUICK_START_FUNCTIONAL.md`

#### **Core Application** → `api/`
- `worker.py` → `api/worker.py`

#### **Test Reports** → `reports/`
- `comprehensive_test_report.json`
- `full_stack_test_results.json`
- `function_dependency_graph.json`
- `test_results.json`

### **Removed Files**
- Generated file lists (`all_files.txt`, `local_only_files.txt`, etc.)
- Empty configuration files (`.env.new`, `secret_key.txt`)
- Build artifacts and temporary files

## 📋 File Location Guidelines

### **Root Directory (Keep Minimal)**
Only essential configuration files should remain in root:
- `README.md` - Project overview
- `requirements.txt` - Python dependencies
- `docker-compose.yml` - Container orchestration
- `Dockerfile` - Container build instructions
- `pyproject.toml` - Python project configuration
- `.env.example` - Environment template
- `.gitignore` - Git exclusions

### **Where to Place New Files**

| File Type | Location | Examples |
|-----------|----------|----------|
| API Routes | `api/routes/` | `auth.py`, `jobs.py` |
| Business Logic | `api/services/` | `audio_service.py`, `user_service.py` |
| Database Models | `api/` | `models.py` |
| Middleware | `api/middlewares/` | `security_headers.py`, `rate_limit.py` |
| React Components | `frontend/src/components/` | `UploadForm.jsx` |
| Documentation | `docs/` | `*.md` files |
| Development Tools | `scripts/dev/` | Testing/debug utilities |
| Operational Scripts | `scripts/` | Build/deployment scripts |
| Unit Tests | `tests/` | `test_*.py` |
| Test Reports | `reports/` | `*.json`, analysis files |

## 🔄 Import Path Updates

After reorganization, update import statements:

```python
# OLD
from worker import celery_app

# NEW 
from api.worker import celery_app
```

## 🚫 Files to Never Commit

The enhanced `.gitignore` now prevents these from being committed:
- `*.deb`, `*.rpm` - Package files
- `whisper_dev.db` - Development database
- `venv/` - Virtual environments
- `uploads/*.wav`, `uploads/*.mp3` - Runtime audio files
- `uploads/logs/` - Runtime logs
- `reports/*.json` - Generated test reports (unless specifically needed)

## 🔧 Build System Updates

Key files updated for new structure:
- `Dockerfile` - Updated worker path: `COPY api/worker.py ./api/worker.py`
- `scripts/docker-entrypoint.sh` - Updated worker checks
- `scripts/diagnose_containers.sh` - Updated diagnostics
- `scripts/dev/test_all_functions.py` - Updated import paths

## ✅ Benefits of New Organization

1. **Cleaner Root** - Only essential files visible
2. **Logical Grouping** - Related files together
3. **Better Navigation** - Clear directory purposes
4. **Improved Maintainability** - Easier to find and modify code
5. **Professional Structure** - Follows industry standards
6. **Reduced Clutter** - Development tools separated from core code

## 🎯 Next Steps

1. Update any remaining scripts that reference old paths
2. Verify all imports work correctly
3. Test build process with new structure
4. Update deployment scripts if needed
5. Consider creating additional subdirectories as the project grows

---

*Last Updated: October 10, 2024*
*This reorganization improves maintainability while preserving all functionality.*
