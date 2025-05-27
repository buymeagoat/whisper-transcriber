Whisper Transcriber — Full System Blueprint and Guardrails

🎯 Final Outcome Directive

This project must culminate in an application that:

* Is usable and intuitive for non‑technical users with no prior AI experience
* Makes audio transcription fast, obvious, and frictionless from upload to result
* Provides a guided and well‑labeled UI with clear system feedback
* Surfaces transcripts as structured, navigable, and human‑readable documents
* Automatically stores and indexes metadata for downstream AI retrieval or project linkage
* Proactively guides the user toward this vision
* Identifies and closes any gaps in implementation that would hinder usability, clarity, or semantic utility

🔭 Project Vision

An AI‑enhanced transcription and job‑management tool for uploading audio/video, monitoring progress, and retrieving enriched transcripts in a clean web‑based frontend backed by a Python FastAPI backend.

Goal: Build a scalable MVP supporting real‑time job tracking, structured metadata enrichment, user annotations, and context‑aware AI integration.

🗂️ Folder and File Structure

```
whisper‑transcriber/
├── api/
│   ├── __pycache__
│   ├── main.py                # FastAPI app, all API endpoints
│   ├── jobs.db                # SQLite DB file
│   ├── metadata_writer.py     # Generate transcript metadata
│   └── logs/                  # Per‑job log storage
├── frontend/
│   ├── dist/
│   ├── node_modules/
│   ├── public/
│   ├── src/
│   │   ├── App.jsx            # Main React Router + Nav
│   │   ├── main.jsx           # Entrypoint
│   │   ├── UploadPage.jsx
│   │   ├── ActiveJobsPage.jsx
│   │   ├── CompletedJobsPage.jsx
│   │   ├── TranscriptViewPage.jsx
│   │   ├── AdminLogsPage.jsx
│   │   ├── DashboardPage.jsx  # (NEW) Summary overview of jobs + stats
│   │   └── SettingsPage.jsx   # (Future) Server/admin configuration
│   └── assets/
│       └── ... static files
├── logs/
├── metadata/
├── models/
├── transcripts/
├── uploads/
├── venv/
├── .gitignore
├── design_scope.md
├── jobs.db
├── requirements.txt
├── schema.sql
└── orchestrate.py             # CLI batch orchestrator
```

---

🚀 **Development Quick‑Start**

**Backend**

```bash
poetry install  # or pip install -r requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend**

```bash
npm install
npm run dev        # http://localhost:5173
```

For a production build, run `npm run build` and serve the generated `dist/` folder with an ASGI static files mount.

---

🛠️ **Logging Policy**

| Concern          | Decision                                                                       |
| ---------------- | ------------------------------------------------------------------------------ |
| Per‑job log path | `backend/logs/{job_id}.log`                                                    |
| Rotation         | `RotatingFileHandler`, max 10 MB, 3 backups                                    |
| Levels           | `DEBUG` in dev, `INFO` in prod                                                 |
| Surfacing errors | Backend returns `detail` in JSON; frontend shows toast + link to AdminLogsPage |
| Retention        | 30 days or 1 GB total, whichever first                                         |

---

🔄 **Job Restart UX**

1. **UI affordance:** On *CompletedJobsPage* each job row shows a “↻ Restart” icon‑button.
2. **Endpoint:** `POST /jobs/{id}/restart`

   * Re‑queues the media using same parameters.
   * Returns new `job_id`.
3. **State flow:** New job appears in ActiveJobsPage. Original job remains archived.
4. **Guardrail:** Backend enforces a single concurrent restart per source file.

---

⚙️ **Ingestion Timing Flag**

| Scenario              | Parameter              | Outcome                                               |
| --------------------- | ---------------------- | ----------------------------------------------------- |
| Auto ingest (default) | `ingest=true`          | Transcript automatically written to vector DB         |
| Manual ingest later   | `ingest=false`         | User clicks “Ingest” on TranscriptViewPage when ready |
| CLI override          | `--ingest/--no-ingest` | Mirrors API behaviour                                 |

---

📄 **`metadata_writer.py` Responsibilities**

* **Trigger:** Called by backend once transcription finishes *or* via CLI for batch re‑processing.
* **Inputs:**

  * `job_id`
  * Raw transcript JSON from Whisper/Faster‑Whisper
  * Media file metadata (duration, sample‑rate)
* **Processing:**

  * Compute duration, token counts, language, average WPM.
  * Generate 500‑char abstract and keyword list.
  * Detect speaker changes if diarization data present.
* **Outputs:**

  * Persist row in `metadata` table (`job_id`, `lang`, `tokens`, `duration`, `abstract`, `vector_id`).
  * Write sidecar markdown (`transcript.md`) and JSON (`metadata.json`) under `transcripts/{job_id}/`.
* **Properties:** Pure function, deterministic, no global state.

---

✅ **Status Summary**

| Component              | Status    |
| ---------------------- | --------- |
| UploadPage.jsx         | TODO      |
| ActiveJobsPage.jsx     | ✅ Stable  |
| CompletedJobsPage.jsx  | ✅ Stable  |
| TranscriptViewPage.jsx | ✅ Stable  |
| AdminLogsPage.jsx      | ✅ Stable  |
| DashboardPage.jsx      | TODO      |
| main.py (API)          | ✅ Stable  |
| orchestrate.py         | TODO      |
| metadata\_writer.py    | ✅ Defined |

---

🎨 **UI & UX Detailed Guidance**

##### End‑User Experience

1. **UploadPage** – drag‑and‑drop, **drag‑select multi‑upload** (shift‑click or marquee) up to 10 files ≤ 2 GB each; file cards cascade with inline validation (format / size / duration).
2. **ActiveJobsPage** – real‑time table with status chip (Queued ▢ / Processing ◔ / Enriching … / Done ✔), ETA **smoothed with exponential moving average** to avoid jitter; heartbeat dot blinks each 5 s; progress bar animates continuously.
3. **CompletedJobsPage** – sortable list; actions: ▸ View, ⭳ Download .txt/.md, ↻ Restart, 🗑 Delete; filter textbox; stable URLs `/transcripts/{job_id}`.
4. **TranscriptViewPage** – two‑pane: left time‑stamped transcript; right metadata sidebar; toolbar: Copy, Download, Ingest, Edit Notes.
5. **Global UI & Responsiveness** – sticky top‑bar with brand + job counter; left drawer nav. **Mobile layout**: 375 px breakpoint collapses nav into bottom tab‑bar, cards stack vertically, progress bar becomes thin line under filename. WCAG‑AA colours (#2563eb primary, #facc15 accent); keyboard‑nav and ARIA labels placeholder tickets created.
6. **Tutorial & FAQ** – *placeholders only* (hidden routes `/tutorial` & `/faq` for future enable).

##### Administrator Experience

1. **DashboardPage** – KPI cards (Active, Failed, Avg ETA, Storage Used) + 24 h throughput chart.
2. **AdminLogsPage** – live tail via WebSocket, severity filter, log download, purge.
3. **SettingsPage (Placeholder)** – env overrides, retention, concurrency, API keys.
4. **Job Controls** – restart, force ingest, delete; batch select.

##### Page Responsibility Clarifications

| Page/Script       | Core Responsibilities                                                                                        |
| ----------------- | ------------------------------------------------------------------------------------------------------------ |
| UploadPage.jsx    | File selection/validation, POST `/jobs/`, optimistic UI card, redirect to ActiveJobsPage                     |
| DashboardPage.jsx | Admin‑only KPI overview, throughput chart, top offenders list                                                |
| orchestrate.py    | CLI batch runner: scans folder, POST `/jobs/` sequentially or in parallel, optional `--watch` for completion |

🗄️ **Persistent Job History Through Restarts**

* **Database** – SQLite `jobs.db` persists all job rows (`id`, `state`, `media_path`, `created_at`, `completed_at`, etc.).
* **Startup Routine** – backend loads jobs where `state IN ('queued','processing','enriching')` and re‑queues them; `state='completed'|'failed'|'cancelled'` populate CompletedJobsPage.
* **Frontend** – on app boot, React queries `/jobs/active` & `/jobs/completed` to hydrate tables.
* **Graceful Shutdown** – workers trap SIGTERM, store heartbeat before exit.
* **Migration Path** – if DB schema changes, Alembic migration scripts ensure historic rows survive.

### Job State Machine & Controls

| UI Chip          | Backend State | Description                                    | User Actions                                 |
| ---------------- | ------------- | ---------------------------------------------- | -------------------------------------------- |
| ▢ **Queued**     | `queued`      | Accepted, waiting for worker slot.             | **Cancel & Delete** (instant)                |
| ◔ **Processing** | `processing`  | Whisper model running.                         | Cancel (until 75 % complete)                 |
| … **Enriching**  | `enriching`   | `metadata_writer.py` generating meta + ingest. | No user action (ensures integrity)           |
| ✔ **Done**       | `completed`   | Transcript + metadata written.                 | View ▸ Transcript, Download, Restart, Delete |
| ✖ **Failed**     | `failed`      | Error, log available.                          | View details, Restart, Delete                |
| ⊘ **Cancelled**  | `cancelled`   | User aborted before 75 %.                      | Restart, Delete                              |

#### Restart Rules

* Available for **Done**, **Failed**, **Cancelled**, and auto‑failed *Stalled* jobs via ↻ icon.
* Endpoint: `POST /jobs/{id}/restart` → returns new `job_id`.
* Backend guardrail: disallows >1 concurrent restart per source file.

#### Delete Policy

| State Group                  | Button Label      | Behaviour                                     |
| ---------------------------- | ----------------- | --------------------------------------------- |
| Queued / <75 % Processing    | Cancel & Delete   | Immediate cancel; data purged; row removed    |
| ≥75 % Processing / Enriching | Mark for Deletion | Flag stored; purge once job completes         |
| Done / Failed / Cancelled    | Delete            | Removes transcript + metadata; row disappears |
| Admin override               | Force Delete      | Hard kill + disk purge regardless of state    |

#### Stall Detection & Auto‑Recovery

| Parameter                     | Default                         | Rationale                           |
| ----------------------------- | ------------------------------- | ----------------------------------- |
| Heartbeat interval            | 5 s                             | Worker sends `/jobs/{id}/heartbeat` |
| Stall Warning Banner          | 60 s silence                    | Allows minor network hiccups        |
| Stall Fail → `failed_stalled` | 15 min **or** 3× media duration | Prevents infinite locks             |
| Auto‑Restart (admin opt‑in)   | off                             | Requires explicit user ↻ restart    |

When a job flips to `failed_stalled`, the row shows ✖ Failed with tooltip *Stalled – no progress*; user may ↻ Restart.

---

### 🚑 Implementation Guarantees & Mitigation Paths

#### Data Model & Alembic Migrations

* **Schema** (`jobs`, `metadata`, `heartbeats`, `users` placeholder).
* **Migration Tool**: Alembic; revision scripts live under `backend/migrations/`.
* **Command**: `alembic upgrade head` on start‑up.
* **CI Check**: GitHub Action runs `alembic check` to ensure models ↔ migrations parity.

#### API Contract & Versioning

* FastAPI auto‑generates **OpenAPI JSON** at `/openapi.json` and Swagger UI at `/docs`.
* Freeze contract by exporting `openapi_v1.json` in repo; breaking changes require `v2` route prefix.

#### Error‑Code Catalogue

| Code  | Meaning                   | Frontend Toast                    |
| ----- | ------------------------- | --------------------------------- |
| 40001 | Unsupported media format  | "Format not supported. See help." |
| 40002 | File too large (>2 GB)    | "File exceeds 2 GB limit."        |
| 40401 | Job not found             | "Job no longer exists."           |
| 40901 | Duplicate job in progress | "Already processing this file."   |
| 50001 | Whisper runtime error     | "Transcription failed — retry."   |

#### Test Strategy & CI/CD

* **Unit Tests**: `pytest` targeting utils + endpoints (≥80 % coverage gate).
* **Integration**: Docker‑compose up backend+worker; run `pytest tests/integration`.
* **Continuous Integration**: GitHub Actions matrix (py3.10/3.11, Node 18), job phases lint → test → build.

#### Security Posture (MVP)

* **Deployment** behind university VPN or localhost only.
* **Optional Token Auth**: `X‑API‑Token` header checked against env var; placeholder routes protected via FastAPI dependency.
* **Future**: OAuth2/JWT with role claims.

🧱 Future Features (post‑MVP) — **Placeholders already wired in code/UI**

* 🔐 **Multi‑user authentication & role‑based access** – login page + protected routes stubbed.
* ⚙️ **Queue scaling (Redis/RQ) & worker autoscaling** – env vars + Docker Compose placeholders.
* 📊 **Observability (Prometheus metrics, Grafana dashboards)** – `/metrics` endpoint stub.
* 🛠️ **CI/CD pipeline & automated tests** – GitHub Actions workflow present, tests TODO.
* 🦾 **Accessibility (ARIA, keyboard‑nav audit)** – a11y tickets tracked.
* 🍱 **Batch drag/drop multiple files** – **implemented** in UploadPage.
* 📝 **Subtitle (SRT/VTT) export** – route `/jobs/{id}/subtitle` placeholder.
* 🌐 **Tutorial, FAQ, Localization** – hidden routes `/tutorial`, `/faq`, `/i18n` ready but disabled.

---

🧭 Update Instructions
