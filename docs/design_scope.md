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
- `models/` – directory for Whisper models. The folder is local only and never committed. It must contain `base.pt`, `large-v3.pt`, `medium.pt`, `small.pt`, and `tiny.pt` when building the image. The application checks for these files on startup. Ensure the directory contains the required models before running or building the container.
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
- `LOG_LEVEL` – log level for backend loggers.
- `LOG_TO_STDOUT` – mirror logs to the console when `true`.
- `METRICS_TOKEN` – optional bearer token for `/metrics`.
- `AUTH_USERNAME` / `AUTH_PASSWORD` – *(deprecated)* old static credentials.
- `ALLOW_REGISTRATION` – enable the `/register` endpoint.
- `SECRET_KEY` – secret for JWT signing.
- `ACCESS_TOKEN_EXPIRE_MINUTES` – JWT lifetime.
- `MAX_CONCURRENT_JOBS` – worker thread count for the internal queue.
- `JOB_QUEUE_BACKEND` – queue implementation (`thread` by default).
- `STORAGE_BACKEND` – where uploads and transcripts are stored.
- `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` – credentials for the cloud
  storage backend.
- `S3_BUCKET` – name of the bucket used by `CloudStorage`.
- `CELERY_BROKER_URL` and `CELERY_BACKEND_URL` – URLs for the broker and
  result backend when using the `broker` queue backend.

## API Overview
- **Job management**: `POST /jobs` to upload, `GET /jobs` and `GET /jobs/{id}` to query, `DELETE /jobs/{id}` to remove, `POST /jobs/{id}/restart` to rerun, and `/jobs/{id}/download` to fetch the transcript. `GET /metadata/{id}` returns generated metadata.
- **Admin actions** under `/admin` allow listing and deleting files, downloading all artifacts, resetting the system, and retrieving basic stats.
- **Logging endpoints** expose job logs and the access log. If the access log does not exist, `/logs/access` returns a `404` with an empty body. Static files under `/uploads`, `/transcripts`, and `/static` are served directly.
- **Authentication**: obtain tokens via `/token` using credentials stored in the `users` table. Accounts can be created through `/register` when enabled.

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
- Admin page lists server files, CPU/memory stats and provides buttons to reset the system or download all data.

### Backend
- REST endpoints handle job submission, progress checks, downloads and admin operations.
- Whisper runs in a background thread writing transcripts to `transcripts/` and logs to `logs/`.
- Metadata is extracted from each transcript and persisted to SQLite.
- Jobs survive server restarts by being rehydrated on startup if processing was incomplete.

## Additional Tweaks and Features
### Completed Items
- Start a New Job button after upload
- Replace default favicon
- Show Docker stats in Admin (`/admin/stats`)
- Web-based file manager for logs/uploads/transcripts (`/admin/files`)
- Zip download of all data (`/admin/download-all`)
- Expose `/metrics` endpoint for monitoring
- Progress WebSocket (`/ws/progress/{job_id}`) sends status updates

### Upcoming Ideas

<!-- Codex: Keep table cells padded to uniform column widths when updating. -->

| Rank | Feature Idea                                    | Reasoning                      | Considerations                  | Roadblocks                    |
| ---- | ----------------------------------------------- | ------------------------------ | ------------------------------- | ----------------------------- |
| 000  | Add `/health` and `/version` endpoints          | Just return status data        | Decide output format            | None                          |
| 001  | Local-time timestamps instead of UTC            | Convert timestamps on display  | Timezone handling               | None                          |
| 002  | Download transcripts as `.txt`                  | Plain text export from SRT     | Maintain timestamp accuracy     | None                          |
| 003  | Download job archive (.zip)                     | Zip existing logs and results  | Avoid large file memory use     | None                          |
| 004  | Support `.vtt` transcript export                | Convert from SRT to VTT        | Extra dependency for conversion | None                          |
| 005  | Provide CLI wrapper for non-UI usage            | Wrapper script around API calls| Package distribution            | None                          |
| 006  | Improve status messaging in UI                  | Better frontend labels         | Localization, UX tweaks         | None                          |
| 007  | Job runtime display (live & final)              | Track job start and end times  | Store runtime data              | None                          |
| 008  | Admin panel health checks and job cleanup       | Add checks and cleanup hooks   | Permission checks               | None                          |
| 009  | Queue limit or concurrency throttle             | Throttle worker count          | Configurable limits             | None                          |
| 010  | Docker Compose setup                            | Provide sample compose file    | Keep dev/prod parity            | None                          |
| 011  | Dashboard KPIs for throughput                   | Show totals and averages       | Pull metrics from DB            | None                          |
| 012  | Role-based authentication                       | Add user roles table           | Password storage, security      | User management complexity    |
| 013  | Settings page to customize default model        | UI for selecting models        | Persist user prefs              | None                          |
| 014  | Allow multiple files per upload with validation | Adjust upload handler          | File size and concurrency       | None                          |
| 015  | Web-based log viewer                            | Simple log tail view           | Log file rotation               | Large logs                    |
| 016  | Sortable and searchable job lists               | Add filters on table views     | DB query optimization           | None                          |
| 017  | Status toasts for admin actions                 | Display toast on success/failure| Frontend state management       | None                          |
| 018  | Playback or text toggle for completed jobs      | Switch between audio and text  | Media player integration        | None                          |
| 019  | Use `updated_at` for job sorting/pagination     | Modify queries                 | Add index                       | None                          |
| 020  | Enhance CLI orchestrate.py with watch mode      | Poll API in loop               | Handle auth tokens              | None                          |
| 021  | Heartbeat table and `/heartbeat` endpoint       | Record worker heartbeats       | Extra DB writes                 | None                          |
| 022  | Kill (cancel) a running job                     | Send termination signal        | Handle partial output           | Process management            |
| 023  | Stop / Restart server from Admin                | Admin commands to stop and start| Risk of accidental shutdown     | Requires elevated permissions |
| 024  | Shell access via web UI                         | Web terminal component         | Security and sandboxing         | Major security risk           |
| 025  | Resume jobs after crash or cancel               | Persist intermediate state     | Robust job recovery             | Complex state handling        |
| 026  | Stream logs to UI via WebSocket                 | Push log lines live            | Scalability of sockets          | None                          |
| 027  | UI progress bars with word-level timestamps     | Parse SRT positions            | Frequent UI updates             | None                          |
| 028  | Auto-delete old transcripts after 30 days       | Background cleanup task        | Configurable retention          | None                          |
| 029  | Workflow automation hooks                       | Fire webhook on job completion | Configurable URLs               | Security of hooks             |
| 030  | Audio format conversion                         | Use ffmpeg for re-encoding     | Manage codecs                   | None                          |
| 031  | Audio cleanup utilities                         | Noise reduction pipeline       | CPU usage                       | External libs                 |
| 032  | Integration with meeting platforms              | OAuth with Zoom/Meet APIs      | API rate limits                 | Authentication complexity     |
| 033  | Searchable transcript archive                   | Full-text search index         | Storage footprint               | Search engine setup           |
| 034  | Speaker diarization support                     | Use speaker detection models   | Model accuracy                  | Heavy processing              |
| 035  | Summarization and keyword extraction            | NLP summarizer models          | Prompt quality                  | Compute load                  |
| 036  | Automatic language translation                  | Translate final text           | Choose translation service      | API cost                      |
| 037  | AI-powered sentiment analysis                   | Run sentiment model on segments| Language coverage               | Accuracy                      |
| 038  | Live streaming transcription                    | Transcribe streaming audio     | Buffer management               | Real-time latency             |
| 039  | Voice cloning for playback                      | Synthesize corrected speech    | Ethical concerns                | Requires heavy models         |
| 040  | Comprehensive audio toolbox                     | Combine many tools in UI       | Complexity of options           | Maintenance burden            |
| 041  | Text-to-speech from documents                   | Generate audio from text       | Multi-language support          | TTS model size                |
| 042  | Mobile voice memo support                       | Mobile upload workflow         | Touch-friendly UI               | None                          |
| 043  | LLM-powered transcript insights                 | Send transcript to LLM service | Token limits, privacy           | API cost                      |
| 044  | Collaborative transcript editing                | Multi-user editing UI          | Real-time sync                  | Conflict resolution           |
| 045  | Automated meeting minutes                       | Compose summary + action items | Integration with calendars      | Summarization accuracy        |
| 046  | Cloud storage sync                              | Upload artifacts to cloud drives| OAuth + API quotas              | Reliability of sync           |
| 047  | Personalized speech models                      | Fine-tune recognition per user | Training data storage           | Model training cost           |
| 048  | Sign language video generation                  | Generate sign language videos  | Signer avatar quality           | Very heavy compute            |
