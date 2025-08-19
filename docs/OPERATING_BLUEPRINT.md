Alias:C=CAG,X=Codex,B=Builder,A=Architect;FieldAliases:AV=AGENTVERSION,AH=AGENTHASH,CH=COMMITHASH,TS=TIMESTAMP,DIAGMETA=DIAGNOSTICMETA,BDT=BUILDER_DATE_TIME,TESTRES=TESTRESULTS,DIFF=DIFFSUMMARY;
Mode=CriticalEngineering;

# Preamble

Bundle-ID: 1
Bundle-UTC: 20250819
Blueprint-Version: 2
Source-of-Truth: OPERATING_BLUEPRINT.md
Approved-By: Architect

This document is the **master authority** for the CAG–Codex system.
It defines roles, rules, lifecycle, lanes, mirrors, compliance gates, and telemetry.  
All other instruction files — **CAG_Instructions, /docs/CAG_spec.md, AGENTS.md, /docs/AGENTS_mirror.md** — must explicitly reference this Blueprint and conform to it.  
If this Blueprint itself drifts out of sync with its mirrors or execution instructions, **all operations halt until the Architect restores alignment**.

## File Identity
- Canonical filename is `/docs/OPERATING_BLUEPRINT.md`. Bundle-ID and Bundle-UTC govern identity; filename is stable but non-cryptographic.
> Rationale: clarifies authoritative path while tying trust to a shared bundle header, not mutable names.

**Visibility Constraints (Authoritative):**
- **CAG** can see: `CAG_Instructions`, this **Blueprint**, and **`/docs/AGENTS_mirror.md`**. CAG **cannot** see `/docs/CAG_spec.md`.
- **Codex** can see: `AGENTS.md` and **`/docs/CAG_spec.md`**. Codex **cannot** see `/docs/AGENTS_mirror.md`.
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

## Rationale Requirement
Every major rule or gate MUST include a `> Rationale:` line explaining its intent.
> Rationale: ensures governance decisions remain transparent and auditable.

# Current Canon

* BuilderContract: ExplicitBuilderIntentForActions; NoCAGActionWithoutB; BRelaysXResponses; NoHiddenStateBetweenSessions; COnlySourcesViaX; BConfirmsIntentBeforeExecutionPrompt.
* Workflow: Baseline snapshot required; all edits via XPrompt; atomic patches; patch logs; tests enforced; health checks; rollback.
* Freshness & Provenance: Live state fetch for every patch; commit hash and timestamp required; reject cached state.
* Safeguards: Concurrency guard; destructive-change confirmations; dependency awareness; binary guard.
* Logging/Trace: Patch logs under /docs/patch_logs/; update AGENTS metadata before logs only when it changes; test enumeration.
* Style/Format: Strict XPrompt structure; alias consistency; no drift; diff summaries; diagnostics mandatory.

# Gaps Addressed

This version fixes ambiguity in snapshot modes, clarifies patch logging rules, integrates UTC and prompt_id fields, hardens lane thresholds, and removes blind spots in governance, concurrency, and CI enforcement.

# Roles (RACI)

* **B (Builder)**: Request owner; supplies scope, acceptance criteria, timestamp; approves irreversible changes; **No Codex execution without explicit Builder confirmation for the current prompt (per-session, per-change), recorded in the patch log.**
* **C (CAG)**: Validator; compiles prompts, enforces contracts, inserts safeguards, owns DIAGMETA; **halts on any inconsistency detected in AGENTS_mirror.md** and escalates to Architect; **cannot** verify `/docs/CAG_spec.md`.
* **X (Codex)**: Executor; fetches live state, applies patches atomically, runs tests, generates diagnostics, patch logs; **halts on any inconsistency detected in CAG_spec.md** and escalates to Architect; **cannot** verify `/docs/AGENTS_mirror.md`.
* **A (Architect)**: Custodian of this Blueprint; governs mirrors; resolves disputes; approves exceptions; **only authority to restore Blueprint drift and to verify/restore system-wide mirror alignment (the only party with visibility into all files).**

## Role Usage Boundaries
Builder = daily operational driver (scope, acceptance criteria, timestamps, confirmation tokens, relaying diagnostics). Architect = governance custodian (mirror restoration, disputes/exceptions, Blueprint drift, cross-mirror verification).

| Trigger | Invoke |
| --- | --- |
| Schema change | Architect |
| Mirror drift or exception dispute | Architect |
| Single-file non-schema fix | Builder |
| Routine diagnostics relay | Builder |

> Rationale: clarifies escalation thresholds and prevents role drift.

## Ask vs Code Decisioning (CAG rule)
CAG must always indicate whether the Builder should use Ask or Code. When CAG provides a Codex-ready prompt, Builder need only press Code—no additional decisioning required.
> Rationale: removes ambiguity in execution mode and preserves auditability.

# Mirror Responsibilities

* **Awareness (per-agent visibility limits):**
  - **CAG**: uses **`/docs/AGENTS_mirror.md`** as its **only** window into Codex; **cannot** access `/AGENTS.md` directly.
  - **Codex**: uses **`/docs/CAG_spec.md`** as its **only** window into CAG; **cannot** access `CAG_Instructions` directly.
* **Enforcement (Architect/Builder):**
  - Mirror pairs must be byte-for-byte identical; Architect/Builder verifies both pairs. Any deviation = halt until restored.
* **Green State (Model G2):**
  - Green iff both mirror pairs are byte-for-byte identical **and** `CAG_Instructions`, `/docs/CAG_spec.md`, `AGENTS.md`, `/docs/AGENTS_mirror.md`, and this Blueprint share identical `Bundle-ID` and `Bundle-UTC` header values.
  > Rationale: G2 unifies alignment on minimal, monotonic metadata.
* **System Integrity:**
  - Agents act only on what they can see; cross-pair validation is an **Architect/Builder** responsibility.

# Bundle Header & Drift Detection

To ensure CAG, Codex, and Builder/Architect operate on the same authoritative instruction sets, the following rules apply.

## Bundle Header Embedding (Authoritative Identity)
- Each core file — **OPERATING_BLUEPRINT.md**, **CAG_Instructions.txt**, **AGENTS.md** — and their mirrors `/docs/CAG_spec.md` and `/docs/AGENTS_mirror.md` MUST embed:
  - `Bundle-ID`
  - `Bundle-UTC`
  - `Blueprint-Version: 2`
> Rationale: single bundle header replaces per-file hash equality.

## Audit Demand (Recovery Protocol)
- Trigger: mirror inequality or mismatched `Bundle-ID`/`Bundle-UTC` values.
- Effect: all operations HALT until Architect/Builder select a canonical source, regenerate mirrors, reset bundle headers, and reissue a green state.
> Rationale: drift resolution remains an Architect/Builder task.

## Logging Enforcement (Immutable Evidence)
- Every patch log MUST record `Bundle-ID`, `Bundle-UTC`, and `Blueprint-Version` observed at commit time.
> Rationale: bundle metadata links logs to governed state.

## Telemetry & Health Checks (Continuous Assurance)
- Append current `Bundle-ID` and `Bundle-UTC` to telemetry and session health reports.
- The periodic **Workflow Health Check** verifies mirror byte-equality and bundle header consistency.
> Rationale: continuous verification without hash overhead.

## Session Gates (Open/Close Criteria)
- **Open** only when both mirror pairs are byte-identical and all governed artifacts share identical `Bundle-ID` and `Bundle-UTC` values (Model G2).
- **Close** (HALT) on any mirror inequality or bundle mismatch.
- Sessions do not expire; each new session with CAG requires the INIT → READY handshake; no timeout policy.
> Rationale: ties session availability to bundle coherence while preserving continuity.

# Repository Bootstrap & Mandatory Artifacts

To ensure CAG, Codex, and Builder/Architect operate against a consistent and verifiable repository baseline, the following rules are mandatory.

## 1) Codex-Only File Authority
- Only **Codex** may create or modify files inside the repository.  
- **CAG** may request documentation updates or generation, but it cannot directly create/edit repository files.  
- **Builder/Architect** approves when new mandatory documents must be introduced.

## 2) Mandatory File Set
The following files must exist in the repository root (or specified path) for any session to proceed:

- **`README.md`** – repository overview and entry point.
  - If a file named `index.md` exists instead of `README.md`, Codex may auto-create a minimal `README.md` on first session under **Grace Mode**; thereafter, rename or regenerate as needed.
- **`design_scope.md`** – project design and scope definition.
- **`future_updates.md`** – backlog of planned or deferred changes.
- **`CHANGELOG.md`** – sequential history of applied patches.
- **`SECURITY.md`** – security practices, restrictions, and handling rules.
- **`testing_strategy.md`** – test execution plan and CI enforcement rules.
- **`/docs/CAG_spec.md`** – mirror of CAG instructions (Codex-visible).
- **`/docs/AGENTS_mirror.md`** – mirror of AGENTS.md (CAG-visible).
- **`/docs/OPERATING_BLUEPRINT.md`** – authoritative copy of this Blueprint.

**Grace Mode (default):** On the first session, missing mandatory documents trigger a warning and Codex may auto-create minimal stubs. After the first successful patch, absence of any mandatory file becomes a hard gate and triggers an **Audit Demand**.

All references to file naming and timestamps across this Blueprint must use explicit formats (e.g., `YYYYMMDD_HHMMSS`) rather than placeholders.
> Rationale: Grace Mode smooths onboarding yet enforces compliance once work begins.

## 3) Audit Artifacts

Codex must generate audit files in the format:handoff_repo_state_YYYYMMDD_HHMMSS.md

These files MUST be stored exclusively in /docs/audit/. No other path is valid.

The UTC datetime in the filename MUST follow the strict YYYYMMDD_HHMMSS format to ensure reproducibility and prevent replay.

Each handoff file captures the repository state as Codex sees it and becomes the canonical baseline for CAG.

CAG and Builder/Architect rely on this handoff for project awareness; Codex is the only authority for repository inspection.

Completeness Rules: Each handoff file must include:

commit_hash,

repo_tree_hash,

bundle_id,

bundle_utc,

UTC timestamp,

Builder confirmation reference (if used).

Files missing any required field are invalid and trigger HALT. Retention: all audit artifacts are preserved indefinitely; they may be rotated into archive subfolders for manageability but are never deleted.

```yaml
loc_delta: {added: <int>, deleted: <int>}
files_changed: {code: <int>, tests: <int>, docs: <int>, other: <int>}
drift_detected: <bool>
recovery_steps: [<string>]
```
These embeds are mandatory for each audit artifact to support longitudinal, machine-readable analysis.
> Rationale: permanent, structured audit records enable reliable recovery and historical review.

## 4) Enforcement of Document Presence
- During INIT → READY transition, Codex verifies presence of the Mandatory File Set.
- Under Grace Mode, missing files generate a warning and may be auto-created.
- After the first successful patch, any missing file triggers **HALT** and Architect/Builder escalation.
> Rationale: gradual enforcement reduces setup friction.

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

Trigger: net LOC ≤150, changed_files ≤2 (one production file + ≤1 related test file), no renames/deletes, no binary files, no API/schema/security flags, no network egress.
> Rationale: explicit inputs prevent misclassification of lane.

Snapshot: meta-only audit allowed (scripts/CPG_repo_audit.py --mode=meta) capturing commit_hash, capture_time_utc, repo_tree_hash, path_scoped_tree_hash, test_runner_presence.

Patch Log: required after commit; filename schema = patch_<YYYYMMDD_HHMMSS>_<short>.log (UTC).
> Rationale: underscore timestamps ensure stable filenames.

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

* **CAG session gate:** `/docs/AGENTS_mirror.md` must be green under Model G2 from CAG's perspective.
* **Codex session gate:** `/docs/CAG_spec.md` must be green under Model G2 from Codex's perspective.
* **Architect system gate:** mirror pairs byte-identical and all governed artifacts share `Bundle-ID` and `Bundle-UTC`.
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

External calls = network egress only (HTTP/SSH/package registry/etc.). Local toolchain executables and test runners are allowed on Fast-Path. Network egress requires explicit SCOPE permission.
> Rationale: narrows the boundary to network activity while enabling local tooling.

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

* File naming: `patch_<YYYYMMDD_HHMMSS>_<short>.log` (UTC).
> Rationale: underscore timestamps ensure stable filenames.
* Must include: TASK, OBJECTIVE, CONSTRAINTS, SCOPE, DIFFSUMMARY, TS, prompt_id, AV, AH, CH, BDT, snapshot_metadata, agent_metadata, test_results, DIAGMETA (9-key), Bundle-ID, Bundle-UTC, Blueprint-Version, decisions/deviations.
* Patch log is created immediately after commit (final step). Reject patch if missing/incomplete.
* If AGENTS metadata changes, update `AGENTS.md` (or its CAG-side mirror) before writing the patch log; otherwise ordering is flexible.
> Rationale: avoids unnecessary rejections when AGENTS metadata is unchanged.
* Retention: Patch logs are preserved indefinitely as historical accounting of the project.
> Rationale: ensures a complete, enduring audit trail.
* Each patch log MUST embed the following structured metadata block:
```json
{
  "loc_delta": {"added": <int>, "deleted": <int>},
  "files_changed": {"code": <int>, "tests": <int>, "docs": <int>, "other": <int>},
  "coverage_delta": "<+/-X.Y%|unknown>",
  "risk_level": "low|medium|high",
  "lane": "fast|audit",
  "drift_detected": true|false,
  "halt_events": <int>,
  "decision_path": ["ask|code", ...]
}
```
* These embeds are mandatory for each patch log to support longitudinal, machine-readable analysis.
> Rationale: structured data enables automated historical analysis and risk tracking.

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

- [CHK-LIVESNAPSHOT] LiveSnapshot metadata present/fresh.
- [CHK-SCOPE] SCOPE respected.
- [CHK-ATOMIC] Atomic commit applied.
- [CHK-PATCHLOG] Patch log created with DIAGMETA.
- [CHK-TESTS] Tests run or runner scaffolded.
- [CHK-ROLLBACK] Rollback instructions present (Audit-Path).
- [CHK-CONCURRENCY] ConcurrencyGuard enforced.
- [CHK-BINARY] BinaryGuard enforced.
- [CHK-DEPMAP] Dependency map or none confirmed.
- [CHK-SECRETS] No secrets in prompts.
- [CHK-ACCEPT] Acceptance criteria met.
- [CHK-TOKEN] Token budget reported.
- [CHK-DIFF] Diff summary present/readable.
- [CHK-IMPACTS] Related file impacts evaluated.
- [CHK-HEALTH] Health check status updated.
- [CHK-VERSION] Version & commit hash recorded.
- [CHK-BUILDER-TOKEN] Builder approval token captured for risky changes.
- [CHK-NOHIDDEN] No hidden state between sessions.

If the evaluation score <14, the patch is REJECTED unless Architect explicitly overrides in writing.

Critical items: failure of any of the following = automatic HALT regardless of total score:

- CHK-ROLLBACK
- CHK-CONCURRENCY
- CHK-BINARY
- CHK-BUILDER-TOKEN
> Rationale: stable IDs decouple enforcement from list ordering.

# Spec-First Template

~~~~
TASK: Implement <feature/bugfix> in <file(s)> via Fast-Path.
OBJECTIVE: <Given/When/Then> + expectations.
CONSTRAINTS: Single-file; context=2; auto patch-log; add/adjust minimal tests; no network egress.
SCOPE: {edit: <path>, create_if_missing: <true/false>}
OUTPUTFORMAT: {patches, tests, DIAGMETA, DIFFSUMMARY}
TIMESTAMP: <UTC YYYYMMDD_HHMMSS>
prompt_id: <UUID or commit hash>
~~~~

# Example Flows

**Fast-Path Example**  
* B: “Add null-check in utils/parse.ts; date strings can be null.”  
* C: Compiles Spec-First → X.  
* X: Applies patch, logs `patch_<YYYYMMDD_HHMMSS>.log`, runs tests or scaffolds minimal.

**Audit-Path Example**  
* B: “Refactor auth to JWT, remove sessions.”  
* C: Produces design, risk matrix, rollback, test plan; requests Builder token.  
* X: Stages patch, runs tests; awaits B “apply.”

# Telemetry

Schema:

~~~~
{
  "ts": "<UTC YYYYMMDD_HHMMSS>",
  "bundle_id": <int>,
  "bundle_utc": "<YYYYMMDD>",
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

Mirror checks for both mirror pairs (Architect-visible): `CAG_Instructions` ↔ `/docs/CAG_spec.md`, `AGENTS.md` ↔ `/docs/AGENTS_mirror.md`.

Verify identical `Bundle-ID` and `Bundle-UTC` across governed artifacts.

Lane eligibility check (thresholds).

Patch log presence & schema validation.

Telemetry append check.

CI scripts: `scripts/cag_check_mirrors.sh`, `scripts/cag_lane_check.sh`, `scripts/cag_patchlog_check.py`; non-zero exit on failure.

If telemetry append fails, patch may not merge. Telemetry entry must exist before merge.

CI publishes a minimal artifact noting `Bundle-ID`, `Bundle-UTC`, and `Blueprint-Version`.
> Rationale: ensures mirrors and bundle headers are consistent without hash overhead.

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

* Place `/docs/OPERATING_BLUEPRINT.md` in repo.
* Place `/docs/CAG_spec.md` and `/docs/AGENTS_mirror.md` as mirrors.
* **Attach to CAG:** Blueprint and `/docs/AGENTS_mirror.md`.
* **Attach to Codex:** Blueprint and `/docs/CAG_spec.md`.
* Ensure mirrors green before any session (**Architect validates all five files**).
* Validate Fast-Path & Audit-Path separately.
* Track KPIs and telemetry.

# Hierarchy & Propagation

* `OPERATING_BLUEPRINT.md` is the sole origin for procedural changes.
* Any changes to CAG instructions or `AGENTS.md` must originate from a Blueprint change.
* After such changes, the Architect directs subsequent patches to propagate the updated bundle header and content to mirrors and masters.
> Rationale: centralizes governance and prevents uncoordinated instruction drift.

## Role Instruction Generation & Propagation (Blueprint as Sole Origin)

**Bundle Header (shared across governed artifacts)**
Bundle-ID: <INT> # Monotonic; increments when this Blueprint changes
Bundle-UTC: <YYYYMMDD> # UTC date only
Blueprint-Version: 2
Source-of-Truth: OPERATING_BLUEPRINT.md

> Rationale: A single monotonic Bundle-ID and UTC date keep all governed artifacts in lockstep without hashes.

**Generated Artifacts**
- `/docs/CAG_instructions_master.md` — human-readable draft of CAG’s Instructions.
- `/AGENTS.md` — human-readable Codex-side instructions.
- Both include the Bundle header from this Blueprint.

**How “green” is determined (Model G2)**
- Mirrors byte-equal within each pair.
- All governed artifacts share identical Bundle-ID and Bundle-UTC.

**Propagation workflow**
1) Architect requests generation → Codex runs `scripts/generate_role_instructions.py`.
2) Architect densifies `/docs/CAG_instructions_master.md` into an ≤8000-char version and pastes it into the CAG.
3) Architect propagates:
   - Copy densified CAG text into `/docs/CAG_spec.md` (Codex-visible).
   - Copy `/AGENTS.md` into `/docs/AGENTS_mirror.md` (CAG-visible).
4) CI validates Model G2 (bundle headers + mirror byte-equality).

**Edits flow only from the Blueprint**
- Any change to CAG’s instructions or AGENTS.md must originate from a Blueprint change (which increments Bundle-ID).
- Direct edits to `/AGENTS.md`, `/docs/CAG_spec.md`, or `/docs/AGENTS_mirror.md` are prohibited; regenerate instead.

**CI additions**
- Verify `/AGENTS.md` and `/docs/CAG_instructions_master.md` carry the Bundle header.
- Verify mirrors are byte-equal once Architect propagates.

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
TIMESTAMP: <UTC YYYYMMDD_HHMMSS>
prompt_id: <UUID or commit hash>
~~~~

**Audit-Path Stub**

~~~~
TASK: <short>
OBJECTIVE: <criteria>
CONSTRAINTS: Audit-Path; multi-file allowed; require Builder confirmation token; rollback required; enumerate dependencies; full tests.
SCOPE: {paths: [..], create_missing: ask}
OUTPUTFORMAT: {design_brief, risk_matrix, staged_patches, test_plan, DIAGMETA, DIFFSUMMARY}
TIMESTAMP: <UTC YYYYMMDD_HHMMSS>
prompt_id: <UUID or commit hash>
~~~~
