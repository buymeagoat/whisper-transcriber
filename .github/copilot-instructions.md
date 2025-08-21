# Repository rules for GitHub Copilot

Always follow these steps on any code change you propose. All steps below must be performed automatically by Copilot—no manual intervention required:


1) Tests
- Copilot must add or update tests that cover the change. If no tests are needed, Copilot must log the rationale in the PR body.

2) CHANGELOG
- Copilot must append an entry to `CHANGELOG.md` following Conventional Commits headings. If no release section exists, Copilot must create an `Unreleased` section.

3) Per-change log file
- Copilot must create `/logs/changes/change_<UTC>.md` with sections:
  - Summary (what/why)
  - Files Changed (list with 1–2 line rationale each)
  - Tests (what was added/updated, brief results)
  - Build Notes (placeholder if CI fills later)
  - Risk & Rollback (low/medium/high + steps)
  - Diff Summary (high-level bullets)

4) Build summary
- Copilot must create `/logs/builds/build_<UTC>.md` as a placeholder and link to CI results. CI will finalize details.

5) PR body
- Copilot must mirror the sections from the change log file and include checkboxes:
  - [ ] Tests updated
  - [ ] CHANGELOG updated
  - [ ] /logs/changes entry added
  - [ ] Build summary present

6) Commit and Push
- Copilot must automatically stage, commit (with a conventional message), and push all changes after every modification—no manual git steps required.

7) Repository Hygiene
- Copilot must automatically identify and remove obsolete files, empty directories, and legacy artifacts as part of every change.

8) Risk & Rollback Documentation
- Copilot must document risk level and rollback steps for every change in the log file.

Conventions:
- Use UTC timestamps formatted as `YYYYMMDD_HHMMSS`.
- Commit messages use Conventional Commits (e.g., `feat(api): add rate limiter`).
- Respect linters/formatters; fix warnings.
- Never commit secrets. Do not commit `/logs/app/` or any `/raw/` logs.
