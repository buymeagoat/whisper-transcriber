# Whisper Transcriber Operating Blueprint

Version: 1.0 (Copilot-centric)  
Status: Adopted  
Source-of-Truth: This file

## Purpose

This Blueprint defines the single-role operating model for building and maintaining applications with GitHub Copilot as the primary automation engine. It replaces prior multi-role governance with repository-first scaffolding, standards, and logging. The goal: every change is consistent, testable, reviewable, and historically analyzable without per-change instructions.

## Repository Scaffolding (must exist before coding)

### Required top-level files
- README.md – project overview and quickstart.
- CHANGELOG.md – human-readable history (Conventional Commits headings).
- CONTRIBUTING.md – commit/PR rules, testing, security.
- SECURITY.md – security reporting & handling.
- CODEOWNERS – review ownership.
- .gitignore – must include transient logs (see below).
- .github/ – CI, PR template, and Copilot instructions.
- .github/copilot-instructions.md – repository instructions for Copilot.
- .github/pull_request_template.md – required sections for change/build/test logs.
- .github/workflows/ci.yml – lint, tests, build, artifact upload, and log sync.

### Logging topology (centralized under /logs)
- /logs/changes/ – one file per change (change_<UTC>.md).
- /logs/builds/ – build summaries (build_<UTC>.md) plus CI artifacts (or links).
- /logs/app/ – runtime application logs (rotated by app; not committed).
- /logs/audit/ – incident reports, postmortems (postmortem_<UTC>.md).
- /logs/metrics/ – optional JSONL telemetry for trend analysis.
- /logs/archive/ – quarterly archives if you want to prune the root log dirs.

### .gitignore minimum
- /logs/app/
- /logs/**/raw/**
- *.log
- *.tmp

### Time & naming conventions
- UTC timestamps only: YYYYMMDD_HHMMSS.
- Filenames: change_<UTC>.md, build_<UTC>.md, postmortem_<UTC>.md.

## Development Standards

### Style & Linting
- Language-appropriate formatters (e.g., Prettier/ESLint for JS/TS, Black/ruff for Python).
- Lint = blocking in CI.

### Testing & Coverage
- Unit tests for new or changed logic.
- Minimum coverage threshold defined per repo; CI enforces.
- Snapshot tests allowed but must be stable and explained.

### Security & Dependencies
- Secret scanning enabled; secrets never committed.
- Dependency updates use lockfiles and are reviewed.
- Known-vuln checks (e.g., npm audit/pip audit) run in CI.

## Change Management (what Copilot must do automatically)

On every code change, Copilot prepares the following artifacts (developer reviews and commits via PR):

### CHANGELOG.md
- Append an entry under the current release (or Unreleased) with type, scope, and summary.

### /logs/changes/change_<UTC>.md
Template:

# Change Log Entry (<UTC>)

## Summary
- What changed and why.

## Files Changed
- List of paths and a 1–2 line rationale each.

## Tests
- New/modified tests and results summary.

## Build Notes
- Build ID/URL or attached summary; key warnings if any.

## Risk & Rollback
- Risk level: low|medium|high
- Rollback steps: <commands/plan>

## Diff Summary
- High-level notable diffs (no large inline patches).

### /logs/builds/build_<UTC>.md (CI summary)
- Created by CI or prefilled by Copilot with placeholders that CI completes.

### PR Description (auto-filled)
- Mirrors change_<UTC>.md sections; includes checkboxes for lint/tests/build.

### Commit & PR Rules
- Commit messages follow Conventional Commits (e.g., feat(api): add rate limiter).
- PR template must be completed; PRs without tests or change logs are blocked by CI.
- Squash merges recommended; PR title becomes the squashed commit subject.

## CI/CD Expectations (reference implementation)

### Stages
- Verify – install, lint, static analysis, typecheck.
- Test – run tests, publish summary.
- Build – produce artifacts, publish summary.
- Sync Logs – write/update /logs/builds/build_<UTC>.md summary and attach full logs as CI artifacts; update CHANGELOG.md if missing entry.
- Status Gates – block merge on failures; enforce required files exist.

### Outputs
- Status checks: lint, tests, build, logs-updated.
- Artifacts: build outputs and raw logs (not committed).

### Retention & Analysis
- Committed: /logs/changes, /logs/builds (summaries), /logs/audit, /logs/metrics.
- Ignored: /logs/app (runtime), any /raw/ subfolders.
- Rotation: Build/change logs may be archived by quarter into /logs/archive/YYYYQn/.

## Minimal Governance (single-role)
- No multi-agent mirrors or role separation.
- The only authoritative governance is this Blueprint + CI.
- Copilot follows .github/copilot-instructions.md; developers review.

## Copilot Triggers (what to ask for)

### Fast change (single file, small):
TASK: <short>
OBJECTIVE: <acceptance criteria>
SCOPE: {edit: <path>}
Ensure: tests updated, CHANGELOG entry added, /logs/changes file created.

### Multi-file change (feature/refactor):
TASK: <short>
OBJECTIVE: <acceptance criteria>
SCOPE: {paths: [..]}
Ensure: tests added/updated, build passes, CHANGELOG & logs generated, rollback plan in change log.

## Adoption Checklist
- [ ] Required files exist
- [ ] Logging scaffold in place
- [ ] Copilot instructions file present
- [ ] PR template present
- [ ] CI workflow enforces standards
- [ ] CHANGELOG and per-change logs updated
- [ ] Build logs generated
- [ ] Security and test standards enforced

---

This Blueprint supersedes all previous multi-role governance. All legacy role-based files and instructions should be archived or deleted. All new work must follow this Copilot-centric, automation-first model.
