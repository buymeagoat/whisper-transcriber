# Whisper Transcriber — MVP Scope and Preservation Design

## 🌟 Project Philosophy

The application will preserve all core features outlined in the original design, but emphasize a practical MVP version that can be shipped, tested, and used. The remainder of the system (e.g. restart jobs, multi-file upload, advanced user flow) is deferred but retained in documentation for future implementation.

---

## 🎡 MVP Core Goals

### User Interface (Basic User)

* Upload one audio file
* Select model (`tiny`, `base`, etc.)
* Submit job for processing
* See real-time, **accurate** job status:

  * `queued`, `processing`, `completed`, `stalled`
* Download timestamped transcript (`.srt`) on completion
* Delete a job and all associated files/records

### Admin View (Advanced Controls)

* Browse uploaded files, transcripts, logs
* Inspect all DB job entries
* Manually delete any job/data/log
* \[Future] Monitor performance / view system metrics

---

## 🔧 Architecture Overview

| Layer         | Technology             | Notes                               |
| ------------- | ---------------------- | ----------------------------------- |
| Frontend      | React                  | File upload, job dashboard          |
| Backend       | FastAPI                | REST endpoints, job orchestration   |
| Transcription | Whisper CLI/Python API | Spawned per job via subprocess      |
| DB            | SQLite                 | Alembic-managed schema, job history |
| Filesystem    | OS folders             | `uploads/`, `transcripts/`, `logs/` |

---

## 📊 MVP Data Model (Job Schema)

```python
{
  "id": str,
  "original_filename": str,
  "saved_filename": str,
  "model": str,
  "status": "queued" | "processing" | "completed" | "failed" | "stalled",
  "created_at": datetime,
  "updated_at": datetime,
  "transcript_path": Optional[str],
  "log_path": Optional[str]
}
```

---

## 🔍 API Endpoints (MVP)

| Method | Route                 | Description                   |
| ------ | --------------------- | ----------------------------- |
| POST   | `/jobs`               | Upload file + create job      |
| GET    | `/jobs/{id}`          | Poll job status               |
| GET    | `/jobs/{id}/download` | Download `.txt` transcript    |
| DELETE | `/jobs/{id}`          | Delete job + associated files |

---
## Application and Job Logging

To support debugging, auditing, and system introspection, the application must:

- Write a dedicated log file per job (`logs/<job_id>.log`)
- Include all major lifecycle events:
  - File upload and validation
  - Model selection
  - Subprocess launch and arguments
  - Transcription outputs (stdout/stderr summaries)
  - Metadata generation
  - Status transitions
  - Failures or exceptions
- Format each log line with timestamp, severity level, and job ID:
    2025-06-04 19:03:21 [INFO] [3c26b17fc68b4b248937359f8254a912] Whisper exited successfully
- Persist logs even if the app restarts, fails, or exits
- Ensure no failure condition is unlogged:
- All errors and exceptions must emit traceable log lines
- Silent failures are unacceptable
- Keep logs human-readable and compatible with tools like `grep`, `less`, or simple log viewers
- Provide access to logs by job ID (e.g., `GET /log/{job_id}` or via direct file access)

This ensures that all system behavior, including edge cases and failures, can be traced post hoc without guessing or reproducing.

---

## 🥹 What is Deferred (Preserved for Future)

| Feature                                   | Reason                              | Tracked as Future?  |
| ------------------------------------------| ------------------------------------| --------------------|
| Restart job                               | Not required for MVP                | ✅ Yes              |
| Batch/multi-file upload                   | Increases backend complexity        | ✅ Yes              |
| Subtitle generation                       | Output not required                 | ✅ Yes              |
| OAuth2 or JWT Auth                        | Not needed in MVP context           | ✅ Yes              |
| Vector DB or embeddings                   | Advanced NLP only                   | ✅ Yes              |
| Diarization                               | Complex ML add-on                   | ✅ Yes              |
| Full Admin Dashboard (graphs)             | More dev effort required            | ✅ Yes              |
| Audio playback for completed/failed jobs  | Improves admin UX and validation    | ✅ Yes              |
| Convert .srt to .txt for user-friendly download | Users expect .txt but need timestamps preserved | ✅ Yes |
---

## 🎓 MVP Completion Criteria
* Each job includes a generated metadata.json file containing duration, token count, and an abstract preview.
* A user can:

  * Upload file
  * Pick a model
  * Monitor progress (accurate)
  * Download transcript
  * Delete job
* An admin can:

  * Inspect DB entries
  * View logs/files
  * Remove old job artifacts
* Jobs persist through restarts
* Logs are saved per job
* Statuses reflect real progress

---

## 🔍 File + Folder Layout

```
whisper-transcriber/
├── api/
│   ├── main.py
│   ├── metadata_writer.py
│   ├── models.py
│   ├── errors.py
│   ├── jobs.db
├── orchestrate.py
├── logs/
├── uploads/
├── transcripts/
├── alembic.ini
├── pyproject.toml
├── requirements.txt
├── frontend/ (MVP version)
│   ├── src/
│   │   ├── UploadPage.jsx
│   │   ├── JobsPage.jsx
│   │   └── TranscriptPage.jsx
└── design_scope.md
```

---

## 🚀 Let's Build It

Next steps:

1. ✅ Validate this scope
2. 📈 Refactor `main.py` to match this behavior
3. 🤝 Finalize `test_integration.py` for upload-through-complete lifecycle
4. 🎨 Begin frontend wiring using this scope

---

All features not in MVP will remain in the repository and this scope document for return after launch.
