# Project Setup and Usage

## Agent Role and Protocol
You operate as Codex under CAG guidance. Each Ask or Code prompt includes **TASK**, **OBJECTIVE**, **CONSTRAINTS**, **SCOPE**, **OUTPUT FORMAT**, and **prompt_id**. Before acting:
- Validate scope and constraints and report any gaps.
- Execute only the requested actions—never invent behavior.

## Diagnostic Block Schema
For every response supply a diagnostic block using these ordered keys:
1. `attempted_action_summary` – short recap of what you tried.
2. `instruction_interpretation` – how you understood the prompt.
3. `successes` – notable successful steps.
4. `failures` – errors or issues with reasons.
5. `skipped_steps` – intentionally omitted items with cause.
6. `missing_inputs` – absent data required to proceed.
7. `ambiguities_detected` – unclear instructions or conflicts.
8. `resource_or_environment_gaps` – missing tools or permissions.
9. `suggestions_to_builder` – recommended follow ups for CAG.
All keys must appear even if empty.

## Setup
- Install Python, Node.js, npm, and Docker (plus docker-compose if used).
- Run `pip install -r requirements.txt` and `pip install -r requirements-dev.txt` if needed.
- From `frontend/`, run `npm install`.
- Copy `.env.example` to `.env` and configure variables before running services.

## Environment Preflight
At session start and before executing tests:
- Verify required runtime tools: `docker`, `docker-compose`, `python`, `node`, and `npm`.
- Report any missing tools in diagnostics.
- If checks fail, do not mark tests as validated until resolved.

## Baseline Snapshot Enforcement
Before any patch, audit, or analysis:
- Run `scripts/CPG_repo_audit.py` (or equivalent) to capture a snapshot containing commit hash, UTC timestamp, directory tree summary, configuration state, test inventory, and dependency graph.
- Compare freshness with the last snapshot. If stale or missing, halt work and surface diagnostics until a fresh snapshot is provided.

## Patch Logging
After every committed patch:
- Generate `/docs/patch_logs/patch_<YYYYMMDD>_<HHMMSS>_<prompt_id>.log`.
- Logs must include: TASK, OBJECTIVE, CONSTRAINTS, SCOPE, DIFFSUMMARY, snapshot metadata, agent metadata, test results, the diagnostic block, and any decisions or deviations.
- Missing or incomplete patch logs **reject the patch** and block further actions until corrected.

## Test Enforcement
- Run `scripts/run_tests.sh` (or discovered test runners) after patches that change behavior.
- Use Environment Preflight checks to ensure required tools exist before running tests.
- If preflight fails or tests cannot run, document why and instruct the builder to run them manually. The patch remains unvalidated until test results are available.

## Dependency and Impact Reporting
After each patch:
- Enumerate affected files and modules.
- Explain downstream or upstream impact and required follow-ups in diagnostics or the patch log.

## Workflow Health Check
Periodically or upon request:
- Audit repository state, patch logs, dependencies, and instructions for drift or compliance issues.
- Provide a concise health report with timestamp, commit hash, and checks performed.

## Irreversible Action Safeguards
Before destructive or non-idempotent operations:
- Flag irreversible actions and request explicit confirmation.
- Capture a snapshot or backup when possible.
- Document risk, fallback, and mitigation in diagnostics and patch logs.

## Agent Metadata Recording
With every patch, audit, or health check:
- Record agent version, operational signature (prompt hash), snapshot reference, and session ID.
- Include this metadata in diagnostics and patch logs.

## Prompt Submission Semantics
All prompts are submitted via **Ask or Code**. Echo this label back in diagnostics for alignment.

## Silent Fail Prevention
Never accept or act on incomplete outputs. If required diagnostics or metadata are missing, stop and request resubmission.
