# Project Design Overview

This repository implements a self‑contained audio transcription service. A FastAPI backend wraps the OpenAI Whisper command line tool and exposes endpoints for uploading audio, tracking progress, and retrieving transcripts.

## Documentation Policy

All contributors—including Codex—must update this document and `README.md` whenever features or configuration change. Keeping both files synchronized ensures the instructions remain accurate.

## Minimum Viable Product
The application is considered working once these basics are functional:
- Jobs can be submitted with `/jobs` and processed with the Whisper CLI.
- Job status can be queried and transcripts downloaded.
- Metadata is generated and stored alongside transcripts.
- Alembic migrations run automatically so the database schema is up to date.
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
- When `STORAGE_BACKEND=cloud` these directories serve as a local cache and
  transcript files are synchronized from S3 when requested.
 - `MODEL_DIR` specifies where the Whisper models are stored. By default this directory is `models/` which is local only and never committed. It must contain `base.pt`, `large-v3.pt`, `medium.pt`, `small.pt`, and `tiny.pt` when building the image. The application checks for these files on startup.
- `frontend/` – React app built into `frontend/dist/` and copied by the Dockerfile
  to `api/static/` for the UI.
- `scripts/` – packaging helpers that generate `dist/whisper-transcriber.exe` and `dist/whisper-transcriber.rpm`.
- `start_containers.sh` – helper script that builds the frontend if needed and launches the Docker Compose stack (`api`, `worker`, `broker`, and `db`).

Both `models/` and `frontend/dist/` are listed in `.gitignore`. They must exist
before running `docker build`:
```bash
cd frontend
npm run build
cd ..
```
Provide a `SECRET_KEY` as a build argument since the image runs a validation
step that loads application settings:
```bash
docker build --build-arg SECRET_KEY=<your_key> -t whisper-app .
```

Key environment files include `pyproject.toml`, `requirements.txt`, and the `Dockerfile` used to build a runnable image. The older `audit_environment.py` helper script is optional and may be removed.

## Configuration

Application settings come from `api/settings.py`. It reads environment
variables once using `pydantic_settings.BaseSettings` and exposes a `settings`
object used throughout the code base. The legacy `api/config.py` module is
retained only for backward compatibility and will be removed in a future
release. Available variables are:

- `DB_URL` – SQLAlchemy connection string for the required PostgreSQL
  database. The default
  `postgresql+psycopg2://whisper:whisper@db:5432/whisper` points to the `db`
  service defined in `docker-compose.yml`.
- `VITE_API_HOST` – base URL for the frontend to reach the API.
- `VITE_DEFAULT_TRANSCRIPT_FORMAT` – default download format used by the web UI (defaults to `txt`).
- `LOG_LEVEL` – log level for backend loggers.
- `LOG_TO_STDOUT` – mirror logs to the console when `true`.
- `LOG_MAX_BYTES` – maximum size of log files before rotation (defaults to
  `10000000`).
- `LOG_BACKUP_COUNT` – number of rotated files to keep (defaults to `3`).
- `DB_CONNECT_ATTEMPTS` – how many times to retry connecting to the database on
  startup (defaults to `10`).
- `AUTH_USERNAME` / `AUTH_PASSWORD` – *(deprecated)* old static credentials.
- `ALLOW_REGISTRATION` – enable the `/register` endpoint.
- `SECRET_KEY` – secret for JWT signing.
- `ACCESS_TOKEN_EXPIRE_MINUTES` – JWT lifetime.
- `MAX_CONCURRENT_JOBS` – worker thread count for the internal queue. This value can be changed at runtime via `/admin/concurrency`.
- `JOB_QUEUE_BACKEND` – queue implementation (`thread` by default).
- Celery must be installed when `JOB_QUEUE_BACKEND=broker` or using Docker
  Compose.
- `STORAGE_BACKEND` – where uploads and transcripts are stored.
- `LOCAL_STORAGE_DIR` – base directory for the local storage backend. Defaults
  to the repository root.
- `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` – credentials for the cloud
  storage backend.
- `S3_BUCKET` – name of the bucket used by `CloudStorage`.
- `CELERY_BROKER_URL` and `CELERY_BACKEND_URL` – URLs for the broker and
  result backend when using the `broker` queue backend.
- `CLEANUP_ENABLED` – toggle periodic cleanup of old transcripts (default `true`).
- `CLEANUP_DAYS` – number of days to retain transcripts when cleanup is enabled
  (defaults to `30`).
- `CLEANUP_INTERVAL_SECONDS` – how often the cleanup task runs
  (defaults to `86400`).
- `ENABLE_SERVER_CONTROL` – allow `/admin/shutdown` and `/admin/restart`
  endpoints (defaults to `false`).
- `TIMEZONE` – local timezone name used for log timestamps (defaults to `UTC`).
- `CORS_ORIGINS` – comma-separated list of allowed CORS origins (defaults to `*`).
- `WHISPER_BIN` – path to the Whisper CLI executable (defaults to `whisper`).
- `WHISPER_LANGUAGE` – language code passed to Whisper (defaults to `en`).
- `MODEL_DIR` – directory containing Whisper models (defaults to `models/`).
- `OPENAI_API_KEY` – API key enabling transcript analysis via OpenAI.
- `OPENAI_MODEL` – model name used when `OPENAI_API_KEY` is set (defaults to `gpt-3.5-turbo`).

## API Overview
- **Job management**: `POST /jobs` to upload, `GET /jobs` (with optional `search` query filtering by ID, filename or keywords) and `GET /jobs/{id}` to query, `DELETE /jobs/{id}` to remove, `POST /jobs/{id}/restart` to rerun, and `/jobs/{id}/download` to fetch the transcript. `GET /metadata/{id}` returns generated metadata.
- **Admin actions** under `/admin` allow listing and deleting files, downloading all artifacts and packaged binaries via `/admin/download-app/{os}`, resetting the system, configuring cleanup via `/admin/cleanup-config`, adjusting concurrency via `/admin/concurrency`, and retrieving CPU/memory stats plus job KPIs.
- **Logging endpoints** expose job logs and the access log. If the access log does not exist, `/logs/access` returns a `404` with an empty body. Static files under `/uploads`, `/transcripts`, and `/static` are served directly.
- **Log streaming**: connect to `/ws/logs/{job_id}` to receive new log lines in real time. The frontend's job log view opens this socket and appends each message as it arrives.
- **System log streaming**: connect to `/ws/logs/system` to watch the access log or `system.log` in real time from the Admin page.
- **Authentication**: obtain tokens via `/token` using credentials stored in the `users` table. Accounts can be created through `/register` when enabled. Each user has a `role` of `admin` or `user`. The `/admin` and `/metrics` routes are restricted to admins.

## Migrations and Logging
- Database schema migrations are managed with Alembic in `api/migrations/`. The `env.py` file loads `Base.metadata` so new models are detected automatically. Migration scripts live in `api/migrations/versions/`.
- Logging utilities in `api/utils/logger.py` create rotating per-job logs and a system log. Log level and optional stdout logging are controlled by environment variables.

This document summarizes the repository layout and how the core FastAPI service orchestrates Whisper transcription jobs.

## Current Functionality

### Frontend
- React-based single page app built with Vite. The build outputs `frontend/dist/`,
  which the Dockerfile copies to `api/static/` for serving.
- Upload page lets users choose audio files and Whisper model size, then starts jobs and links to a status view.
- Active, Completed and Failed pages display jobs filtered by status with actions to view logs or restart/remove.
- Completed Jobs now includes a search box that filters results via the `/jobs` `search` query, matching job IDs, filenames or metadata keywords.
- Transcript viewer shows the final text in a simple styled page.
- Admin page lists server files, shows CPU/memory usage and KPIs (completed job count, average job time and queue length), and provides buttons to reset the system or download all data.
- A sidebar along the left provides tabs for each page. It also contains a **Download Desktop App** link that hits the `/download-app` endpoint.

### Backend
- REST endpoints handle job submission, progress checks, downloads and admin operations.
- Whisper runs in a background thread writing transcripts to `transcripts/` and logs to `logs/`.
- Metadata is extracted from each transcript and persisted to the database.
- Jobs survive server restarts by being rehydrated on startup if processing was incomplete.
## Roadmap
The future feature roadmap is tracked in [future_updates.md](future_updates.md).



Cleanup retention can be configured via the `/admin/cleanup-config` endpoint.
The concurrency limit can be adjusted at runtime using `/admin/concurrency`.
