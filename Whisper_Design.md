# Whisper Transcriber Design Doc

## 📒 Project Overview

Whisper Transcriber is a professional-grade web application for managing audio/video transcription tasks using OpenAI's Whisper models.

The system allows users to:
- Upload audio/video files
- Select model size and language variant (multilingual or English-only)
- Track active transcription jobs
- View and download completed transcriptions as clean TXT files

---

## 🔢 Folder Structure

```
/whisper-transcriber/
  app/
    app.py                # Flask app main file
    templates/
      base.html           # Base template
      home.html           # Main menu (New, Active, Past Jobs)
      new_transcription.html  # Upload new transcription job
      active_jobs.html    # View active jobs
      past_jobs.html      # View completed jobs
  models/                 # Local Whisper model .pt files
  uploads/                # Uploaded audio/video files
  transcripts/            # Output TXT transcripts
  logs/                   # Transcription logs (stdout/stderr)
  data/
    jobs.db               # SQLite database to store completed jobs
  transcribe.py            # Command-line script to run Whisper transcription
  setup_env.py             # (future) Script to rebuild environment from scratch
  Whisper_Design.md        # This design document
  README.md                # Project overview and instructions
```

---

## 📑 Key Features

### Current Features (✅ Completed)
- [x] **Web upload form** (new transcription)
- [x] **Active Jobs tracking**
- [x] **Background thread-based transcription**
- [x] **Move completed jobs out of Active Jobs**
- [x] **Past Jobs listing (dynamic)**
- [x] **Download TXT transcript**
- [x] **TXT-only output from `transcribe.py` (no JSON)**
- [x] **Basic professional dark-themed UI**

### Pending Work (🔄 In Progress)
- [ ] **Database persistence for completed jobs** (`jobs.db`) — survival across server restarts
- [ ] **Better active job progress display** (if desired)
- [ ] **File upload size and extension validation hardening**
- [ ] **Multi-file upload support (optional future feature)**
- [ ] **Docker containerization (optional)**


---

## 🛰 Transcription Engine

- **Whisper Local Models**: Models loaded from `/models/` folder if available.
- **Default Behavior**: TXT output saved into `/transcripts/`, logs into `/logs/`.
- **Model Choices Available**:
  - tiny / tiny.en
  - base / base.en
  - small / small.en
  - medium / medium.en
  - large

(Default recommended model = `small.en` for general-purpose transcription.)

---

## ✨ Known Differences from Original Plan
- `transcribe.py` was relocated from `/app/` to root for subprocess cleanliness.
- `.json` outputs were intentionally removed from transcriptions.
- Memory-based `completed_jobs` currently clears on server restart; persistence pending.

---

## 🚀 Next Steps

| Priority | Task |
|:--------|:-----|
| 🔗 | Implement SQLite persistence for Completed Jobs |
| 📈 | Upgrade Past Jobs view to show database entries |
| 🛋️ | Create migrations/setup for `jobs.db` if needed |
| 📑 | Polish README and usage instructions |


---

# End of Updated Whisper_Design.md

