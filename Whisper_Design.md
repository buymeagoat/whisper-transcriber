# 🧠 Whisper Transcriber — Core System Design Document

**Version:** 1.6  
**Audience:** Senior Developers  
**Author:** GPT (for Tony)  
**Last Updated:** 2025-04-12

---

## ✅ Project Goal

Build a local web-based transcription platform using OpenAI Whisper, designed to run in a Docker container inside a VMware-managed VM (eventually OVF). The system provides a browser-based interface for uploading audio, selecting settings, viewing live progress, and downloading transcripts — all without internet access.

This document reflects only **tested, implemented work**. If a module exists but has not been functionally verified, it is listed as 🔜 Upcoming.

---

## 🔧 Project Milestones (Verified)

### ✅ Completed
- Repository initialized and under Git
- `scripts/Start-WhisperSession.ps1` created and validates environment
- `app/job_store.py` implemented with SQLite + full CRUD
- `app/main.py` implemented with Flask routes + subprocess job calling
- UI templates created: `base.html`, `index.html`, `jobs.html`, `status.html`

### 🔜 Upcoming
- Validate `transcribe.py` with real audio (currently untested)
- Add transcript download functionality
- Add `log_utils.py` for streaming logs
- Begin Docker containerization

---

## 🔧 Architecture Overview

### 📁 Project Layout

```
whisper-transcriber/
├── app/
│   ├── transcribe.py       # 🔜 Exists, needs validation
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
├── setup_env.py           # ⚙️ Dev-only reset script
├── README.md              # ✅ Present
├── .gitignore             # ✅ Present
├── Whisper_Design.md      # ✅ This file
└── data/jobs.db           # 🟡 Runtime artifact
```

---

## 🛠️ Core Modules

### `job_store.py` ✅
- SQLite-backed persistence for all jobs
- CRUD lifecycle management
- Ready for use in Flask, CLI, or async

### `main.py` ✅
- Flask routes: `/`, `/submit`, `/jobs`, `/status/<job_id>`
- Handles file uploads and job metadata
- Submits jobs via subprocess call to `transcribe.py`

### `transcribe.py` 🔜
- Python script using `openai-whisper`
- Supports CLI args: model, language, output format
- Script exists but has **not been tested with real audio**
- Validation is a required milestone

### UI Templates ✅
- Bootstrap layout and job views implemented
- Output and status displayed in browser

---

## 🔢 What’s Next (Milestone Plan)

1. **Validate Transcription Engine**
   - Run real audio through `transcribe.py`
   - Inspect output JSON and error handling
   - Document behavior and adjust if needed

2. **Implement transcript download UI**
   - Add Flask route to serve finished transcript files

3. **Build `log_utils.py`**
   - Write per-job logs to disk
   - Integrate with job view page

4. **Begin Docker containerization**
   - Offline support required
   - All packages vendored
   - Model weights bundled in image

---

## 🎙️ Transcription Engine

- Engine: `openai-whisper`
- Script: `app/transcribe.py`
- Models: `tiny`, `base`, `small`, etc.
- Must run offline — models must be preloaded

---

## 📋 Development Policy

| Status | Meaning                            |
|--------|-------------------------------------|
| ✅     | Implemented and verified            |
| 🔜     | Exists but unvalidated              |
| 🚧     | Actively in progress                |
| ❌     | Planned only — do not build yet     |

No module may be treated as “Complete” unless verified by test or usage.  
Whisper GPT is configured to enforce this rule during development sessions.

---

## 📦 Containerization Policy

- No internet access allowed at runtime
- Pip wheels must be vendored
- All model weights preloaded into build
- Volumes: `/uploads`, `/logs`, `/transcripts`, `/data`

---

## 📅 GPT Sync Log

- 2025-04-12: `transcribe.py` demoted from ✅ to 🔜 due to lack of testing
- 2025-04-12: GPT logic now halts development if design doc is out of sync
- 2025-04-12: Roadmap shifted to reflect true milestone order
