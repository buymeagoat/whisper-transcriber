# Repository rules for GitHub Copilot

Always follow these steps on any code change you propose. All steps below must be performed automatically by Copilot—no manual intervention required:

## MANDATORY: Task Completion Workflow

After completing ANY development task, Copilot MUST run:
```bash
./scripts/ai_task_complete.sh
```

This enforces all requirements below automatically and includes MANDATORY validation. DO NOT SKIP THIS STEP.

## MANDATORY: TASKS.md Updates

**EVERY task completion MUST update TASKS.md:**
1. Change task status from `- [ ]` to `- [x]`
2. Add completion marker: `✅ **COMPLETED**`
3. Include detailed description of what was implemented
4. Format example:
```markdown
- [x] **T036**: Real-time Collaboration Features ✅ **COMPLETED**
  - WebSocket infrastructure for real-time communication with session management
  - Operational transform algorithm for conflict-free collaborative editing
  - Shared project workspaces with user permissions and project management
  - Real-time comments & annotations with threading and notification system
  - Complete React UI components for collaborative editing experience
```

## MANDATORY: Comprehensive Testing

**EVERY task completion MUST include comprehensive testing:**
1. **Add/Update Tests**: Create or modify test files for new functionality
   - Follow naming: `tests/test_<feature>.py`
   - Include unit tests, integration tests, and edge cases
   - Test both success and failure scenarios
2. **Run Test Suite**: Execute full test suite before completion
   - Backend: `pytest tests/ --cov=api`
   - Frontend: `npm test` 
   - Document test results
3. **Test Coverage**: Maintain or improve test coverage
   - Generate coverage reports
   - Address any gaps in critical functionality
4. **Test Documentation**: Document testing in change logs
   - What tests were added/updated
   - Test results and coverage metrics
   - Any known testing limitations

## Detailed Requirements

1) **Repository Cleanup**
- Copilot must move any temporary files, test scripts, or summaries out of repository root
- Test files go to `temp/` directory
- Documentation/summaries go to `docs/development/`
- Remove any `.tmp`, `.temp`, or other temporary artifacts
- Clean up empty directories and build artifacts

2) **Tests**
- Copilot must add or update tests that cover the change. If no tests are needed, Copilot must log the rationale in the change log.

3) **Documentation Updates**
- Copilot must update `CHANGELOG.md` following Conventional Commits headings
- Update `docs/api_integration.md` for any API changes
- Update `docs/frontend_architecture.md` for any frontend changes
- Create `README.md` sections if missing

4) **Per-change log file**
- Copilot must create `/logs/changes/change_<UTC>.md` with sections:
  - Summary (what/why)
  - Files Changed (list with 1–2 line rationale each)
  - Tests (what was added/updated, brief results)
  - Build Notes (placeholder if CI fills later)
  - Risk & Rollback (low/medium/high + steps)
  - Diff Summary (high-level bullets)

5) **Build summary**
- Copilot must create `/logs/builds/build_<UTC>.md` as a placeholder and link to CI results

6) **Commit and Push**
- Copilot must automatically stage, commit (with a conventional message), and push all changes
- Use format: `type(scope): description`
- Include detailed commit body with change rationale

7) **Repository Hygiene Enforcement**
- Pre-commit hook validates no temporary files in root
- Automated cleanup moves files to proper locations
- Documentation validation ensures updates accompany code changes

8) **File Organization Rules**
- `/temp/` - Temporary files, test scripts, development artifacts
- `/docs/` - All documentation, architecture notes, API docs
- `/logs/changes/` - Per-change documentation 
- `/logs/builds/` - Build and CI summaries
- Root directory - Only essential project files

## Automation Scripts

- `./scripts/ai_task_complete.sh` - Main task completion workflow
- `./scripts/post_task_cleanup.sh` - Detailed cleanup and commit process
- `.git/hooks/pre-commit` - Validates repository state before commits

## Enforcement

The enhanced enforcement system ensures compliance through multiple layers:

### 1. Pre-Task Validation
- `./scripts/validate_task_completion.sh` - Comprehensive pre-completion validation
- Checks TASKS.md updates, testing requirements, and documentation
- MUST pass before ai_task_complete.sh will proceed

### 2. Pre-Commit Hook Enforcement  
The pre-commit hook will REJECT commits that:
- Have temporary files in repository root
- Make code changes without documentation updates
- Don't follow the established file organization
- Update TASKS.md without proper completion markers (✅ **COMPLETED**)
- Complete tasks without corresponding test updates
- Submit test files without actual test functions

### 3. Automated Validation
- TASKS.md format validation (completion markers, descriptions)
- Test file quality checks (presence of test functions)
- Documentation update requirements
- Repository hygiene enforcement

**Copilot must ALWAYS run `./scripts/ai_task_complete.sh` at the end of every task.**
**The script will automatically validate all requirements before proceeding.**

Conventions:
- Use UTC timestamps formatted as `YYYYMMDD_HHMMSS`.
- Commit messages use Conventional Commits (e.g., `feat(api): add rate limiter`).
- Respect linters/formatters; fix warnings.
- Never commit secrets. Do not commit `/logs/app/` or any `/raw/` logs.
