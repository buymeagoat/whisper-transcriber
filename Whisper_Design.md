# Whisper Transcriber Design Doc

## 📒 Project Overview

Whisper Transcriber is a professional-grade web application for managing audio/video transcription tasks using OpenAI's Whisper models.

The system allows users to:
- Upload audio/video files
- Select model size and language variant (multilingual or English-only)
- Track active transcription jobs
- View and download completed transcriptions as clean TXT files
- Persist completed job records into a SQLite database (`jobs.db`) to survive restarts

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
    jobs.db               # SQLite database to store job records
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
- [x] **Move completed jobs into `jobs.db` SQLite database**
- [x] **Past Jobs listing (dynamic from database)**
- [x] **Download TXT transcript**
- [x] **TXT-only output from `transcribe.py` (no JSON)**
- [x] **Basic professional dark-themed UI**

### Pending Work (🔄 In Progress)
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
- Database-backed completed job persistence now implemented using `jobs.db`.

---

## 🚀 Next Steps

| Priority | Task |
|:--------|:-----|
| 📈 | Enhance active job progress indicators |
| 🛋️ | Implement multi-file uploads (optional) |
| 🛢️ | Containerize app for easier deployment |
| 📑 | Update and polish final documentation |


---

# End of Updated Whisper_Design.md

