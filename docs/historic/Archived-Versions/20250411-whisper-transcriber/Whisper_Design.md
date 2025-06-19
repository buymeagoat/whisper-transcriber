# 🧠 Whisper Transcriber — Core System Design Document

**Version:** 1.0  
**Audience:** Senior Developers  
**Author:** GPT (for Tony)  
**Last Updated:** 2025-04-09

---

## ✅ Project Goal

Build a local web-based transcription platform using OpenAI Whisper, designed to run in a Docker container inside a VMware-managed VM (eventually OVF). The system provides a browser-based interface for uploading audio, selecting settings, viewing live progress, and downloading transcripts — all without internet access.

---

## 🔧 Critical Architecture Overview

### 📁 Directory Structure (Container Layout)

```
whisper_transcriber/
├── app/
│   ├── main.py             # Flask web server
│   ├── transcribe.py       # Whisper logic, cooperative logging
│   ├── job_store.py        # SQLite-based job persistence
│   ├── log_utils.py        # Central logging utilities
│   ├── auth.py             # Simple authentication system
│   └── config.py           # Configuration for paths, cleanup, user roles
│
├── templates/              # Jinja2 templates
│   ├── index.html
│   ├── status.html
│   ├── jobs.html
│   └── admin.html
│
├── static/                 # Vanilla JS + CSS
│   ├── style.css
│   └── progress.js
│
├── uploads/                # Uploaded audio files
├── transcripts/            # Transcription outputs
├── logs/                   # Per-job logs
├── data/                   # SQLite DB + users
│   └── jobs.db
├── Dockerfile
├── requirements.txt
└── entrypoint.py
```

---

## 🧱 Core Functional Modules

### `main.py`
- Flask routes and UI entrypoints
- Starts background transcription jobs in threads
- Reads/writes to `job_store.py` for state
- Cooperatively cancels jobs using a shared `CANCELLED` dict

### `transcribe.py`
- Loads Whisper model (based on user selection)
- Supports:
  - Transcription vs Translation
  - Segmenting (start/end)
  - Timestamped vs plain output
  - Initial prompt
- Writes `.txt`, `.srt`, or `.vtt` to `transcripts/`
- Logs output to `logs/<job_id>.log`

### `job_store.py`
- Wraps SQLite DB `jobs.db`
- Defines schema for:

```sql
CREATE TABLE jobs (
  job_id TEXT PRIMARY KEY,
  file_name TEXT,
  original_name TEXT,
  created_at TEXT,
  status TEXT,
  model TEXT,
  format TEXT,
  timestamps BOOLEAN,
  task TEXT,
  language TEXT,
  initial_prompt TEXT,
  start_time INTEGER,
  end_time INTEGER,
  log_path TEXT,
  output_path TEXT
);
```

### `auth.py`
- Basic login and session tracking
- Admin user defined at setup
- Admin can add additional users via `/admin/users`

---

## 🧭 Job Lifecycle

1. Upload page `/`
   - User uploads audio and selects settings
2. Server analyzes file via `/analyze_audio`
   - Detects duration and language
3. User submits via `/upload`
4. Flask starts thread to run `transcribe.py`
5. Job is visible at `/status/<job_id>`
   - Progress shown live
   - Log streamed from `logs/<id>.log`
6. When complete:
   - Transcript is written
   - Status is marked as “Done”
7. User can download via `/download/<job_id>`

---

## 🔐 Authentication & Permissions

- Users must log in to access `/jobs`, `/upload`, or `/admin`
- Admin account defined in config or SQLite
- Admins can:
  - Restart backend
  - Delete jobs
  - Add/remove users
  - Trigger cleanup of old logs
- Future option: IP restriction for admin functions

---

## 📝 Logging Architecture

| Type | Path | Description |
|------|------|-------------|
| Per-job logs | `logs/<job_id>.log` | Segment-by-segment log output (shown in UI) |
| App logs     | `app_log.txt`       | Flask errors, job state, startup, auth events |
| Critical vs Non-critical | Stored on separate partitions if needed |

### 🧹 Log Cleanup Strategy
- Manual by default
- Configurable option to remove logs older than `X` days
- Executed via UI or cron-style backend

---

## 📦 Containerization

### Base Image:
```dockerfile
FROM python:3.10-slim
```

- Whisper and dependencies installed from local `.whl` files
- FFmpeg included
- No internet access required at runtime
- Mounted volumes:
  - `/uploads`
  - `/logs`
  - `/transcripts`
  - `/data`

---

## 🛠️ System Administration Features

- Admin-only dashboard (`/admin`)
- View system status (active jobs, thread count)
- View full application logs (`app_log.txt`)
- Restart Flask application via web button (container-level command)
  - Admin clicks "Restart Backend"
  - Triggers a subprocess or container-level restart (supervised context)
  - Optional: show countdown and auto-refresh UI
- Delete stale jobs (manually or via cleanup rule)

---

## 📈 Planned Enhancements (not critical path)

| Feature | Notes |
|---------|-------|
| Job retry/resume | Support restarts after crash or container reboot |
| WebSocket log streaming | Instead of polling |
| Job archive download | .zip of transcript + log |
| Role-based auth | Future tiered permission levels |
| `/metrics` endpoint | For external system monitoring |
| Job retention policy | Auto-delete old transcripts after 30 days |

---

## ✅ Final Notes

This design reflects a production-grade architecture with a clean interface, robust backend, and future-focused extensibility. It enables development to proceed in modular phases, with clear separation between user workflows, job handling, and system administration.
