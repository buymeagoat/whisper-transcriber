# Whisper Transcriber — Application Functionality and Design Scope

## Project Summary

A browser-based, containerized audio transcription platform running locally (no cloud dependency) using Whisper models. Initially designed around OpenAI Whisper, currently transitioning to Faster-Whisper for local inference performance.

---

## Core Features (Confirmed)

### Input

- Upload audio files via UI (`.wav`, `.mp3`, `.m4a`, `.ogg`, etc.)
- Upload endpoint: `POST /jobs` (FastAPI)
- Files stored in `uploads/`

### Processing

- Background job queue using Celery
- Redis as message broker
- WhisperModel loads on task start and performs segment-wise transcription
- Segment metadata collected during transcription

### Output

- Transcript: plain text file → `outputs/<job_id>.txt`
- Metadata: JSON file → segment count, model, timestamps
- Planned: `.srt` and `.vtt` subtitle exports

### UI (Planned)

- Swagger UI at `/docs`
- Flask + Jinja2 HTML UI
  - Drag-and-drop file upload
  - Model selection dropdown
  - Language override (optional)
  - Output format checkboxes: `.txt`, `.srt`, `.vtt`
  - Timestamp toggle
  - Segment range input (start/end)
  - Job progress view (logs, segment preview)
  - Download transcripts
  - Retry/cancel jobs
  - Admin dashboard (restart server, delete jobs, view logs)
  - Authentication & role-based access

### Models

- Default: `faster-whisper-large-v3`
- Stored in `./models/faster-whisper-large-v3/`
- Local-only loading (`local_files_only=True`)
- All models preloaded in `/models/` for offline use
- Future: allow user model selection (base, small, medium, large)

---

## Job Lifecycle

1. Upload audio file
2. UUID assigned, saved to `uploads/`
3. Celery worker picks up job
4. Transcription runs
5. Output written to `outputs/` as `.txt` and `.json`
6. Log stored in `logs/<job_id>.log`
7. Status view updates
8. User downloads transcript

---

## Admin Interface (`/admin`) [Planned]

### System Status

- Redis: up/down
- Celery workers: connected/count
- Disk usage: uploads, outputs, logs
- System uptime, CPU, and memory

### Job Management

- Job history (status, user, model, lang, date)
- View logs (tail/full)
- Retry/cancel jobs
- Delete data (input, transcript, metadata, logs)

### Model Management

- List all models in `/models/`
- View model disk usage
- Set default model

### Log Management

- Search logs in `logs/*.log`
- Download ZIP of logs
- Delete selected logs

### File Cleanup Tools

- Show oldest files
- Batch delete jobs/transcripts/logs
- Wipe failed jobs
- Full workspace reset (with confirmation)

### User Access Control

- Simple SQLite-based `users` table
- Admin/user roles
- Add/remove users
- Audit logs (actions, logins)

---

## Admin & Developer Tooling

- Per-job logs: `logs/<job_id>.log`
- Manual cleanup tools:
  - Remove uploads, logs, outputs
  - Re-download inputs
  - Re-fetch logs
  - Clear log directory
- Server restart from UI
- `jobs.db` for user/job tracking (planned)
- Transcript ZIP download
- System health indicators

---

## Future Features

| Feature                      | Status         |
|-----------------------------|----------------|
| Live log streaming          | Not started    |
| Admin dashboard             | Not started    |
| ZIP archive download        | Not started    |
| Auth (admin/user)           | Not started    |
| Docker Compose deployment   | Not started    |
| VM packaging / OVF export   | Not started    |
| Language auto-detection     | ✅ Done         |
| Resume/retry support        | Planned        |
| Model selector in UI        | Not started    |
| Prompt text seeding         | Not started    |
| SRT/VTT subtitle export     | Not started    |

---

## Logging Expectations

- Metadata: duration, language, segments
- Preview log output (first 3 segments)
- Per-job logs: `logs/<job_id>.log`
- Job errors print with job ID
- Separate log file per Celery session
- Logs exposed to admin UI

---

## User Configuration Options (Planned)

- Model selection (dropdown)
- Language override
- Format selection (`.txt`, `.srt`, `.vtt`)
- Timestamp toggle
- Prompt seeding
- Segment start/end
- Retry job toggle

---

## Authentication (Planned)

- User auth via SQLite `users` table
- Admin-only functions:
  - View logs
  - Restart backend
  - Delete jobs
  - Clean expired files
  - View job metadata

---

## Architecture Notes

- Runs in WSL, Docker, or VM
- Stack: Redis + Celery + Uvicorn + FastAPI + Flask
- Fallback to CPU if GPU unavailable
- `/uploads`, `/outputs`, `/logs` mounted in Docker
- Central config file for model and path management

---

## Testing Status

- ✅ FastAPI `/jobs` endpoint works
- ✅ Celery jobs process audio
- ✅ Transcripts and metadata written
- ✅ stdout logs created
- ✅ Output folders operational
- ❌ UI needs implementation
- ❌ Real-time feedback not yet wired

---

## Open Questions

- ✅ Flask chosen for UI (not React)
- ✅ WebSocket preferred over polling
- ❓ MVP file format requirements (TBD)
- ✅ Resume/retry supported
- ✅ Preload all models
- ✅ Manual cleanup preferred (no auto-purge)

---

## References

- `Whisper_Design.md`: UI and system architecture
- `gpt_config_notes.md`: GPT co-dev patterns
- Session logs: o3, 4o iterative planning
- `Transcription Methods Overview`: multi-model comparison
