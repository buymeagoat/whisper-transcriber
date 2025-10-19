# Architecture Documentation - READ ME FIRST

> **Start Here**: How to use these architecture documents to understand, verify, and maintain the Whisper Transcriber system

## 📋 Table of Contents

1. [Document Overview](#document-overview)
2. [How to Use These Docs](#how-to-use-these-docs)
3. [Verification Workflows](#verification-workflows)
4. [Running the Scanner](#running-the-scanner)
5. [Interpreting Diffs](#interpreting-diffs)
6. [Maintenance Guide](#maintenance-guide)

---

## Document Overview

This architecture documentation suite provides comprehensive coverage of the Whisper Transcriber system:

### 📁 Document Structure

| Document | Purpose | When to Use |
|----------|---------|-------------|
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | Complete system architecture with diagrams | System overview, onboarding, design decisions |
| **[ICD.md](ICD.md)** | Interface Control Document | API changes, integration planning, breaking changes |
| **[TRACEABILITY.md](TRACEABILITY.md)** | Code-to-test mapping | Test planning, coverage analysis, risk assessment |
| **[INVENTORY.json](INVENTORY.json)** | Machine-readable codebase inventory | Automated analysis, dependency tracking |
| **[READ_ME_FIRST.md](READ_ME_FIRST.md)** | This document - usage guide | Getting started with architecture docs |

### 🎯 Intended Audience

- **Developers**: Understanding system design and making changes
- **DevOps Engineers**: Deployment, monitoring, and operational concerns  
- **Product Managers**: Feature impact analysis and technical planning
- **Security Engineers**: Attack surface analysis and threat modeling
- **QA Engineers**: Test planning and coverage validation

---

## How to Use These Docs

### For New Team Members

1. **Start with [ARCHITECTURE.md](ARCHITECTURE.md)** - Get the big picture
   - Read System Context and C4 diagrams
   - Understand the three-container architecture
   - Review critical data flows

2. **Review [ICD.md](ICD.md)** - Understand the interfaces
   - Study API contracts and versioning
   - Learn about external dependencies
   - Understand stability guarantees

3. **Check [TRACEABILITY.md](TRACEABILITY.md)** - See what's tested
   - Identify test coverage gaps
   - Understand risk areas
   - Plan your testing approach

### For System Changes

**Before Making Changes:**
1. Run the inventory scanner to establish baseline
2. Check [ICD.md](ICD.md) for interface stability guarantees
3. Review [TRACEABILITY.md](TRACEABILITY.md) for affected tests

**After Making Changes:**
1. Update relevant architecture documents
2. Re-run scanner to detect changes
3. Update tests as identified in traceability matrix
4. Validate no breaking changes introduced

### For Incident Investigation

1. **Check [ARCHITECTURE.md](ARCHITECTURE.md)** for system interactions
2. **Use [INVENTORY.json](INVENTORY.json)** to trace function calls
3. **Review [TRACEABILITY.md](TRACEABILITY.md)** for test coverage
4. **Validate interfaces in [ICD.md](ICD.md)** for contract violations

---

## Verification Workflows

### 🔍 System Health Verification

```bash
# 1. Check all services are running
docker-compose ps

# 2. Verify API endpoints
curl -f http://localhost:8000/health
curl -f http://localhost:8000/metrics  # Admin only

# 3. Test WebSocket connectivity
# Use browser dev tools or wscat
wscat -c ws://localhost:8000/ws/progress/test-id

# 4. Verify worker health
docker exec whisper-worker celery -A app.worker inspect ping

# 5. Check queue status
docker exec whisper-worker celery -A app.worker inspect active
```

### 🧪 API Contract Verification

```bash
# Test core endpoints match ICD specifications
python tools/verify_api_contracts.py

# Expected output:
# ✅ POST /token - contract valid
# ✅ POST /transcribe - contract valid
# ❌ GET /admin/stats - response schema mismatch
```

### 📊 Test Coverage Verification

```bash
# Run test suite with coverage
pytest --cov=app --cov-report=html tests/

# Check coverage against traceability matrix
python tools/validate_test_coverage.py

# Expected output:
# Coverage Summary:
# - API Endpoints: 25% (3/12 tested)
# - Background Jobs: 0% (0/4 tested)
# - Data Flows: 15% (1/8 tested)
```

### 🔄 Data Flow Verification

```bash
# Test complete upload-to-transcript flow
python tools/test_e2e_flow.py

# Expected output:
# 1. ✅ File upload successful
# 2. ✅ Job created in database
# 3. ✅ Task queued in Redis
# 4. ✅ Worker processed task
# 5. ✅ Transcript saved
# 6. ✅ WebSocket notification sent
```

---

## Running the Scanner

### Basic Usage

```bash
# Generate fresh inventory
python tools/repo_inventory.py

# Output location: docs/architecture/INVENTORY.json
# Processing time: ~30 seconds for typical codebase
```

### Advanced Options

```bash
# Custom output location
python tools/repo_inventory.py /path/to/custom/inventory.json

# Verbose mode with debug info
python tools/repo_inventory.py --verbose

# Include test files in analysis
python tools/repo_inventory.py --include-tests
```

### Scanner Output

The scanner generates a comprehensive JSON inventory:

```json
{
  "metadata": {
    "generated_at": "2025-10-15T00:00:00Z",
    "repository_root": "/path/to/repo",
    "scan_version": "1.0"
  },
  "modules": {
    "app.main": {
      "functions": ["login", "register", "create_transcription"],
      "exports": ["app", "lifespan"],
      "loc": 800
    }
  },
  "api_endpoints": [
    {
      "method": "POST",
      "path": "/token",
      "function_name": "login",
      "file_path": "app/main.py",
      "line_number": 546
    }
  ],
  "statistics": {
    "total_modules": 45,
    "total_functions": 234,
    "total_api_endpoints": 12
  }
}
```

### Scheduled Scanning

Set up automated scanning in CI/CD:

```yaml
# .github/workflows/architecture-scan.yml
name: Architecture Inventory
on:
  push:
    branches: [main]
  pull_request:

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run inventory scanner
        run: python tools/repo_inventory.py
      - name: Upload inventory artifact
        uses: actions/upload-artifact@v3
        with:
          name: architecture-inventory
          path: docs/architecture/INVENTORY.json
```

---

## Interpreting Diffs

### Understanding Inventory Changes

When comparing inventory files, focus on these sections:

#### 1. API Changes

```diff
  "api_endpoints": [
    {
      "method": "POST",
-     "path": "/transcribe",
+     "path": "/v2/transcribe",
      "function_name": "create_transcription"
    }
  ]
```

**Impact**: Breaking change - requires client updates

#### 2. Function Signature Changes

```diff
  "functions": {
    "app.main.login": {
-     "signature": "def login(username: str, password: str)",
+     "signature": "def login(username: str, password: str, remember_me: bool = False)",
      "is_endpoint": true
    }
  }
```

**Impact**: Non-breaking change - optional parameter added

#### 3. Module Dependencies

```diff
  "modules": {
    "app.main": {
      "imports": [
        "fastapi",
        "sqlalchemy",
+       "redis"
      ]
    }
  }
```

**Impact**: New dependency - update requirements.txt

### Critical Changes to Monitor

**🚨 High Impact Changes**:
- API endpoint path or method changes
- Required parameter additions/removals
- Function signature changes for public APIs
- Database schema modifications

**⚠️ Medium Impact Changes**:
- New module dependencies
- Function relocations between modules
- Optional parameter additions
- New background tasks

**ℹ️ Low Impact Changes**:
- Documentation updates
- Internal function refactoring
- Code formatting changes
- Test file additions

### Change Review Checklist

- [ ] **Breaking Changes**: Any API contract violations?
- [ ] **Dependencies**: New external dependencies added?
- [ ] **Security**: Any new external service integrations?
- [ ] **Performance**: Function call path changes affecting hot paths?
- [ ] **Testing**: Coverage impact for modified functions?

---

## Maintenance Guide

### Weekly Tasks

- [ ] **Run inventory scanner** and commit updated INVENTORY.json
- [ ] **Review traceability matrix** for new test gaps
- [ ] **Check API contract compliance** with ICD specifications
- [ ] **Validate architectural diagrams** still match implementation

### Monthly Tasks

- [ ] **Update architecture diagrams** for significant changes
- [ ] **Review and update ICD** for any interface changes
- [ ] **Assess test coverage gaps** and plan improvements
- [ ] **Validate system health** using verification workflows

### Before Major Releases

- [ ] **Complete architecture review** with stakeholders
- [ ] **Update all documentation** for new features
- [ ] **Validate backward compatibility** for API changes
- [ ] **Run comprehensive verification** workflows
- [ ] **Update versioning and change management** policies

### Document Update Triggers

Update documents when these changes occur:

| Change Type | Documents to Update |
|-------------|-------------------|
| **New API Endpoint** | ARCHITECTURE.md, ICD.md, TRACEABILITY.md |
| **API Contract Change** | ICD.md, TRACEABILITY.md |
| **New Component** | ARCHITECTURE.md |
| **External Service Integration** | ARCHITECTURE.md, ICD.md |
| **Security Changes** | All documents |
| **Database Schema Changes** | ARCHITECTURE.md, ICD.md |

### Automation Opportunities

Consider automating these maintenance tasks:

```bash
# 1. Daily inventory updates
crontab -e
0 2 * * * cd /path/to/repo && python tools/repo_inventory.py

# 2. Weekly diff reports  
0 9 * * 1 cd /path/to/repo && python tools/generate_weekly_diff.py

# 3. API contract validation
# Include in CI/CD pipeline for every PR

# 4. Dead link checking in documentation
# Monthly cron job to validate all links
```

---

## Troubleshooting

### Common Issues

**Scanner fails with import errors:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt
```

**Inventory shows missing modules:**
```bash
# Check for syntax errors in Python files
python -m py_compile app/main.py
```

**Diagrams not rendering in GitHub:**
```bash
# Validate Mermaid syntax
npx @mermaid-js/mermaid-cli --version
npx mmdc -i docs/architecture/ARCHITECTURE.md -o test.png
```

### Getting Help

- **Architecture Questions**: Review [ARCHITECTURE.md](ARCHITECTURE.md) first
- **API Issues**: Check [ICD.md](ICD.md) for contract specifications
- **Test Planning**: Use [TRACEABILITY.md](TRACEABILITY.md) for coverage analysis
- **System Verification**: Follow workflows in this document

---

## Success Metrics

Track these metrics to ensure documentation effectiveness:

- **Onboarding Time**: New developers productive within 2 days
- **Change Safety**: Zero production incidents from undocumented changes
- **Test Coverage**: Maintain >80% coverage for critical paths
- **Documentation Freshness**: Updates within 1 week of code changes

---

*Keep this document updated as the architecture documentation system evolves.*
