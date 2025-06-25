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

## API Overview
- **Job management**: `POST /jobs` to upload, `GET /jobs` and `GET /jobs/{id}` to query, `DELETE /jobs/{id}` to remove, `POST /jobs/{id}/restart` to rerun, and `/jobs/{id}/download` to fetch the transcript. `GET /metadata/{id}` returns generated metadata.
- **Admin actions** under `/admin` allow listing and deleting files, downloading all artifacts, resetting the system, and retrieving basic stats.
- **Logging endpoints** expose job logs and the access log. If the access log does not exist, `/logs/access` returns a `404` with an empty body. Static files under `/uploads`, `/transcripts`, and `/static` are served directly.

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
Start a New Job button after upload
Replace default favicon
Show Docker stats in Admin (`/admin/stats`)
Web-based file manager for logs/uploads/transcripts (`/admin/files`)
Zip download of all data (`/admin/download-all`)

### Upcoming Ideas

<!-- Codex: Keep table cells padded to uniform column widths when updating. -->

| Rank | Feature Idea                                    | Reasoning                      | Considerations                  | Roadblocks                    |
| ---- | ----------------------------------------------- | ------------------------------ | ------------------------------- | ----------------------------- |
| 000  | Expose `/metrics` endpoint for monitoring       | Simple Prometheus integration  | Keep endpoint secured           | None                          |
| 001  | Add `/health` and `/version` endpoints          | Just return status data        | Decide output format            | None                          |
| 002  | Local-time timestamps instead of UTC            | Convert timestamps on display  | Timezone handling               | None                          |
| 003  | Download transcripts as `.txt`                  | Plain text export from SRT     | Maintain timestamp accuracy     | None                          |
| 004  | Download job archive (.zip)                     | Zip existing logs and results  | Avoid large file memory use     | None                          |
| 005  | Support `.vtt` transcript export                | Convert from SRT to VTT        | Extra dependency for conversion | None                          |
| 006  | Provide CLI wrapper for non-UI usage            | Wrapper script around API calls| Package distribution            | None                          |
| 007  | Improve status messaging in UI                  | Better frontend labels         | Localization, UX tweaks         | None                          |
| 008  | Job runtime display (live & final)              | Track job start and end times  | Store runtime data              | None                          |
| 009  | Admin panel health checks and job cleanup       | Add checks and cleanup hooks   | Permission checks               | None                          |
| 010  | Queue limit or concurrency throttle             | Throttle worker count          | Configurable limits             | None                          |
| 011  | Docker Compose setup                            | Provide sample compose file    | Keep dev/prod parity            | None                          |
| 012  | Dashboard KPIs for throughput                   | Show totals and averages       | Pull metrics from DB            | None                          |
| 013  | Role-based authentication                       | Add user roles table           | Password storage, security      | User management complexity    |
| 014  | Settings page to customize default model        | UI for selecting models        | Persist user prefs              | None                          |
| 015  | Allow multiple files per upload with validation | Adjust upload handler          | File size and concurrency       | None                          |
| 016  | Web-based log viewer                            | Simple log tail view           | Log file rotation               | Large logs                    |
| 017  | Sortable and searchable job lists               | Add filters on table views     | DB query optimization           | None                          |
| 018  | Status toasts for admin actions                 | Display toast on success/failure| Frontend state management       | None                          |
| 019  | Playback or text toggle for completed jobs      | Switch between audio and text  | Media player integration        | None                          |
| 020  | Use `updated_at` for job sorting/pagination     | Modify queries                 | Add index                       | None                          |
| 021  | Enhance CLI orchestrate.py with watch mode      | Poll API in loop               | Handle auth tokens              | None                          |
| 022  | Heartbeat table and `/heartbeat` endpoint       | Record worker heartbeats       | Extra DB writes                 | None                          |
| 023  | Kill (cancel) a running job                     | Send termination signal        | Handle partial output           | Process management            |
| 024  | Stop / Restart server from Admin                | Admin commands to stop and start| Risk of accidental shutdown     | Requires elevated permissions |
| 025  | Shell access via web UI                         | Web terminal component         | Security and sandboxing         | Major security risk           |
| 026  | Resume jobs after crash or cancel               | Persist intermediate state     | Robust job recovery             | Complex state handling        |
| 027  | Stream logs to UI via WebSocket                 | Push log lines live            | Scalability of sockets          | None                          |
| 028  | UI progress bars with word-level timestamps     | Parse SRT positions            | Frequent UI updates             | None                          |
| 029  | Auto-delete old transcripts after 30 days       | Background cleanup task        | Configurable retention          | None                          |
| 030  | Workflow automation hooks                       | Fire webhook on job completion | Configurable URLs               | Security of hooks             |
| 031  | Audio format conversion                         | Use ffmpeg for re-encoding     | Manage codecs                   | None                          |
| 032  | Audio cleanup utilities                         | Noise reduction pipeline       | CPU usage                       | External libs                 |
| 033  | Integration with meeting platforms              | OAuth with Zoom/Meet APIs      | API rate limits                 | Authentication complexity     |
| 034  | Searchable transcript archive                   | Full-text search index         | Storage footprint               | Search engine setup           |
| 035  | Speaker diarization support                     | Use speaker detection models   | Model accuracy                  | Heavy processing              |
| 036  | Summarization and keyword extraction            | NLP summarizer models          | Prompt quality                  | Compute load                  |
| 037  | Automatic language translation                  | Translate final text           | Choose translation service      | API cost                      |
| 038  | AI-powered sentiment analysis                   | Run sentiment model on segments| Language coverage               | Accuracy                      |
| 039  | Live streaming transcription                    | Transcribe streaming audio     | Buffer management               | Real-time latency             |
| 040  | Voice cloning for playback                      | Synthesize corrected speech    | Ethical concerns                | Requires heavy models         |
| 041  | Comprehensive audio toolbox                     | Combine many tools in UI       | Complexity of options           | Maintenance burden            |
| 042  | Text-to-speech from documents                   | Generate audio from text       | Multi-language support          | TTS model size                |
| 043  | Mobile voice memo support                       | Mobile upload workflow         | Touch-friendly UI               | None                          |
| 044  | LLM-powered transcript insights                 | Send transcript to LLM service | Token limits, privacy           | API cost                      |
| 045  | Collaborative transcript editing                | Multi-user editing UI          | Real-time sync                  | Conflict resolution           |
| 046  | Automated meeting minutes                       | Compose summary + action items | Integration with calendars      | Summarization accuracy        |
| 047  | Cloud storage sync                              | Upload artifacts to cloud drives| OAuth + API quotas              | Reliability of sync           |
| 048  | Personalized speech models                      | Fine-tune recognition per user | Training data storage           | Model training cost           |
| 049  | Sign language video generation                  | Generate sign language videos  | Signer avatar quality           | Very heavy compute            |
