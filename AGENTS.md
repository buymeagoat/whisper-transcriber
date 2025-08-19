<!-- Auto-generated from OPERATING_BLUEPRINT.md; do not edit directly. -->
Bundle-ID: 1
Bundle-UTC: 20250819
Blueprint-Version: 2
Source-of-Truth: OPERATING_BLUEPRINT.md
Generated-At: 20250819_192308

# Codex Instructions (Draft)

Bundle 1 @ 20250819 • Blueprint 2 • OPERATING_BLUEPRINT.md • Generated 20250819_192308

> Regenerate from the Blueprint; do not edit directly.

## Role
Codex edits the repository, runs tests, and reports diagnostics. Only Codex commits to the repo.

## Visibility & Mirrors
Codex reads `AGENTS.md` and `/docs/CAG_spec.md` but cannot view `/docs/AGENTS_mirror.md` or CAG internals. Model G2 (“green”) requires `AGENTS.md` and `/docs/AGENTS_mirror.md` to be byte-equal and to share Bundle-ID and Bundle-UTC. Drift → halt and notify Builder.

## Lanes
* **Fast** – single-file or routine changes; ensure tests run and patch log exists.
* **Audit** – multi-file or governance changes; request builder confirmation, extra tests, and rollback notes.

## Patch Logs & DIAGMETA
Every commit writes `/docs/patch_logs/patch_<timestamp>_<short>.log` including bundle fields, commit hash, diff summary, test results, and the nine-key DIAGMETA checklist in order.
