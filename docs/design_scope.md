# Project Design Overview

> **Note**
> OpenAI-generated insights are automated and may contain errors. Always verify the output before relying on it.

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
- `scripts/` – helper utilities for Docker builds, testing and container management.
  - `start_containers.sh` – helper script that builds the frontend if needed, verifies required models and `.env`, then launches the Docker Compose stack (`api`, `worker`, `broker`, and `db`). It normally runs `prestage_dependencies.sh` first to refresh the `cache/` directory with Docker images and packages. Set `SKIP_PRESTAGE=1` or pass `--offline` to reuse the existing cache instead. Pass `--force-frontend` to rebuild the React UI even when `frontend/dist` already exists. When `cache/` is already populated it installs dependencies from there so the stack can start offline. All output is mirrored to `logs/start_containers.log` for troubleshooting.
  - `docker_build.sh` – performs a full rebuild or an incremental update. Pass `--full` to wipe old Docker resources and rebuild the compose stack from scratch, or `--incremental` to rebuild only missing or unhealthy images. Before building it stages all required Docker images and Python packages so network interruptions do not halt the process. Pass `--offline` or set `SKIP_PRESTAGE=1` to skip refreshing the cache. Use `--force-frontend` to rebuild the web UI even when `frontend/dist` is present. Run it after `git fetch` and `git pull` when dependencies, the Dockerfile or compose configuration change, or if the environment is out of sync. Output is saved to `logs/docker_build.log`. After rebuilding, run `scripts/run_tests.sh` to verify everything works. Use `scripts/run_backend_tests.sh` if you only need the backend tests.
  - `update_images.sh` – inspects the running containers and rebuilds only the API or worker image when its container is unhealthy or the image is missing. Healthy services are left untouched. Like `docker_build.sh` it stages dependencies up front and then verifies the Whisper models and `ffmpeg` are available. Pass `--offline` or set `SKIP_PRESTAGE=1` to skip refreshing the cache. Use `--force-frontend` to rebuild the UI even if `frontend/dist` exists. Its log is written to `logs/update_images.log`. Run it after `git fetch` and `git pull` for routine code updates.
- `prestage_dependencies.sh` – remove and repopulate `cache/` on every run with all Docker images and Python packages needed for the build. Before caching packages it checks that the Dockerfile base image codename and the host `/etc/os-release` codename are `jammy`, exiting on mismatch unless `ALLOW_OS_MISMATCH=1` is set. Because it clears the cache each time, offline startup requires skipping this step with `SKIP_PRESTAGE=1` or the `--offline` flag or manually pre-populating `cache/` before running other scripts. Pass `--checksum` to record SHA-256 sums in `cache/checksums.txt`. The build scripts automatically run this step, so invoke it manually only when you want a separate download pass.
 - The build scripts store cached packages and Docker images under `/tmp/docker_cache`. Set `CACHE_DIR` to another location—for example `/mnt/c/whisper_cache`—if you need the cache to survive WSL resets.
- All build helpers automatically install or upgrade Node.js 18 using the NodeSource repository when needed.
- `run_backend_tests.sh` – runs backend tests and verifies the `/health` and `/version` endpoints, logging output to `logs/test.log`.
- `diagnose_containers.sh` – checks that Docker is running, verifies cache directories, and prints container and build logs for troubleshooting.
 - `check_env.sh` – validates DNS resolution and ensures cached `.deb` packages
   correspond to the base image used in the Dockerfile. Cached packages must
   match the `python:3.11-jammy` image to avoid build errors.
 - `run_tests.sh` – preferred wrapper that runs backend, frontend and Cypress
  tests by default. Pass `--backend`, `--frontend` or `--cypress` to run a
  subset. Results are saved to `logs/full_test.log`.

Both `models/` and `frontend/dist/` are listed in `.gitignore`. Ensure the
Whisper models are present before running `docker build`. The precompiled
frontend assets already live under `frontend/dist/`.
Create a file containing your SECRET_KEY and pass it to BuildKit so the
validation step can load application settings. BuildKit secrets are the
preferred mechanism:
```bash
docker build --secret id=secret_key,src=<file> -t whisper-app .
```
If `docker build` does not support `--secret`, pass the key as a build
argument instead:
```bash
docker build --build-arg SECRET_KEY=<key> -t whisper-app .
```

Key environment files include `pyproject.toml`, `requirements.txt`, and the `Dockerfile` used to build a runnable image.

## Configuration

Application settings come from `api/settings.py`. It reads environment
variables once using `pydantic_settings.BaseSettings` and exposes a `settings`
object used throughout the code base. Available variables are:

- `DB_URL` – SQLAlchemy connection string for the required PostgreSQL
  database. The default
  `postgresql+psycopg2://whisper:whisper@db:5432/whisper` points to the `db`
  service defined in `docker-compose.yml`.
- `VITE_API_HOST` – base URL for the frontend to reach the API.
- `PORT` – TCP port used by the Uvicorn server (defaults to `8000`).
- `VITE_DEFAULT_TRANSCRIPT_FORMAT` – default download format used by the web UI (defaults to `txt`).
- `LOG_LEVEL` – log level for backend loggers.
- `LOG_FORMAT` – set to `json` for structured logs or `plain` for text (defaults to `plain`).
- `LOG_TO_STDOUT` – mirror logs to the console when `true`.
- `LOG_MAX_BYTES` – maximum size of log files before rotation (defaults to
  `10000000`).
- `LOG_BACKUP_COUNT` – number of rotated files to keep (defaults to `3`).
- `MAX_UPLOAD_SIZE` – maximum allowed upload size in bytes (defaults to `2147483648`).
- `DB_CONNECT_ATTEMPTS` – how many times to retry connecting to the database on
  startup (defaults to `10`).
- `BROKER_CONNECT_ATTEMPTS` – how many times to retry pinging the Celery broker
  on startup (defaults to `20`).
- `BROKER_PING_TIMEOUT` – how many seconds the worker entrypoint waits for RabbitMQ to respond before exiting (defaults to `60`).
- `API_HEALTH_TIMEOUT` – how many seconds the build scripts wait for the API container to become healthy (defaults to `300`).
- `AUTH_USERNAME` / `AUTH_PASSWORD` – *(deprecated)* old static credentials.
- `ALLOW_REGISTRATION` – enable the `/register` endpoint.
- `SECRET_KEY` – secret for JWT signing.
- `ACCESS_TOKEN_EXPIRE_MINUTES` – JWT lifetime.
- `MAX_CONCURRENT_JOBS` – worker thread count for the internal queue. This value can be changed at runtime via `/admin/concurrency`.
- `JOB_QUEUE_BACKEND` – queue implementation (`thread` by default).
- Celery is installed from `requirements.txt` and used when
  `JOB_QUEUE_BACKEND=broker` or running Docker Compose.
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
- `WHISPER_TIMEOUT_SECONDS` – maximum seconds to wait for Whisper before marking the job failed (0 disables timeout).
- `MODEL_DIR` – directory containing Whisper models (defaults to `models/`).
- `OPENAI_API_KEY` – API key enabling transcript analysis via OpenAI.
- `OPENAI_MODEL` – model name used when `OPENAI_API_KEY` is set (defaults to `gpt-3.5-turbo`).

## API Overview
- **Job management**: `POST /jobs` to upload, `GET /jobs` (with optional `search` query filtering by ID, filename or keywords) and `GET /jobs/{id}` to query, `DELETE /jobs/{id}` to remove, `POST /jobs/{id}/restart` to rerun, and `/jobs/{id}/download` to fetch the transcript. `GET /metadata/{id}` returns generated metadata.
- **Admin actions** under `/admin` allow listing and deleting files, downloading all artifacts via `/admin/download-all`, resetting the system, configuring cleanup via `/admin/cleanup-config`, adjusting concurrency via `/admin/concurrency`, and retrieving CPU/memory stats plus job KPIs.
- **Logging endpoints** expose job logs and the access log. `/log/{job_id}`, `/logs/access` and `/logs/{filename}` require authentication. If the access log does not exist, `/logs/access` returns a `404` with an empty body. Static files under `/uploads`, `/transcripts`, and `/static` are served directly.
- **Log streaming**: connect to `/ws/logs/{job_id}` to receive new log lines in real time. The frontend's job log view opens this socket and appends each message as it arrives.
- **System log streaming**: connect to `/ws/logs/system` to watch the access log or `system.log` in real time from the Admin page.
- **Authentication**: obtain tokens via `/token` using credentials stored in the `users` table. Accounts can be created through `/register` when enabled. Each user has a `role` of `admin` or `user`. The `/admin` and `/metrics` routes are restricted to admins.

## Migrations and Logging
- Database schema migrations are managed with Alembic in `api/migrations/`. The `env.py` file loads `Base.metadata` so new models are detected automatically. Migration scripts live in `api/migrations/versions/`.
- Logging utilities in `api/utils/logger.py` create rotating per-job logs and a system log. Log level and optional stdout logging are controlled by environment variables.

This document summarizes the repository layout and how the core FastAPI service orchestrates Whisper transcription jobs.

## Current Functionality

### Frontend
- React-based single page app built with Vite. The prebuilt files live in
  `frontend/dist/`, which the Dockerfile copies to `api/static/` for serving.
- Upload page lets users choose audio files and Whisper model size, then starts jobs and links to a status view.
- Active, Completed and Failed pages display jobs filtered by status with actions to view logs or restart/remove.
- Completed Jobs now includes a search box that filters results via the `/jobs` `search` query, matching job IDs, filenames or metadata keywords.
- Transcript viewer shows the final text in a simple styled page.
- Admin page lists server files, shows CPU/memory usage and KPIs (completed job count, average job time and queue length), and provides buttons to reset the system or download all data.

### Backend
- REST endpoints handle job submission, progress checks, downloads and admin operations.
- `/health` verifies the database connection and returns `{"status": "db_error"}`
  with a 500 code when the query fails.
- Whisper runs in a background thread writing transcripts to `transcripts/` and logs to `logs/`.
- Metadata is extracted from each transcript and persisted to the database.
- Jobs survive server restarts by being rehydrated on startup if processing was incomplete.
## Roadmap
The future feature roadmap is tracked in [future_updates.md](future_updates.md).



Cleanup retention can be configured via the `/admin/cleanup-config` endpoint.
The concurrency limit can be adjusted at runtime using `/admin/concurrency`.
