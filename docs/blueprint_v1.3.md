Alias:C=CAG,X=Codex,B=Builder,A=Architect;FieldAliases:AV=AGENTVERSION,AH=AGENTHASH,CH=COMMITHASH,TS=TIMESTAMP,DIAGMETA=DIAGNOSTICMETA,BDT=BUILDER_DATE_TIME,TESTRES=TESTRESULTS,DIFF=DIFFSUMMARY;
Mode=CriticalEngineering;

# Preamble

**Blueprint-Version: v1.3**  
**Approved-By: Architect**  
**Approved-At (UTC): 2025-08-19 14:21**

This document is the **master authority** for the CAG–Codex system.  
It defines roles, rules, lifecycle, lanes, mirrors, compliance gates, and telemetry.  
All other instruction files — **CAG_Instructions, /docs/CAG_spec.md, AGENTS.md, /docs/AGENTS_mirror.md** — must explicitly reference this Blueprint and conform to it.  
If this Blueprint itself drifts out of sync with its mirrors or execution instructions, **all operations halt until the Architect restores alignment**.

**Visibility Constraints (Authoritative):**  
- **CAG** can see: `CAG_Instructions`, this **Blueprint**, `/Personalized_ChatGPT_Instructions_v1.0_densified.md`, and **`/docs/AGENTS_mirror.md`**. CAG **cannot** see `/docs/CAG_spec.md`.  
- **Codex** can see: `AGENTS.md`, `/Personalized_ChatGPT_Instructions_v1.0_densified.md`, and **`/docs/CAG_spec.md`**. Codex **cannot** see `/docs/AGENTS_mirror.md`.  
- **Architect/Builder** can see **all** files and is the **only** party who can directly verify and restore mirror alignment across the system.

# Purpose & Scope

This Blueprint defines the authoritative, project-agnostic operating model for the CAG–Codex system. It binds four parties:

* C (CAG): Orchestrates logic, validation, prompts, and guardrails.
* X (Codex): Executes changes, tests, and returns diagnostics/artifacts.
* B (Builder): Provides scope, intent, approvals, and confirmation tokens.
* A (Architect): Owns governance of this Blueprint and adjudicates exceptions.

Out of scope: product-specific business requirements and domain code; those live in project repositories and are governed by this Blueprint’s process.

# Objective

Harden the collaboration model between C (CAG) and X (Codex) using GPT-5 Thinking while preserving explicit contracts and constraints. Deliver a deterministic operating structure, evaluation criteria, and an upgrade path that preserves token efficiency and eliminates dependency on Copilot.

# Current Canon

* BuilderContract: ExplicitBuilderIntentForActions; NoCAGActionWithoutB; BRelaysXResponses; NoHiddenStateBetweenSessions; COnlySourcesViaX; BConfirmsIntentBeforeExecutionPrompt.
* Workflow: Baseline snapshot required; all edits via XPrompt; atomic patches; patch logs; tests enforced; health checks; rollback.
* Freshness & Provenance: Live state fetch for every patch; TS+Hash required; reject cached state.
* Safeguards: Concurrency guard; destructive-change confirmations; dependency awareness; binary guard.
* Logging/Trace: Patch logs under /docs/patch_logs/; AGENTS.md updates before logs; test enumeration.
* Style/Format: Strict XPrompt structure; alias consistency; no drift; diff summaries; diagnostics mandatory.

# Gaps Addressed

This version fixes ambiguity in snapshot modes, clarifies patch logging rules, integrates UTC and prompt_id fields, hardens lane thresholds, and removes blind spots in governance, concurrency, and CI enforcement.

# Roles (RACI)

* **B (Builder)**: Request owner; supplies scope, acceptance criteria, timestamp; approves irreversible changes; **No Codex execution without explicit Builder confirmation for the current prompt (per-session, per-change), recorded in the patch log.**
* **C (CAG)**: Validator; compiles prompts, enforces contracts, inserts safeguards, owns DIAGMETA; **halts on any inconsistency detected in AGENTS_mirror.md** and escalates to Architect; **cannot** verify `/docs/CAG_spec.md`.
* **X (Codex)**: Executor; fetches live state, applies patches atomically, runs tests, generates diagnostics, patch logs; **halts on any inconsistency detected in CAG_spec.md** and escalates to Architect; **cannot** verify `/docs/AGENTS_mirror.md`.
* **A (Architect)**: Custodian of this Blueprint; governs mirrors; resolves disputes; approves exceptions; **only authority to restore Blueprint drift and to verify/restore system-wide mirror alignment (the only party with visibility into all files).**

# Mirror Responsibilities

* **Awareness (per-agent visibility limits):**  
  - **CAG**: uses **`/docs/AGENTS_mirror.md`** as its **only** window into Codex; **cannot** access `/AGENTS.md` directly.  
  - **Codex**: uses **`/docs/CAG_spec.md`** as its **only** window into CAG; **cannot** access `CAG_Instructions` directly.
* **Enforcement (Architect/Builder):**  
  - **Mirror pairs must be byte-for-byte identical; Architect/Builder verifies both pairs. Any deviation = halt until restored.**  
* **System Integrity:**  
  - **All five files** must be aligned for system-wide operations: `{CAG_Instructions, /docs/CAG_spec.md, /AGENTS.md, /docs/AGENTS_mirror.md, /docs/CAG_Codex_Collaboration_Blueprint.md}`.  
  - Agents act only on what they can see; cross-pair validation is an **Architect/Builder** responsibility.

# Structural Integrity & Drift Detection

To ensure CAG, Codex, and Builder/Architect always operate on the same authoritative instruction sets, the following rules are mandatory.

## 1) SPEC_HASH Embedding (Authoritative Identity)
- Each **core file** — **Blueprint.md**, **CAG_Instructions.txt**, **AGENTS.md** — MUST embed:
  - **SPEC_HASH**: SHA-256 of the file’s exact bytes as committed (UTF-8, LF line endings; no BOM; no normalization).
  - **Blueprint-Version**: matches this Blueprint’s version string.
  - **Approved-At (UTC)**: Architect/Builder approval timestamp.
- Each **mirror file** — **/docs/CAG_spec.md** (mirror of CAG_Instructions) and **/docs/AGENTS_mirror.md** (mirror of AGENTS.md) — MUST embed the **same three fields**.
- **Format (example within each file):**
  ~~~
  SPEC_HASH: <64-hex-sha256>
  Blueprint-Version: v1.1.1
  Approved-At (UTC): <YYYY-MM-DDTHH:MM:SSZ>
  ~~~

## 2) Prompt & Response Drift Check (Per-Exchange Proof)
- All **Ask/Code** prompts and all agent responses MUST include a `SPEC_HASHES` mapping:
  ~~~
  SPEC_HASHES: { blueprint: <sha>, cag: <sha>, codex: <sha> }
  ~~~
- **Codex** MUST echo the received `SPEC_HASHES` inside its diagnostic block.
- **CAG** MUST record the `SPEC_HASHES` it observes for the exchange.
- **Builder/Architect** MUST relay both sides unaltered.
- **Hard Gate:** If any of the three hashes differ at any time, **HALT immediately** and issue an **Audit Demand** (see §4).

## 3) Byte-for-Byte Mirror Requirement (Strict)
- Mirror pairs MUST be **byte-for-byte identical**:
  - `CAG_Instructions.txt` ↔ `/docs/CAG_spec.md`
  - `AGENTS.md` ↔ `/docs/AGENTS_mirror.md`
- Any deviation constitutes **drift**. CAG/Codex report drift; only Architect/Builder can restore.

## 4) Audit Demand (Recovery Protocol)

Trigger: any SPEC_HASH mismatch or mirror inequality.

Effect: all operations HALT until Architect/Builder:

Runs a mirror audit for all core + mirror files.

Selects the canonical source-of-truth.

Regenerates mirrors from the canonical source.

Recomputes and republishes SPEC_HASH values.

Reissues a green state confirmation (session gate reopen).

CAG and Codex must not self-heal drift.

Logging Requirement: Architect/Builder must produce a mirror_recovery_<UTC>.md file in /docs/audit/ documenting:

source-of-truth selection,

regeneration steps taken, and

the new SPEC_HASH values.

Partial Corruption: If metadata fields match but file content differs, this is treated as drift and escalated as above.


## 5) Logging Enforcement (Immutable Evidence)
- Every patch log MUST record the SPEC hashes observed at commit time:
  ~~~
  SPEC_HASHES: { blueprint: <sha>, cag: <sha>, codex: <sha> }
  ~~~
- Logs **REJECTED** if any hash is missing or blank.
- Deterministic ordering applies: **Update `AGENTS.md` (or its CAG-side mirror) BEFORE writing the patch log**; abort if ordering fails.

## 6) CI Enforcement (Pre-Session & Per-PR)
- CI MUST recompute SHA-256 for:
  - `Blueprint.md`, `CAG_Instructions.txt`, `/docs/CAG_spec.md`
  - `AGENTS.md`, `/docs/AGENTS_mirror.md`
- CI **FAILS** if:
  - Any mirror pair is not byte-for-byte identical, or
  - Any embedded **Blueprint-Version** or **Approved-At (UTC)** field differs across the five files.
- CI publishes the current `SPEC_HASHES` bundle as a build artifact.

## 7) Telemetry & Health Checks (Continuous Assurance)
- Append the current `SPEC_HASHES` to telemetry and session health reports.
- The periodic **Workflow Health Check** MUST verify:
  - Mirror byte-equality,
  - Hash equality across all five files,
  - Latest Architect/Builder approval timestamp consistency.
- Any failure escalates to **Audit Demand** and closes session gates.

## 8) Session Gates (Open/Close Criteria)
- **Open** only when:
  - All five files pass CI mirror checks,
  - `SPEC_HASHES` are equal across CAG, Codex, and Blueprint,
  - Latest **Approved-At (UTC)** matches across all embedded fields.
- **Close** (HALT) on any drift signal from §2–§7.

> Rationale: These controls create cryptographic provenance for instructions, force per-exchange baseline proof, and make drift both immediately visible and non-actionable until Architect/Builder restores a green state.

# Repository Bootstrap & Mandatory Artifacts

To ensure CAG, Codex, and Builder/Architect operate against a consistent and verifiable repository baseline, the following rules are mandatory.

## 1) Codex-Only File Authority
- Only **Codex** may create or modify files inside the repository.  
- **CAG** may request documentation updates or generation, but it cannot directly create/edit repository files.  
- **Builder/Architect** approves when new mandatory documents must be introduced.

## 2) Mandatory File Set
The following files must exist in the repository root (or specified path) for any session to proceed:

- **`README.md`** – repository overview and entry point.  
  - If a file named `index.md` exists instead of `README.md`, this is treated as **non-compliant** and triggers an **Audit Demand**. Codex must rename or regenerate the file as `README.md`.  
- **`design_scope.md`** – project design and scope definition.  
- **`future_updates.md`** – backlog of planned or deferred changes.  
- **`CHANGELOG.md`** – sequential history of applied patches.  
- **`SECURITY.md`** – security practices, restrictions, and handling rules.  
- **`testing_strategy.md`** – test execution plan and CI enforcement rules.  
- **`/docs/CAG_spec.md`** – mirror of CAG instructions (Codex-visible).  
- **`/docs/AGENTS_mirror.md`** – mirror of AGENTS.md (CAG-visible).  
- **`/docs/CAG_Codex_Collaboration_Blueprint.md`** – authoritative copy of this Blueprint.

**Hard Gate:** If any of these files are missing, outdated, or misplaced, the session halts and triggers an **Audit Demand**.  
All references to file naming, hashes, and datetime values across this Blueprint must use explicit formats (e.g., `YYYYMMDD_HHMMSS` for timestamps, 64-hex for SHA256) rather than placeholders.

## 3) Audit Artifacts

Codex must generate audit files in the format:handoff_repo_state_YYYYMMDD_HHMMSS.md

These files MUST be stored exclusively in /docs/audit/. No other path is valid.

The UTC datetime in the filename MUST follow the strict YYYYMMDD_HHMMSS format to ensure reproducibility and prevent replay.

Each handoff file captures the repository state as Codex sees it and becomes the canonical baseline for CAG.

CAG and Builder/Architect rely on this handoff for project awareness; Codex is the only authority for repository inspection.

Completeness Rules: Each handoff file must include:

commit_hash,

repo_tree_hash,

SPEC_HASHES,

UTC timestamp,

Builder confirmation reference (if used).

Files missing any required field are invalid and trigger HALT.  Retention: all audit artifacts must be preserved ≥1 year, rotated monthly, and archived under /docs/audit/archive/.

## 4) Enforcement of Document Presence
- During INIT → READY transition, Codex must verify presence and integrity of the Mandatory File Set.  
- If any file is missing:
  - **HALT** the session.  
  - CAG must escalate to Builder/Architect.  
  - Builder/Architect decides whether Codex should generate the missing document(s).

## 5) Audit Path Start Condition
- **Audit-Path cannot begin** until:
  - Codex produces a valid `handoff_repo_state_YYYYMMDD_HHMMSS.md` in `/docs/audit/`,  
  - The Mandatory File Set is present and validated, and  
  - Mirrors are byte-for-byte aligned.  
- If these preconditions fail, operations halt and escalate to **Architect/Builder** for resolution.

> Rationale: These controls prevent blind starts, ensure project documentation exists in predictable locations, and enforce that Codex is the only authority to write repository artifacts while CAG and Builder/Architect enforce presence and alignment.

# Builder Responsibilities

Relay complete outputs/diagnostics between CAG and Codex without omission or corruption.

Provide explicit confirmation tokens for irreversible/high-risk actions.

Supply session timestamps in UTC.

Approve restoration sources when mirrors drift.

No Codex execution without explicit Builder confirmation for the current prompt (per-session, per-change), recorded in the patch log.

Builder confirmation tokens must follow strict rules:

Format: CONFIRM_<UUID>_<UTC>

Validity: maximum 24h from issuance.

Non-reusable: once logged in a patch, the token cannot be reused.

Replay detected → HALT and escalate to Architect.


# Two Lanes

Fast-Path (small, local, reversible)

Trigger: ≤150 LOC net change (adds+deletes), single production file plus ≤1 related test file, non-binary, no schema/API/security/external deps, no renames/deletes.

Snapshot: meta-only audit allowed (scripts/CPG_repo_audit.py --mode=meta) capturing commit_hash, capture_time_utc, repo_tree_hash, path_scoped_tree_hash, test_runner_presence.

Patch Log: required after commit; filename schema = patch_<YYYYMMDD><HHMMSS>_<short>.log (UTC).

Exception: Even if under LOC/file thresholds, any change that modifies API contracts, schemas, or security logic MUST escalate to Audit-Path.

## Audit-Path (multi-file, infra, risky)

* Trigger: multi-file, LOC >150, migrations, API changes, security code, external deps (network, package installs, toolchain), binary/large files, deletes/renames.  
* Requires design brief, rollback plan, dependency map, test plan, and explicit Builder confirmation token.  
* Snapshot: full audit script (`scripts/CPG_repo_audit.py`) required.

### Format-only multi-file changes

Treated as Audit-Path (light). Requirements:

Mirrors, snapshot gates, and patch logging still enforced.

Rollback and dependency map optional.

All other Audit-Path rules apply.

# Process Lifecycle

INIT → READY → PATCHING → VERIFYING → LOGGING → COMPLETE → (optional) POSTMORTEM → (if unrecoverable) ABORT

INIT → READY: mirrors green, lane chosen, scope set.

READY → PATCHING: prompt accepted, scope locked.

PATCHING → VERIFYING: patch applied atomically, tests executed or scaffolded.

VERIFYING → LOGGING: results recorded, DIAGMETA generated, patch log created.

LOGGING → COMPLETE: compliance gates satisfied.

Any state → INIT: on drift, concurrency violation, or hard gate failure.

ABORT: terminal failure state when recovery not possible in current session (e.g., missing mandatory files). Requires Architect/Builder restart.

POSTMORTEM: optional stage after COMPLETE or ABORT; produces postmortem_<UTC>.md in /docs/audit/, recording cause, resolution, and prevention notes.

# Compliance Gates

**Hard Gates (halt if failed):**

* **CAG session gate:** **`/docs/AGENTS_mirror.md` must be green** (no inconsistency observed by CAG in its only visible mirror).  
* **Codex session gate:** **`/docs/CAG_spec.md` must be green** (no inconsistency observed by Codex in its only visible mirror).  
* **Architect system gate:** **All five files green** (Architect-validated alignment across `{CAG_Instructions, /docs/CAG_spec.md, /AGENTS.md, /docs/AGENTS_mirror.md, Blueprint}`).  
* LiveSnapshot: meta-only allowed for Fast-Path, full for Audit-Path.  
* Atomic patch enforcement (multi-file).  
* Diagnostics block present and complete (9-key schema).  
* Patch log created with all required fields.  
* Tests run or minimal runner scaffolded.  
* ConcurrencyGuard enforced.

**Guidelines (warn only):**

* Diff compression in chat (context=2).  
* Token budget reporting.  
* Coverage delta tracking.  
* Dependency impact notes.

# State & Freshness

* Always request LiveSnapshot first.  
* Fast-Path may skip full baseline only if path_scoped_tree_hash matches last patch; else escalate.  
* If audit script missing: prompt Builder to create or approve stub.  
* Snapshots must include unique commit_hash+UTC; duplicates/backwards/hashes rejected.

# Exception & Escalation

Mirror drift detected by CAG (via AGENTS_mirror.md) → halt; escalate to Architect.

Mirror drift detected by Codex (via CAG_spec.md) → halt; escalate to Architect.

Architect/Builder determines source-of-truth and restores alignment; agents resume only after Architect confirmation (green state).

Missing test runner: Fast-Path may scaffold minimal runner once; otherwise escalate.

Tooling gaps: patch flagged "unvalidated"; Architect decides proceed/pause.

Ambiguities: CAG must ask Builder; no guessing.

Tie-breaker: Architect decision logged.

If Architect is unavailable >24h, Builder may act as temporary custodian for urgent fixes only (security patches, repo unlocks).

Builder actions must be logged in architect_delegation_<UTC>.md in /docs/audit/.

Architect must review and ratify retroactively.

# Security & Data Handling

Secrets/credentials must be hashed/redacted.

No PII beyond necessity.

Patch logs immutable ≥1 year unless Architect approves archival.

External calls = network egress (HTTP, SSH), package registry, toolchain execs. Only allowed in Audit-Path if SCOPE explicitly permits.

Builder is prohibited from embedding secrets or credentials in prompts.

Mirrors must not contain sensitive data; CI scans mirrors for forbidden patterns (e.g., AWS_SECRET, PRIVATE_KEY). Detection = HALT.

# Prompt Structure

Prompts must be in triple backticks, no nested blocks or language tags.  
Codex must echo Ask/Code in diagnostics.

Fields:  
**TASK, OBJECTIVE, CONSTRAINTS, SCOPE, OUTPUTFORMAT, TIMESTAMP (UTC), prompt_id**

# Interface Contracts

* Codex output must include: patches, tests, DIAGMETA (9-key block), DIFFSUMMARY.  
* DIAGMETA schema = {attempted_action_summary, instruction_interpretation, successes, failures, skipped_steps, missing_inputs, ambiguities_detected, resource_or_environment_gaps, suggestions_to_builder}.  
* All logs and diagnostics must include agent version, signature (prompt hash), snapshot reference, session ID.

# Patch Logging

* File naming: `patch_<YYYYMMDD><HHMMSS>_<short>.log (UTC)`.  
* Must include: TASK, OBJECTIVE, CONSTRAINTS, SCOPE, DIFFSUMMARY, TS, prompt_id, AV, AH, CH, BDT, snapshot_metadata, agent_metadata, test_results, DIAGMETA (9-key), SPEC_HASHES, decisions/deviations.  
* Patch log is created immediately after commit (final step). Reject patch if missing/incomplete.  
* **Update AGENTS.md (or its CAG-side mirror) before writing the patch log; abort if ordering fails.**

# Decision Tree

* Change reversible & local? → Fast-Path.  
* Missing tests? → Fast-Path adds minimal; Audit-Path for framework-level.  
* Binary/large/multi-file/migration? → Audit-Path.  
* File rename/delete? → Audit-Path.  
* Concurrency detected? → Halt.

# Token Economy Controls

* Meta-only baseline for Fast-Path.  
* Auto patch-log creation mandatory.  
* Diff compression (context=2) for chat.  
* Report token budget on every patch.  
* If no runner, scaffold minimal runner and record rationale.

Evaluation Checklist (score 0–2; target ≥14/18)

LiveSnapshot metadata present/fresh.

SCOPE respected.

Atomic commit applied.

Patch log created with DIAGMETA.

Tests run or runner scaffolded.

Rollback instructions present (Audit-Path).

ConcurrencyGuard enforced.

BinaryGuard enforced.

Dependency map or none confirmed.

No secrets in prompts.

Acceptance criteria met.

Token budget reported.

Diff summary present/readable.

Related file impacts evaluated.

Health check status updated.

Version & commit hash recorded.

Builder approval token captured for risky changes.

No hidden state between sessions.

If the evaluation score <14, the patch is REJECTED unless Architect explicitly overrides in writing.

Critical items: failure of any of the following = automatic HALT regardless of total score:

6 (Rollback instructions),

7 (ConcurrencyGuard),

8 (BinaryGuard),

17 (Builder confirmation token).

# Spec-First Template

~~~~
TASK: Implement <feature/bugfix> in <file(s)> via Fast-Path.
OBJECTIVE: <Given/When/Then> + expectations.
CONSTRAINTS: Single-file; context=2; auto patch-log; add/adjust minimal tests; no external calls.
SCOPE: {edit: <path>, create_if_missing: <true/false>}
OUTPUTFORMAT: {patches, tests, DIAGMETA, DIFFSUMMARY}
TIMESTAMP: <UTC YYYYMMDD HHMMSS>
prompt_id: <UUID or commit hash>
~~~~

# Example Flows

**Fast-Path Example**  
* B: “Add null-check in utils/parse.ts; date strings can be null.”  
* C: Compiles Spec-First → X.  
* X: Applies patch, logs `patch_<UTC>.log`, runs tests or scaffolds minimal.  

**Audit-Path Example**  
* B: “Refactor auth to JWT, remove sessions.”  
* C: Produces design, risk matrix, rollback, test plan; requests Builder token.  
* X: Stages patch, runs tests; awaits B “apply.”

# Telemetry

Schema:

~~~~
{
  "ts": "<UTC ISO8601>",
  "session_id": "<id>",
  "lane": "fast|audit",
  "mirrors_green": true|false,
  "lead_time_s": <int>,
  "token_spend": {"prompt": <int>, "completion": <int>},
  "tests": {"ran": true|false, "passed": true|false, "runner_scaffolded": true|false},
  "coverage_delta": "<+/-X.Y%|unknown>",
  "revert": false,
  "notes": "<brief>"
}
~~~~

Telemetry logs are appended to `/docs/telemetry/patch_telemetry.jsonl` (UTC), rotated weekly, retained ≥1 year.

# Change Management

Any Blueprint change requires Architect approval and mirror regeneration.

Mirrors must be in sync before session start.

If Blueprint/mirrors corrupted, Architect designates canonical source.

Resume only after full alignment is green.

Precedence with Unified Operating Contract (UOC):

This Blueprint governs multi-agent/system workflows.

UOC v1.0 governs conversational behavior.

If conflicts arise: Blueprint overrides for repository/system governance; UOC overrides for conversational flow.

Architect adjudicates any overlap.

# CI Integration

Run on every PR and session init (Architect-controlled checks):

Mirror checks for both mirror pairs (Architect-visible): CAG_Instructions ↔ /docs/CAG_spec.md, /AGENTS.md ↔ /docs/AGENTS_mirror.md.

Lane eligibility check (thresholds).

Patch log presence & schema validation.

Telemetry append check.

CI scripts: scripts/cag_check_mirrors.sh, scripts/cag_lane_check.sh, scripts/cag_patchlog_check.py; non-zero exit on failure.

CI enforcement scripts themselves must embed SPEC_HASH headers. Drift in these scripts = HALT.

If telemetry append fails, patch may not merge. Telemetry entry must exist before merge.

# Risks & Mitigations

* Skipping full baseline → stale scope. Mitigation: require tree hashes.  
* Test scaffolds bloat → tag/consolidate later.  
* Human bottleneck (Builder) → cache tokens ≤24h.  
* Mirror drift → halt until restored (Architect-only enforcement).

# Spec DR & Continuity

* If Blueprint/mirrors missing, Architect chooses canonical copy (latest signed commit).  
* Regenerate all instructions/mirrors from canonical.  
* Resume only after mirrors green.

# Operational Requirements & Locations

* Place `/docs/CAG_Codex_Collaboration_Blueprint.md` in repo.  
* Place `/docs/CAG_spec.md` and `/docs/AGENTS_mirror.md` as mirrors.  
* **Attach to CAG:** Blueprint, `/docs/AGENTS_mirror.md`, `/Personalized_ChatGPT_Instructions_v1.0_densified.md`.  
* **Attach to Codex:** Blueprint, `/docs/CAG_spec.md`, `/Personalized_ChatGPT_Instructions_v1.0_densified.md`.  
* Ensure mirrors green before any session (**Architect validates all five files**).  
* Validate Fast-Path & Audit-Path separately.  
* Track KPIs and telemetry.

# What You Gain

* Deterministic, test-backed patches.  
* Design-first guardrails.  
* Transparent logs and KPIs.  
* Full traceability without Copilot.

# Ready-to-Use Prompt Stubs

**Fast-Path Stub**

~~~~
TASK: <short>
OBJECTIVE: <criteria>
CONSTRAINTS: Fast-Path; single-file; atomic; context=2; auto patch-log; no secrets; token_budget=<N>.
SCOPE: {edit: <path>, create_if_missing: false}
OUTPUTFORMAT: {patches, tests(minimal_ok), DIAGMETA, DIFFSUMMARY}
TIMESTAMP: <UTC YYYYMMDD HHMMSS>
prompt_id: <UUID or commit hash>
~~~~

**Audit-Path Stub**

~~~~
TASK: <short>
OBJECTIVE: <criteria>
CONSTRAINTS: Audit-Path; multi-file allowed; require Builder confirmation token; rollback required; enumerate dependencies; full tests.
SCOPE: {paths: [..], create_missing: ask}
OUTPUTFORMAT: {design_brief, risk_matrix, staged_patches, test_plan, DIAGMETA, DIFFSUMMARY}
TIMESTAMP: <UTC YYYYMMDD HHMMSS>
prompt_id: <UUID or commit hash>
~~~~
