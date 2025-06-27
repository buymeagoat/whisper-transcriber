# Project Design Overview

This repository implements a self‑contained audio transcription service. A FastAPI backend wraps the OpenAI Whisper command line tool and exposes endpoints for uploading audio, tracking progress, and retrieving transcripts.

## Documentation Policy

All contributors—including Codex—must update this document and `README.md` whenever features or configuration change. Keeping both files synchronized ensures the instructions remain accurate.

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
- When `STORAGE_BACKEND=cloud` these directories serve as a local cache and
  transcript files are synchronized from S3 when requested.
 - `MODEL_DIR` specifies where the Whisper models are stored. By default this directory is `models/` which is local only and never committed. It must contain `base.pt`, `large-v3.pt`, `medium.pt`, `small.pt`, and `tiny.pt` when building the image. The application checks for these files on startup.
- `frontend/` – React app built into `frontend/dist/` and copied by the Dockerfile
  to `api/static/` for the UI.

Both `models/` and `frontend/dist/` are listed in `.gitignore`. They must exist
before running `docker build`:
```bash
cd frontend
npm run build
cd ..
```

Key environment files include `pyproject.toml`, `requirements.txt`, and the `Dockerfile` used to build a runnable image. The older `audit_environment.py` helper script is optional and may be removed.

## Configuration

Application settings come from `api/settings.py`. It reads environment
variables once using `pydantic.BaseSettings` and exposes a `settings`
object used throughout the code base. Available variables are:

- `DB_URL` – database URL.
- `DB` – SQLite path overriding `DB_URL`.
- `VITE_API_HOST` – base URL for the frontend to reach the API.
- `VITE_DEFAULT_TRANSCRIPT_FORMAT` – default download format used by the web UI (defaults to `txt`).
- `LOG_LEVEL` – log level for backend loggers.
- `LOG_TO_STDOUT` – mirror logs to the console when `true`.
- `LOG_MAX_BYTES` – maximum size of log files before rotation (defaults to
  `10000000`).
- `LOG_BACKUP_COUNT` – number of rotated files to keep (defaults to `3`).
- `AUTH_USERNAME` / `AUTH_PASSWORD` – *(deprecated)* old static credentials.
- `ALLOW_REGISTRATION` – enable the `/register` endpoint.
- `SECRET_KEY` – secret for JWT signing.
- `ACCESS_TOKEN_EXPIRE_MINUTES` – JWT lifetime.
- `MAX_CONCURRENT_JOBS` – worker thread count for the internal queue.
- `JOB_QUEUE_BACKEND` – queue implementation (`thread` by default).
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

## API Overview
- **Job management**: `POST /jobs` to upload, `GET /jobs` and `GET /jobs/{id}` to query, `DELETE /jobs/{id}` to remove, `POST /jobs/{id}/restart` to rerun, and `/jobs/{id}/download` to fetch the transcript. `GET /metadata/{id}` returns generated metadata.
- **Admin actions** under `/admin` allow listing and deleting files, downloading all artifacts, resetting the system, configuring cleanup via `/admin/cleanup-config`, and retrieving CPU/memory stats plus job KPIs.
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
- Transcript viewer shows the final text in a simple styled page.
- Admin page lists server files, shows CPU/memory usage and KPIs (completed job count, average job time and queue length), and provides buttons to reset the system or download all data.

### Backend
- REST endpoints handle job submission, progress checks, downloads and admin operations.
- Whisper runs in a background thread writing transcripts to `transcripts/` and logs to `logs/`.
- Metadata is extracted from each transcript and persisted to SQLite.
- Jobs survive server restarts by being rehydrated on startup if processing was incomplete.

## Future Updates
<!-- Codex: Keep table cells padded to uniform column widths when updating. -->

| Feature Idea                                                         | Status    | Reasoning                        | Considerations                 | Roadblocks                    |
| -------------------------------------------------------------------- | --------- | -------------------------------- | ------------------------------- | ----------------------------- |
| Global state management                                              | Done   | Share job data across components | Choose state library            | Data sync complexity        |
| Sortable job table component                                        | Open   | Track jobs more easily            | Table library, UI state         | None                        |
| Notification/toast system                                           | Done   | Surface status messages          | Auto-dismiss timing             | None                        |
| Admin dashboard KPIs                                                | Done   | Monitor throughput               | Metrics queries                 | None                        |
| Role-based auth with settings page                                  | Done   | Restrict features per role       | Session handling, UI            | User management complexity    |
| Download job archive (.zip)                                          | Done      | Zip existing logs and results    | Avoid large file memory use     | None                          |
| Support `.vtt` transcript export                                     | Done      | Convert from SRT to VTT          | Extra dependency for conversion | None                          |
| Provide CLI wrapper for non-UI usage                                 | On Hold      | Wrapper script around API calls  | Package distribution            | None                          |
| Improve status messaging in UI                                       | Done      | Real-time updates via progress WebSocket | Friendlier labels, localization | None                          |
| Job runtime display (live & final)                                   | Open      | Track job start and end times    | Store runtime data              | None                          |
| Admin panel health checks and job cleanup                            | Open      | Add checks and cleanup hooks     | Permission checks               | None                          |
| Queue limit or concurrency throttle                                  | Done      | Throttle worker count            | Configurable limits             | None                          |
| Docker Compose setup                                                 | Done      | Provide sample compose file      | Keep dev/prod parity            | None                          |
| Dashboard KPIs for throughput                                        | Open      | Show totals and averages         | Pull metrics from DB            | None                          |
| Role-based authentication                                            | Done      | Add user roles table             | Password storage, security      | User management complexity    |
| Settings page to customize default model                             | Open      | UI for selecting models          | Persist user prefs              | None                          |
| Allow multiple files per upload with validation                      | Open      | Adjust upload handler            | File size and concurrency       | None                          |
| Web-based log viewer                                                 | Open      | Simple log tail view             | Log file rotation               | Large logs                    |
| Sortable and searchable job lists                                    | Open      | Add filters on table views       | DB query optimization           | None                          |
| Status toasts for admin actions                                      | Open      | Display toast on success/failure | Frontend state management       | None                          |
| Playback or text toggle for completed jobs                           | Open      | Switch between audio and text    | Media player integration        | None                          |
| Use `updated_at` for job sorting/pagination                          | Open      | Modify queries                   | Add index                       | None                          |
| Enhance CLI orchestrate.py with watch mode                           | Open      | Poll API in loop                 | Handle auth tokens              | None                          |
| Heartbeat table and `/heartbeat` endpoint                            | Open      | Record worker heartbeats         | Extra DB writes                 | None                          |
| Kill (cancel) a running job                                          | Open      | Send termination signal          | Handle partial output           | Process management            |
| Stop / Restart server from Admin                                     | Done      | Admin commands to stop and start | Risk of accidental shutdown     | Requires elevated permissions |
| Shell/CLI access from admin page                                     | Open      | Web terminal component           | Security and sandboxing         | Major security risk           |
| Resume jobs after crash or cancel                                    | Open      | Persist intermediate state       | Robust job recovery             | Complex state handling        |
| Stream logs to UI via WebSocket                                      | Done      | Push log lines live              | Scalability of sockets          | None                          |
| UI progress bars with word-level timestamps                          | Open      | Parse SRT positions              | Frequent UI updates             | None                          |
| Auto-delete old transcripts after 30 days                            | Done         | Background cleanup task          | Configurable retention          | None                          |
| Workflow automation hooks                                            | Open      | Fire webhook on job completion   | Configurable URLs               | Security of hooks             |
| Audio format conversion                                              | Open      | Use ffmpeg for re-encoding       | Manage codecs                   | None                          |
| Audio cleanup utilities                                              | Open      | Noise reduction pipeline         | CPU usage                       | External libs                 |
| Integration with meeting platforms                                   | Open      | OAuth with Zoom/Meet APIs        | API rate limits                 | Authentication complexity     |
| Searchable transcript archive                                        | Open      | Full-text search index           | Storage footprint               | Search engine setup           |
| Speaker diarization support                                          | Open      | Use speaker detection models     | Model accuracy                  | Heavy processing              |
| Summarization and keyword extraction                                 | Open      | NLP summarizer models            | Prompt quality                  | Compute load                  |
| Automatic language translation                                       | Open      | Translate final text             | Choose translation service      | API cost                      |
| AI-powered sentiment analysis                                        | Open      | Run sentiment model on segments  | Language coverage               | Accuracy                      |
| Live streaming transcription                                         | Open      | Transcribe streaming audio       | Buffer management               | Real-time latency             |
| Voice cloning for playback                                           | Open      | Synthesize corrected speech      | Ethical concerns                | Requires heavy models         |
| Comprehensive audio toolbox                                          | Open      | Combine many tools in UI         | Complexity of options           | Maintenance burden            |
| Text-to-speech from documents                                        | Open      | Generate audio from text         | Multi-language support          | TTS model size                |
| Mobile voice memo support                                            | Open      | Mobile upload workflow           | Touch-friendly UI               | None                          |
| LLM-powered transcript insights                                      | Open      | Send transcript to LLM service   | Token limits, privacy           | API cost                      |
| Collaborative transcript editing                                     | Open      | Multi-user editing UI            | Real-time sync                  | Conflict resolution           |
| Automated meeting minutes                                            | Open      | Compose summary + action items   | Integration with calendars      | Summarization accuracy        |
| Cloud storage sync                                                   | Open      | Upload artifacts to cloud drives | OAuth + API quotas              | Reliability of sync           |
| Personalized speech models                                           | Open      | Fine-tune recognition per user   | Training data storage           | Model training cost           |
| Sign language video generation                                       | Open      | Generate sign language videos    | Signer avatar quality           | Very heavy compute            |
| Start a New Job button after upload                                  | Done      |                                  |                                 |                               |
| Replace default favicon                                              | Done      |                                  |                                 |                               |
| Show Docker stats in Admin (`/admin/stats`)                          | Done      |                                  |                                 |                               |
| Web-based file browser for logs/uploads/transcripts (`/admin/browse`) | Done      | Replaces inline lists with a navigable UI | Delete/download actions in UI |                        |
| Zip download of all data (`/admin/download-all`)                     | Done      |                                  |                                 |                               |
| Expose `/metrics` endpoint for monitoring                            | Done      |                                  |                                 |                               |
| Progress WebSocket (`/ws/progress/{job_id}`) sends status updates    | Done      |                                  |                                 |                               |
| Health check (`/health`) and version info (`/version`)               | Done      |                                  |                                 |                               |
| Local-time timestamps shown in the UI                                | Done      |                                  |                                 |                               |
| Download transcripts as `.txt` (default in UI)                       | Done      |                                  |                                 |                               |
| Directory browser API (`/admin/browse`)                              | Done   |                                  |                                 |                        |
\nCleanup retention can be configured via the `/admin/cleanup-config` endpoint.
