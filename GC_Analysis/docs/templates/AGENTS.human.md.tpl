# Codex Instructions (Draft)

Bundle {{BUNDLE_ID}} @ {{BUNDLE_UTC}} • Blueprint {{BLUEPRINT_VERSION}} • {{SOURCE_OF_TRUTH}} • Generated {{GENERATED_AT}}

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
