# Project Design Overview

This repository implements a self‑contained audio transcription service. A FastAPI backend wraps the OpenAI Whisper command line tool and exposes endpoints for uploading audio, tracking progress, and retrieving transcripts.

## Minimum Viable Product
The application is considered working once these basics are functional:
- Jobs can be submitted with `/jobs` and processed with the Whisper CLI.
- Job status can be queried and transcripts downloaded.
- Metadata is generated and stored alongside transcripts.
- Alembic migrations run automatically so the SQLite schema is up to date.
- Logs are written for each job and for overall system activity.

## Architecture
- **FastAPI entry point**: `api/main.py` bootstraps the web app. It mounts static directories, sets up CORS, and defines all API endpoints.
- **Database layer**: SQLAlchemy ORM models are defined in `api/models.py` (`jobs` and `metadata` tables). `api/orm_bootstrap.py` runs Alembic migrations and validates the schema on startup.
- **Job flow**:
  1. Audio is uploaded via `POST /jobs`. The server stores it under `uploads/` and creates a new `Job` record.
  2. `handle_whisper` spawns the Whisper CLI to generate a `.srt` file under `transcripts/{job_id}`. The job status moves from `queued` → `processing`.
  3. On success the transcript is enriched by `metadata_writer.py`, which creates a JSON metadata file and DB entry. Status becomes `completed`. Failures update the status accordingly and save logs under `logs/`.

## Important Directories
- `uploads/` – user-uploaded audio files.
- `transcripts/` – per‑job folders containing `.srt` results and metadata.
- `logs/` – rotating log files for jobs and the system.
- `models/` – where Whisper models are stored if downloaded.
- `frontend/` – React app bundled into `api/static/` for the UI.

Key environment files include `pyproject.toml`, `requirements.txt`, and the `Dockerfile` used to build a runnable image. The older `audit_environment.py` helper script is optional and may be removed.

## API Overview
- **Job management**: `POST /jobs` to upload, `GET /jobs` and `GET /jobs/{id}` to query, `DELETE /jobs/{id}` to remove, `POST /jobs/{id}/restart` to rerun, and `/jobs/{id}/download` to fetch the transcript. `GET /metadata/{id}` returns generated metadata.
- **Admin actions** under `/admin` allow listing and deleting files, downloading all artifacts, resetting the system, and retrieving basic stats.
- **Logging endpoints** expose job logs and the access log. Static files under `/uploads`, `/transcripts`, and `/static` are served directly.

## Migrations and Logging
- Database schema migrations are managed with Alembic in `api/migrations/`. The `env.py` file loads `Base.metadata` so new models are detected automatically. Migration scripts live in `api/migrations/versions/`.
- Logging utilities in `api/utils/logger.py` create rotating per-job logs and a system log. Log level and optional stdout logging are controlled by environment variables.

This document summarizes the repository layout and how the core FastAPI service orchestrates Whisper transcription jobs.

## Current Functionality

### Frontend
- React-based single page app built with Vite and bundled under `api/static/`.
- Upload page lets users choose audio files and Whisper model size, then starts jobs and links to a status view.
- Active, Completed and Failed pages display jobs filtered by status with actions to view logs or restart/remove.
- Transcript viewer shows the final text in a simple styled page.
- Admin page lists server files, CPU/memory stats and provides buttons to reset the system or download all data.

### Backend
- REST endpoints handle job submission, progress checks, downloads and admin operations.
- Whisper runs in a background thread writing transcripts to `transcripts/` and logs to `logs/`.
- Metadata is extracted from each transcript and persisted to SQLite.
- Jobs survive server restarts by being rehydrated on startup if processing was incomplete.
## Additional Tweaks and Features

The list below ranks future enhancements from simplest to most complex. Items marked **Done** are present in the current codebase.

1. **Start a New Job button after upload** – **Done**
2. **Replace default favicon** – **Done**
3. **Show Docker stats in Admin** – **Done** (`/admin/stats`)
4. **Local-time timestamps instead of UTC** – Not yet
5. **Job runtime display (live & final)** – Not yet
6. **Kill (cancel) a running job** – Not yet
7. **Stop / Restart server from Admin** – Not yet
8. **Web-based file manager for logs/uploads/transcripts** – **Done** (`/admin/files`)
9. **Shell access via web UI** – Not yet

### Ideas from Historic Documents

10. **Resume jobs after crash or cancel** – from archived designs
11. **Stream logs to UI via WebSocket** – from handoff notes
12. **Download job archive (.zip)** – transcripts and logs together
13. **Role-based authentication** – admin can add users
14. **Expose `/metrics` endpoint for monitoring**
15. **Auto-delete old transcripts after 30 days**
16. **Add `/health` and `/version` endpoints** – verify service status
17. **Improve status messaging in UI** – show queueing/transcribing/saving
18. **Provide CLI wrapper for non-UI usage**
19. **Queue limit or concurrency throttle** – prevent overload
20. **Support `.vtt` transcript export**
21. **Docker Compose setup** – optional container orchestration
22. **Admin panel health checks and job cleanup**
23. **UI progress bars with word-level timestamps**


24. **Allow multiple files per upload with validation** – upcoming UI change
25. **Dashboard KPIs for throughput** – show metrics on admin page
26. **Settings page to customize default model** – choose options
27. **Enhance CLI orchestrate.py with watch mode** – monitor jobs from CLI
28. **Heartbeat table and `/heartbeat` endpoint** – detect stalled workers
29. **Web-based log viewer** – display logs in browser
30. **Sortable and searchable job lists** – filter by file name or status
31. **Status toasts for admin actions** – show success messages
32. **Playback or text toggle for completed jobs** – media or text view
33. **Use `updated_at` for job sorting/pagination** – future feature
34. **Download transcripts as `.txt`** – preserve timestamps
35. **Zip download of all data** – **Done** (`/admin/download-all`)
