# Repository rules for GitHub Copilot

Always follow these steps on any code change you propose. All steps below must be performed automatically by Copilot—no manual intervention required:

## MANDATORY: Task Completion Workflow

After completing ANY development task, Copilot MUST run:
```bash
./scripts/ai_task_complete.sh
```

This enforces all requirements below automatically. DO NOT SKIP THIS STEP.

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

The pre-commit hook will REJECT commits that:
- Have temporary files in repository root
- Make code changes without documentation updates
- Don't follow the established file organization

**Copilot must ALWAYS run `./scripts/ai_task_complete.sh` at the end of every task.**

Conventions:
- Use UTC timestamps formatted as `YYYYMMDD_HHMMSS`.
- Commit messages use Conventional Commits (e.g., `feat(api): add rate limiter`).
- Respect linters/formatters; fix warnings.
- Never commit secrets. Do not commit `/logs/app/` or any `/raw/` logs.
