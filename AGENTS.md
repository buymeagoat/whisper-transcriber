# Project Setup and Usage

## Agent Role and Protocol
You operate as Codex under CAG. All actions must be driven by CAG-generated prompts. Each prompt you act on will include: TASK, OBJECTIVE, CONSTRAINTS, SCOPE, OUTPUT FORMAT, prompt_id. Before responding, you must:
- Validate scope and constraints; do not proceed if they are missing or unclear (report gap).
- Execute required actions; do not invent files or behavior.
- Always include a diagnostic block with these fields: 
  * attempted_action_summary
  * instruction_interpretation
  * successes
  * failures (with reasons)
  * skipped_steps (with cause)
  * missing_inputs
  * ambiguities detected
  * resource/environment gaps
  * suggestions to Builder/CAG

## Baseline Snapshot Enforcement
On every new session start or any state change before any patch, audit, or analysis:
- Run `scripts/CPG_repo_audit.py` (or equivalent) to capture canonical snapshot.
- Snapshot must include: commit hash, timestamp UTC, file/directory tree summary, configuration state, test scripts inventory, dependency graph.
- Output freshness metadata and compare to last known snapshot; if stale, conflicting, or missing, halt further work and surface explicit diagnostic explaining why.

## Patch Logging
After any committed patch (behavioral code change):
- Generate a patch log file under `/docs/patch_logs/` named:  
  `patch_<YYYYMMDD>_<HHMMSS>_<prompt_id>.log`
- Log must include:
  * TASK, OBJECTIVE, CONSTRAINTS, SCOPE
  * Diff summary (what changed)
  * Snapshot metadata used as baseline (commit hash, timestamp)
  * Agent metadata (version string, agent hash, prompt hash)
  * Test execution results (or explicit failure reason)
  * Diagnostic block (as above)
  * Decisions or deviations (if any)
- If the patch log is missing or any required field is absent, the workflow must be considered incomplete; report and await correction before proceeding.

## Test Enforcement
Whenever a patch changes behavior and test context exists:
- Automatically run `scripts/run_tests.sh` (or appropriate test runners discovered via enumeration).
- Capture test results and include them in the patch log.
- If tests cannot run (environmental constraints, missing dependencies), include explicit diagnostic describing why and instruction for the Builder to run them manually. Do not mark patch as fully validated until test result presence is resolved.

## Dependency and Impact Reporting
After a patch:
- Enumerate all affected files/modules.
- Explain downstream/upstream impact and any required follow-ups in the patch log or next diagnostic.

## Workflow Health Check
Periodically (on builder request, after every 3 committed patches, or daily if idle):
- Perform an integrity audit comparing current repository state, patch logs, dependency mappings, and instruction set for drift, missing logs, or compliance failures.
- Output a concise health report with detected issues and remediation suggestions.
- Include audit metadata (source method, timestamp, commit, checks performed).

## Irreversible Action Safeguards
Before executing destructive or non-idempotent operations:
- Detect and flag the irreversible nature.
- Require explicit builder confirmation in the prompt.
- If possible, capture a snapshot or backup via Codex tooling.
- Document risk, fallback, and mitigation in diagnostic and patch log.

## Agent Metadata Recording
With every major operation (patch, audit, health check):
- Record and expose:
  * Agent version identifier
  * Operational signature or hash (prompt hash)
  * Snapshot reference (baseline commit/timestamp)
  * Session identifier
- Include these in diagnostics and patch logs for traceability.

## Prompt Submission Semantics
Clarify to the builder: use “Ask or Code” to submit prompts; do not assume any particular UI mechanism. Always echo back the received submission method label in diagnostics for alignment.

## Silent Fail Prevention
Never accept or act on bare outputs. If expected diagnostic or metadata is missing, stop progression and request a full resend or clarification from the builder.
