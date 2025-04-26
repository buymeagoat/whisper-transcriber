# Whisper Transcriber — Design Document

## 🛠 Project Overview
Whisper Transcriber is a local-first, privacy-focused platform for transcribing audio files using OpenAI's Whisper models. The project emphasizes simplicity, local processing, and minimal external dependencies.

## 📦 Project Structure

```
/whisper-transcriber/
  app/
    app.py
    templates/
  data/
    jobs.db
  logs/
  models/
  transcripts/
  uploads/
  paths.py
  transcribe.py
  setup_env.py
  Whisper_Design.md
  README.md
```

## 🧩 Key Components

- `app/app.py`: Flask app handling uploads, job tracking, and downloads.
- `paths.py`: Centralized module for all filesystem path constants.
- `transcribe.py`: Transcription engine script using Whisper.
- `jobs.db`: SQLite database for tracking job states.
- `uploads/`: Folder for incoming audio files.
- `transcripts/`: Folder for output transcripts.

## 🔥 Core Features

- Web interface for uploading and tracking transcription jobs.
- Background threading for transcription processing.
- Centralized path management through `paths.py`.
- Local-only, privacy-respecting design.
- Modular code structure for future expansion (e.g., Docker, offline mode).

## 🏃 Running the Web Application Locally

From the project root (`/whisper-transcriber`), run:

```bash
py -m app.app
```

This will launch the Flask server with correct module paths.

### Why use `-m app.app`?

Running with `-m` ensures Python treats `/app` as a module, allowing clean imports (like `from paths import ...`) without needing hacky sys.path changes.

## 🔮 Future Enhancements

- Add transcript download button after processing.
- Full test and validation of `transcribe.py` with real audio.
- Docker container for offline deployment.
- Improved active jobs UI.
- Full unit testing coverage.

## ✅ Current Progress

- Web interface fully working (upload, active jobs, past jobs, download transcript)
- Background threading for transcription
- TXT-only output from `transcribe.py`
- `jobs.db` tracking all job statuses (Queued → Running → Completed)
- Flask app cleaned up and functional
- Centralized path management with `paths.py`
- Whisper_Design.md updated to reflect all changes

## 📋 Special Notes

- No hardcoded folder or database paths inside scripts.
- Always import from `paths.py`.
- Always launch app from the project root using `py -m app.app`.
- Keep Whisper_Design.md and README.md updated with any architecture changes.
