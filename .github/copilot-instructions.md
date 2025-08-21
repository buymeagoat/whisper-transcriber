# Repository rules for GitHub Copilot

Always follow these steps on any code change you propose:

1) Tests
- Add or update tests that cover the change. If no tests are needed, explain why in the PR body.

2) CHANGELOG
- Append an entry to `CHANGELOG.md` following Conventional Commits headings.
- If no release section exists, create an `Unreleased` section.

3) Per-change log file
- Create `/logs/changes/change_<UTC>.md` with sections:
  - Summary (what/why)
  - Files Changed (list with 1–2 line rationale each)
  - Tests (what was added/updated, brief results)
  - Build Notes (placeholder if CI fills later)
  - Risk & Rollback (low/medium/high + steps)
  - Diff Summary (high-level bullets)

4) Build summary
- Create `/logs/builds/build_<UTC>.md` as a placeholder and link to CI results. CI will finalize details.

5) PR body
- Mirror the sections from the change log file and include checkboxes:
  - [ ] Tests updated
  - [ ] CHANGELOG updated
  - [ ] /logs/changes entry added
  - [ ] Build summary present

Conventions:
- Use UTC timestamps formatted as `YYYYMMDD_HHMMSS`.
- Commit messages use Conventional Commits (e.g., `feat(api): add rate limiter`).
- Respect linters/formatters; fix warnings.
- Never commit secrets. Do not commit `/logs/app/` or any `/raw/` logs.
