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
* Compare freshness with the last snapshot. **Halt** if stale or missing; surface diagnostics
  until a fresh snapshot is supplied.

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

---

## Patch Logging
After each committed patch:

1. Generate `/docs/patch_logs/patch_<YYYYMMDD><HHMMSS>_<short>.log`.
2. Log must include: **TASK, OBJECTIVE, CONSTRAINTS, SCOPE, DIFFSUMMARY, snapshot
   metadata, agent metadata, test results, full diagnostic block, SPEC_HASHES,
   decisions/deviations**.
3. Missing or incomplete patch logs **reject the patch** and block further actions.

Use UTC when constructing patch file names to align with TIMESTAMP (Z).

---

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
Periodically **or on request**:

* Audit repo state, patch logs, dependencies, and instructions for drift/compliance.  
* Provide a concise health report with timestamp, commit hash, and checks performed.

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
All prompts are submitted via **Ask** or **Code**. Echo this label in diagnostics.

---

## Silent Fail Prevention
If diagnostics or required metadata are missing, **stop** and request resubmission—never act
on incomplete output.
