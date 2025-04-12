# 🧠 Whisper Transcriber — Core System Design Document

**Version:** 1.5  
**Audience:** Senior Developers  
**Author:** GPT (for Tony)  
**Last Updated:** 2025-04-12

---

## ✅ Project Goal

Build a local web-based transcription platform using OpenAI Whisper, designed to run in a Docker container inside a VMware-managed VM (eventually OVF). The system provides a browser-based interface for uploading audio, selecting settings, viewing live progress, and downloading transcripts — all without internet access.

This document reflects the **true, current implementation state**, based on direct analysis of all local files. Development follows milestone-based gating to ensure code and documentation stay aligned.

---

## 🔧 Project Milestones (History + Plan)

### ✅ Completed
- Repository initialized and under Git
- Initial design documents created
- `scripts/Start-WhisperSession.ps1` created and validates environment
- `app/transcribe.py` implemented with `openai-whisper` CLI
- `app/job_store.py` implemented with SQLite + full CRUD
- `app/main.py` implemented with Flask routes + subprocess job calling
- UI templates created: `base.html`, `index.html`, `jobs.html`, `status.html`

### 🚧 In Progress
- Live job log streaming (TBD)
- Download transcript button (not wired yet)

### 🔜 Upcoming
- Logging module (`log_utils.py`)
- Transcript viewer
- Containerization (Dockerfile, local wheels)
- Optional: authentication (`auth.py`), configuration centralization (`config.py`)

---

## 🔧 Architecture Overview

### 📁 Current Project Layout

```
whisper-transcriber/
├── app/
│   ├── transcribe.py       # ✅ Implemented
│   ├── job_store.py        # ✅ Implemented
│   ├── main.py             # ✅ Implemented
│   └── templates/          # ✅ UI Templates
│       ├── base.html
│       ├── index.html
│       ├── jobs.html
│       └── status.html
│
├── scripts/
│   └── Start-WhisperSession.ps1  # ✅ Implemented
│
├── setup_env.py           # ⚙️ Local dev utility script
├── README.md              # ✅ Present
├── .gitignore             # ✅ Present
├── Whisper_Design.md      # ✅ This file
└── data/jobs.db           # 🟡 Runtime artifact
```

---

## 🛠️ Core Functional Modules

### `transcribe.py` ✅
- CLI script to run OpenAI Whisper transcription
- Uses `whisper.load_model()` with runtime options
- Outputs JSON with timestamps
- Model, format, language selectable via args

### `job_store.py` ✅
- SQLite persistence for job records
- Functions: `add_job`, `get_job`, `get_all_jobs`, `update_job_status`
- Manages job schema and lifecycle

### `main.py` ✅
- Flask web server with routes:
  - `/`: Upload interface
  - `/submit`: Handles new jobs
  - `/jobs`: Lists all jobs
  - `/status/<job_id>`: Shows log + transcript link
- Launches transcription jobs via subprocess call to `transcribe.py`

### UI Templates ✅
- `base.html`: Shared layout
- `index.html`: Upload form
- `jobs.html`: Job history
- `status.html`: Job result/status view

---

## ⚙️ Support Scripts & Utilities

### `Start-WhisperSession.ps1` ✅
- Verifies git status, Python version, and installed packages
- Part of the milestone-based development flow
- Used to initialize each dev session

### `setup_env.py` ⚙️
- Local utility script (not required for container build)
- Wipes `.db`, log folders, and resets environment
- Used to prep fresh local development

---

## 🔢 Development Flow — What’s Next?

1. **Implement `log_utils.py`**
   - Provide per-job logging to disk
   - Integrate live tailing into `/status/<job_id>` view

2. **Wire download link for transcript**
   - Job completion view should link to final transcript file

3. **Containerize project**
   - Build `Dockerfile`
   - Use vendored wheels only
   - Include preloaded model weights

---

## 🎙️ Transcription Engine

- Engine: `openai-whisper` (Python binding)
- Default model: Set via CLI in `transcribe.py`
- Options: `tiny`, `base`, `small`, `medium`, `large`
- Model weights must be preloaded — offline-only container enforcement applies

---

## 📋 Development Policy

All development must follow gated milestones:

| Status | Meaning                            |
|--------|-------------------------------------|
| ✅     | Fully implemented and tested        |
| 🚧     | Being actively developed or staged  |
| 🔜     | Approved and next to be built       |
| ❌     | Do not begin until promoted         |

No module may be implemented if not approved in this document. Whisper GPT enforces this rule.

---

## 📦 Containerization Policy

- **No runtime internet** — model and dependencies must be preloaded
- All pip packages must be vendored as `.whl` files
- Audio uploads and transcripts go to bind-mountable volumes
- Build uses `python:3.10-slim` as base

---

## 📅 GPT Sync Log

- 2025-04-12: All modules confirmed implemented via source inspection
- 2025-04-12: Design doc reconciled with reality — Flask + UI promoted
- 2025-04-12: Roadmap updated; next milestone is logging + transcript UI
