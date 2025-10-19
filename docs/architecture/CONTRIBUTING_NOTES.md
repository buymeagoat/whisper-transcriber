# Contributing to Architecture Documentation

This document explains how to maintain and update the architecture documentation as the codebase evolves.

## 🏗️ Architecture Documentation System

Our architecture documentation is **automatically maintained** through:

- **Inventory Scanner**: `tools/repo_inventory.py` scans the codebase and generates `INVENTORY.json`
- **Documentation Updater**: `tools/update_architecture_docs.py` refreshes docs based on inventory
- **GitHub Workflow**: `.github/workflows/architecture-inventory.yml` automates the process

## 📋 Developer Pre-PR Checklist

Before submitting a pull request that adds/modifies APIs, endpoints, or significant functionality:

### ✅ Required Steps

1. **Run the inventory scanner**:
   ```bash
   make arch.scan
   # OR manually: python tools/repo_inventory.py && python tools/update_architecture_docs.py
   ```

2. **Check for documentation changes**:
   ```bash
   make arch.check
   # OR manually: git diff docs/architecture/
   ```

3. **Update Interface Control Document (ICD)** if you:
   - Added new API endpoints
   - Changed request/response schemas
   - Modified authentication/authorization
   - Updated external service integrations

4. **Update Traceability Matrix** if you:
   - Added new modules without corresponding tests
   - Identified missing test coverage
   - Changed function signatures that affect testing

5. **Review generated changes**:
   - Verify `INVENTORY.json` reflects your changes
   - Check that `ARCHITECTURE.md` statistics are updated
   - Ensure `ICD.md` includes your new endpoints
   - Confirm `TRACEABILITY.md` shows correct coverage

### 🚨 What Triggers Documentation Updates

The architecture docs are automatically updated when code changes affect:

- **Python files** (`**/*.py`) - Functions, classes, imports, decorators
- **TypeScript/JavaScript** (`**/*.ts`, `**/*.tsx`, `**/*.js`) - Components, exports, API calls
- **Configuration** (`**/*.json`, `**/*.yml`, `**/*.yaml`) - Settings, dependencies, workflows

## 🤖 Automated Workflow

### How It Works

1. **Trigger**: Push to `main` or PR with relevant file changes
2. **Scan**: Repository inventory is regenerated
3. **Update**: Documentation sections are refreshed automatically
4. **PR Creation**: If changes detected, creates/updates PR titled `chore(docs): architecture inventory update`

### Workflow Links

- **Latest Workflow Run**: [Architecture Inventory](../../actions/workflows/architecture-inventory.yml)
- **Open Architecture PRs**: [Filter by `architecture-docs` label](../../pulls?q=is%3Apr+is%3Aopen+label%3Aarchitecture-docs)

## 📝 Manual Documentation Updates

### When to Update Manually

You should manually edit documentation when:

1. **Adding new system components** not detected by the scanner
2. **Updating architectural decisions** or design rationale
3. **Adding sequence diagrams** for new user flows
4. **Documenting integration patterns** with external services
5. **Updating security considerations** or deployment notes

### What Gets Auto-Updated vs Manual

| File | Auto-Updated Sections | Manual Sections |
|------|----------------------|-----------------|
| `ARCHITECTURE.md` | System statistics, component overview | Diagrams, design decisions, rationale |
| `ICD.md` | API endpoints table | Interface specifications, schemas, examples |
| `TRACEABILITY.md` | Test coverage summary | Detailed mappings, coverage goals |
| `INVENTORY.json` | Complete file | *Never edit manually* |

## 🛠️ Available Commands

### Makefile Commands

```bash
# Scan and update all architecture docs
make arch.scan

# Check if docs are stale (diff-only, fails if out of sync)
make arch.check

# Regenerate Mermaid diagrams (if templated)
make arch.diagrams

# Clean up generated artifacts
make arch.clean
```

### Manual Commands

```bash
# Generate inventory only
python tools/repo_inventory.py

# Update docs from existing inventory
python tools/update_architecture_docs.py

# Validate documentation links and syntax
python tools/validate_docs.py
```

## 🔍 Troubleshooting

### Common Issues

**Q: The workflow created a PR but I don't see my changes**
- Check if your changes are in files covered by the scanner (`.py`, `.ts`, `.js`, etc.)
- Run `make arch.scan` locally to see what gets detected
- Verify your endpoints use standard FastAPI decorators (`@app.get`, `@router.post`, etc.)

**Q: Documentation is out of sync after merging**
- The workflow only triggers on file changes in monitored paths
- Run `make arch.scan` manually if you suspect staleness
- Check the [latest workflow run](../../actions/workflows/architecture-inventory.yml) for errors

**Q: My API endpoint isn't showing up in ICD.md**
- Ensure it uses FastAPI decorators that the scanner recognizes
- Check the `INVENTORY.json` to see if the endpoint was detected
- Add manual documentation in `ICD.md` if the scanner can't detect it

### Getting Help

1. **Check the workflow logs**: [Latest runs](../../actions/workflows/architecture-inventory.yml)
2. **Review the inventory**: Look at `docs/architecture/INVENTORY.json` for what was detected
3. **Open an issue**: If the scanner misses important code patterns

## 🔄 Workflow Integration

### For Maintainers

- **Auto-PRs**: Review and merge architecture documentation PRs promptly
- **Labels**: Use `architecture-docs` label for all architecture-related PRs
- **Validation**: CI will fail PRs that make code changes without updating docs

### For Contributors

- **Documentation First**: Consider architecture impact before implementing
- **Early Feedback**: Run `make arch.scan` during development to catch issues early
- **Clean PRs**: Include architecture updates in the same PR as code changes when possible

---

*This documentation system ensures our architecture stays current with minimal manual effort while preserving the flexibility to add detailed explanations where needed.*
