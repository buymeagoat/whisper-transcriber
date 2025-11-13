# Production Readiness Action Plan

## Purpose
This document translates the current remediation status and architectural guidance into a concrete, execution-ready plan to bring the Whisper Transcriber application to a production-ready state without introducing net-new feature areas.

## Guiding Decisions
- **Interface contract management:** Adopt the FastAPI OpenAPI schema as the single source of truth. Generate typed client hooks for the React application from this schema and enforce contract drift tests in CI so future changes remain coordinated.
- **User identity model:** Extend the `jobs` table with a string-based `user_id` column that mirrors authenticated accounts.
  The legacy `X-User-ID` header is now gated behind `LEGACY_USER_HEADER_ENABLED`, keeping the schema future-proof without
  requiring the header in production.
- **Incomplete features:** Finish partially implemented or stubbed functionality already present in the codebase (e.g., admin metrics routes, transcript retrieval). Defer entirely new concepts while documenting them as follow-up work.
- **Model assets:** Assume Whisper `.pt` checkpoints are staged under `/models` at deploy time. Do not introduce alternate download logic; surface clear validation errors if assets are missing.

## Workstream Breakdown

### 1. Align Web Upload Flows with FastAPI Contract
- Generate updated API client bindings (`openapi-typescript` for TypeScript types + `rtk-query` or `react-query` hooks) from the FastAPI schema during CI.
- Replace hard-coded REST paths in `TranscribePage.jsx` with calls through the generated client, covering initialization, chunk uploads, job submission, and polling.
- Update backend route handlers to accept any required compatibility aliases (e.g., temporary `/uploads/init`) with metrics to detect legacy usage, deprecating them once the frontend deploys.
- Add integration tests:
  - Frontend: Playwright smoke test that uploads a small file and observes transcript completion via mocked Whisper response.
  - Backend: pytest API test that verifies alias routes return 301/410 as scheduled when sunsetted.

### 2. Persist Job Ownership and Secure Transcript Access
- Create an Alembic migration adding `jobs.user_id` (non-nullable with backfill via existing audit trail or default staging value) and associated index.
- Thread `user_id` through direct and chunked upload services so new jobs capture ownership.
- Update `ConsolidatedTranscriptService` and related routes to enforce ownership using the stored column.
- Expand tests covering transcript listing/export, including negative cases (user tries to access another user’s job).

### 3. Restore Admin Dashboard Functionality
- Implement the documented admin endpoints:
  - `/api/admin/jobs/stats`: Aggregate job counts, states, and average durations from the database and Celery task results.
  - `/api/admin/health/system`: Expose application uptime, worker heartbeat, and model asset validation results.
  - `/api/admin/health/performance`: Surface rolling latency percentiles sourced from existing Prometheus metrics.
- Update the React admin dashboard to consume the real endpoints via generated client hooks, replacing stubbed state.
- Cover these endpoints with backend unit/integration tests and frontend component tests, including error-state rendering.

### 4. Documentation & Contract Synchronization
- Refresh `README.md`, `FUNCTIONS.md`, and API reference snippets to match the canonical `/uploads/*` and `/jobs/*` endpoints
  and document the compatibility switch (`LEGACY_USER_HEADER_ENABLED`) instead of a mandatory `X-User-ID` header.
- Document the new job ownership semantics and admin telemetry sources.
- Add a “Contract Drift” section to the contributing guide that explains how API schema updates propagate to generated clients and testing.

### 5. Regression Coverage & CI Enhancements
- Increase coverage thresholds once new negative tests are in place (target ≥60 %).
- Enforce Playwright and contract-generation steps in the CI pipeline.
- Reactivate or document gating for k6 performance runs, noting they are optional until real baselines are captured post-deployment.

## Milestones & Sequencing
1. **Week 1:** Database migration + backend service adjustments (Workstream 2), backend aliasing for uploads (Workstream 1 partial), contract generation tooling setup (Workstream 4 foundation).
2. **Week 2:** Frontend refactor to generated client (Workstream 1), transcript UI integration tests, backend tests for ownership.
3. **Week 3:** Admin endpoints and dashboard wiring (Workstream 3) with associated tests; CI enhancements (Workstream 5).
4. **Week 4:** Documentation sweep, deprecate temporary upload aliases, raise coverage gate, and stage final acceptance testing.

## Risks & Mitigations
- **Schema rollout coordination:** Mitigate by releasing migration and backend changes behind feature flags while keeping old endpoints temporarily aliased.
- **Contract generation churn:** Pin OpenAPI generation tooling versions and store generated artifacts in the repo to avoid CI/runtime drift.
- **Test flakiness (async jobs):** Use deterministic Celery eager settings in CI and seed transcripts with lightweight fixtures to keep tests reliable.

## Acceptance Criteria
- Browser upload (direct + chunked) completes successfully end-to-end against FastAPI in staging.
- Transcript retrieval/export respects user ownership and is covered by automated tests.
- Admin dashboard cards render real data without console errors.
- Documentation reflects the deployed API surface, and CI enforces contract + coverage standards.

