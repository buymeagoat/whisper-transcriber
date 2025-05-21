# Whisper Transcriber Design Scope (OpenAI Whisper Version)

---

## 📚 Summary

This project enables **local-first, file-based audio transcription** using OpenAI Whisper. Audio is uploaded via an HTTP API and processed immediately with the OpenAI Whisper model. Outputs are written to disk.

Target users are developers or researchers running long-form transcription jobs in Ubuntu WSL2 environments.

---

## 🛠️ Architecture

* **API**: FastAPI

  * Endpoint: `POST /jobs`
  * Accepts: `multipart/form-data`
  * Saves files to `uploads/`

* **Processing**: Python wrapper around `openai-whisper`

  * Model: `tiny` by default
  * CLI-compatible and import-friendly
  * Invoked synchronously within FastAPI handler

* **Storage**:

  * Inputs: `uploads/`
  * Outputs: `outputs/{job_id}.txt` (text) + `{job_id}.json` (metadata)

* **Logging**:

  * Uses `logging` module, INFO level or more verbose
  * Logs major steps: receipt, model start, segment count, completion

---

## ✅ Required Folders

* `/uploads` - where user-submitted files are stored
* `/outputs` - final transcriptions and metadata
* `/api/main.py` - entrypoint for the web handler

---

## 🚀 Deployment

* Environment: Ubuntu WSL2
* Python: 3.10+
* Start server: `uvicorn api.main:app --reload`
* Test client: Swagger UI at `localhost:8000/docs`

---

## 📚 Job Format

**Request**:

* POST `/jobs`
* `multipart/form-data`

  * `file`: `.m4a`, `.mp3`, `.wav`, etc.

**Response**:

```json
{
  "job_id": "uuid-string"
}
```

---

## 🔧 Output Artifacts

* `outputs/{job_id}.txt`: plain text
* `outputs/{job_id}.json`: metadata

```json
{
  "job_id": "abc-123",
  "input_file": "uploads/abc-123_example.m4a",
  "output_file": "outputs/abc-123.txt",
  "language": "en",
  "duration_sec": 123.45,
  "segment_count": 37,
  "started_utc": "...",
  "finished_utc": "..."
}
```

---

## 🚫 Out of Scope (for now)

* No Celery or Redis background jobs
* No UI beyond `/docs`
* No real-time streaming or file chunking

---

## ⚖️ Licensing / Model

* Using `openai-whisper`, MIT License
* Models downloaded on first use unless cached

---
