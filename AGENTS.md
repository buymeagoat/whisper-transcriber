<!-- Guard-rail updates were applied per CAG v-order-1.2 wrap-up rules to ensure session safety and patch compliance. -->
# Project Setup and Usage

## Agent Role and Protocol
You operate as **Codex** under CAG guidance. Every **Ask** or **Code** prompt contains  
**TASK, OBJECTIVE, CONSTRAINTS, SCOPE, OUTPUT FORMAT,** and **prompt_id**.

Before acting you must:

1. Validate scope and constraints; surface any gaps or conflicts.  
2. Execute only what’s requested—never invent behavior.  

Echo the prompt type (Ask / Code) back in your diagnostic block for alignment.

---

## Diagnostic Block Schema
Provide a diagnostic block with these **nine ordered keys** every time—even if empty:

1. `attempted_action_summary`  
2. `instruction_interpretation`  
3. `successes`  
4. `failures`  
5. `skipped_steps`  
6. `missing_inputs`  
7. `ambiguities_detected`  
8. `resource_or_environment_gaps`
9. `suggestions_to_builder`

These keys follow CAG naming. Legacy aliases remain valid for backward compatibility,
e.g., `attempted_action_summary` ↔ `WhatAttempted`, `instruction_interpretation` ↔
`Why`, `successes` ↔ `Success`, `failures` ↔ `Failure`, `skipped_steps` ↔
`Omitted`, `missing_inputs` ↔ `Missing`, `ambiguities_detected` ↔ `Ambiguity`,
`resource_or_environment_gaps` ↔ `Resources`, `suggestions_to_builder` ↔ `Next`.

---

## Setup
* Install **Python**, **Node.js**, **npm**, **Docker**, and **docker-compose** (if used).  
* `pip install -r requirements.txt` and (if present) `-r requirements-dev.txt`.  
* From **frontend/** run `npm install`.  
* Copy `.env.example` → `.env`, then set environment variables.

---

## Environment Preflight
At session start **and** before tests:

1. Verify presence of `docker`, `docker-compose`, `python`, `node`, `npm`.  
2. Report missing tools in diagnostics.  
3. If checks fail, mark tests **not validated** until resolved.

---

## Baseline Snapshot Enforcement
* Before any patch, audit, or analysis run `scripts/CPG_repo_audit.py` (or equivalent) to
  capture: commit hash, UTC timestamp, dir-tree summary, config state, test inventory,
  dependency graph.
* If the script fails, fall back to recording git commit hash plus UTC timestamp; builder
  must explicitly acknowledge this degraded mode.
* Every snapshot reference must include explicit freshness metadata (capture time and
  commit hash).
* Compare freshness with the last snapshot. **Halt** if stale or missing; surface
  diagnostics until a fresh snapshot is supplied.

## Snapshot Script / State Snapshot Validation
* If `scripts/CPG_repo_audit.py` is missing, prompt the builder to create it or approve a
  stub before proceeding.
* Run the script to capture a canonical snapshot including commit hash, UTC timestamp,
  directory tree summary, config state, test inventory, and dependency graph.
* Each snapshot must be uniquely identified by its timestamp and hash; compare to the
  previous snapshot and halt on duplicates, backwards timestamps, or missing data.

## Live State Fetch Enforcement
* For any patch, revert, or audit operation, fetch the live project state before acting.
* Report source, fetch time (UTC), and session ID in diagnostics.
* If using cached/local state or metadata is omitted, **halt** and request a re-fetch.

---

## Guard Rails — Session & Patch Safety
* **ConcurrencyGuard** – Abort if another active session is using a different builder.  
* **ClarifyIntent** – If builder instructions are ambiguous, ask a follow-up; never guess.  
* **Timeout** – Abort execution exceeding **300 s** and return `diag_timeout`.  
* **MergeCheck** – Abort if files contain unresolved `<<<< HEAD` conflict markers.  
* **BinaryGuard** – If a diff > 1 MB **or** binary content is detected, pause and ask builder
  for confirmation.  
* **AtomicPatch** – When > 1 file is modified, commit all changes atomically; otherwise
  revert.  
* **InputRedaction** – Reject prompts containing un-hashed secrets or credentials.  
* **AutoRollback** – If a fallback is triggered *after* files changed, automatically revert
  to the pre-patch state and report.
* **PathCreation Guard** – If a referenced file is missing, prompt the builder to create
  or abort; upon approval, generate a minimal stub.

## XOutputValidation
* Only modify files within the defined scope and apply all constraints.
* Do not hallucinate modules, files, or structures.
* Update documentation whenever behavior changes.
* Ensure output is syntactically executable and free of TODOs or placeholders.

---

## Patch Logging
After each committed patch:

1. Generate `/docs/patch_logs/patch_<YYYYMMDD><HHMMSS>_<short>.log`.
2. Log must include: **TASK, OBJECTIVE, CONSTRAINTS, SCOPE, DIFFSUMMARY, TS,
   prompt_id (commit hash fallback), AV, AH, CH, BDT, snapshot_metadata,
   agent_metadata, test_results, full diagnostic block, SPEC_HASHES,
   decisions/deviations**.
3. Missing or incomplete patch logs **reject the patch** and block further actions.
4. Patch log creation is a final step after the commit; confirm builder-supplied date/time
   before naming and note any degraded fallback.

Use UTC when constructing patch file names to align with TIMESTAMP (Z).

---

## Testing Enumeration
For any testing or build context:

* List all available tests, entry points, and runner configurations.
* If none are found or discovery is ambiguous, provide diagnostics on how to locate or
  add tests.

## Test Enforcement
* Run `scripts/run_tests.sh` (or discovered test runners) after patches that change behavior.
* Use Environment Preflight checks first.
* If tests can’t run, document why and instruct builder to run them manually. Patch remains
  **unvalidated** until results exist.

---

## Dependency and Impact Reporting
After each patch:

* Enumerate affected files/modules.  
* Explain downstream or upstream impact and required follow-ups (diagnostics or patch log).

---

## Workflow Health Check
Triggered on builder request, after every **3 committed patches**, or **daily** if idle:

* Audit current state, patch logs, dependency map, and instruction set for drift or
  inconsistencies.
* Provide a concise health report with timestamp, commit hash, and checks performed.
* **Block workflow** if critical inconsistencies are found.

## Session Summary
On builder request or after **3 committed patches**:

* Summarize prompt IDs, files changed, decisions made, and outstanding dependencies.

---

## Irreversible Action Safeguards
Before destructive/non-idempotent operations:

1. Flag irreversible action; request explicit confirmation.  
2. Capture snapshot/backup when possible.  
3. Document risk, fallback, mitigation in diagnostics and patch logs.

---

## Agent Metadata Recording
With every patch, audit, or health check include:

* **agent version, operational signature (prompt hash), snapshot reference, session ID**  
* Record this in diagnostics and patch logs.

---

## Prompt Submission Semantics
All prompts must be submitted via **Ask** or **Code** and include builder date-time in
`YYYYMMDD HHMMSS` format.
Prompts to Codex must be wrapped in triple backticks with no nested backticks or language
tags.
Echo the prompt type (Ask / Code) back in diagnostics.

## Builder Relay
* Builder must relay the full Codex output and diagnostic block before CAG proceeds.
* If the relay is partial, missing, or corrupted, **halt** and request correction.

---

## Silent Fail Prevention
If diagnostics or required metadata are missing, **stop** and request resubmission—never act
on incomplete output.
