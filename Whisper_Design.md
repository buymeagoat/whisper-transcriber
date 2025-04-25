# Whisper Transcriber - Project Design Document

---

## 📆 Project Overview

**Whisper Transcriber** is a local-first, privacy-respecting audio transcription platform.

Features:
- Offline-first transcription using OpenAI Whisper or compatible models
- Minimal web UI for uploading audio, viewing, and downloading transcripts
- Local SQLite job tracking (no cloud dependency)
- Lightweight CLI bootstrap for developer sessions

---

## 📊 Project Layout

```
whisper-transcriber/
├── app/
│   ├── transcribe.py          # CLI transcription tool
│   ├── job_store.py           # SQLite job tracking
│   ├── main.py                # Flask routes for UI
│   └── templates/             # HTML templates for UI
│       ├── base.html
│       ├── index.html
│       ├── jobs.html
│       └── status.html
│
├── scripts/
│   └── start-whispersession.ps1  # Developer environment session starter
│
├── uploads/                 # Uploaded audio files (runtime only)
├── transcripts/              # Output transcript files (.json, .txt)
├── logs/                     # Runtime logs and debug logs
├── data/
│   └── jobs.db                # SQLite database file (created at runtime)
│
├── setup_env.py              # Developer environment reset tool
├── requirements.txt          # Python dependencies
├── README.md                 # Project overview and usage
├── Whisper_Design.md         # This design document
├── .gitignore                # Ignores whisper-env, uploads, logs, transcripts
└── whisper-env/              # (local virtual environment, ignored by Git)
```

---

## 🔢 Local Development Environment

- Create a local Python virtual environment:

```bash
python -m venv whisper-env
```

- Activate the virtual environment:

```bash
# Windows
.\whisper-env\Scripts\activate

# macOS/Linux
source whisper-env/bin/activate
```

- Install dependencies:

```bash
pip install -r requirements.txt
```

- `whisper-env/` is **ignored from GitHub** via `.gitignore` and should always remain local.

---

## 🔄 Development Workflow

1. **Start Developer Session:**
   ```bash
   .\scripts\start-whispersession.ps1
   ```
2. **Upload or place audio files into** `uploads/`
3. **Run CLI transcription:**
   ```bash
   python app/transcribe.py --input uploads/yourfile.wav
   ```
4. **View transcripts in** `transcripts/`
5. **(Optional) Start Flask UI:**
   ```bash
   python app/main.py
   ```

---

## 📅 Milestone Status

| Component                 | Status   |
|----------------------------|----------|
| Developer Session Script   | ✅ Completed |
| CLI Transcription (`transcribe.py`) | ✅ Validated |
| Database Schema (`job_store.py`) | ✅ Completed |
| Flask App Skeleton (`main.py`) | ✅ Completed |
| HTML Templates (`templates/`) | ✅ Created |
| Transcript Download UI | ⏳ Upcoming |
| Job Logs UI (`log_utils.py`) | ⏳ Upcoming |
| Dockerfile / Offline Packaging | ⏳ Upcoming |

---

## 🚀 Next Steps

- Implement **transcript download feature** in UI
- Add **basic log visualization** (job status and errors)
- Build **Docker container** for full offline deployability
- Create lightweight **unit tests** for CLI and Flask endpoints

---

# 👋 End of Document

