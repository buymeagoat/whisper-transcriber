# 📚 Whisper Transcriber — Architecture Design

---

## 📂 Folder Structure

/whisper-transcriber  
├── app/  
│   ├── app.py  
│   ├── templates/  
│   │   ├── base.html  
│   │   ├── home.html  
│   │   ├── new-transcription.html  
│   │   ├── active-jobs.html  
│   │   ├── past-jobs.html  
├── data/  
│   ├── (jobs.db dynamically created)  
├── logs/  
├── models/  
├── transcripts/  
├── uploads/  
├── scripts/  
│   ├── migrate_db.py  
│   ├── inspect_db.py  
├── paths.py  
├── README.md  
├── Whisper_Design.md  

> **Note:**  
> - `/data/jobs.db` is dynamically created if missing at runtime (not Git-tracked).  
> - `/uploads`, `/logs`, and `/transcripts` folders are required and are auto-created if absent.

---

## 🛢️ Database Schema (`jobs` Table)

| Column Name       | Type                | Purpose                                               |
|:------------------|:--------------------|:------------------------------------------------------|
| `job_id`           | INTEGER PRIMARY KEY | Unique identifier (auto-incremented)                  |
| `file_name`        | TEXT                | Original uploaded file name                           |
| `status`           | TEXT                | Current job status (`Queued`, `Running`, `Completed`, `Failed`) |
| `model`            | TEXT                | Whisper model size selected                           |
| `created`          | TIMESTAMP           | Timestamp when the job was created (default `CURRENT_TIMESTAMP`) |
| `duration_seconds` | REAL                | Duration of the audio file in seconds (optional)      |
| `language_detected`| TEXT                | Auto-detected language (optional)                     |
| `error_message`    | TEXT                | Error message if job fails (optional)                 |
| `completed_at`     | TIMESTAMP           | Timestamp when job completed (optional)               |

> **Schema Notes:**  
> - `init_db()` inside `app.py` creates the `jobs` table if it doesn't exist.  
> - `scripts/migrate_db.py` can be used to update existing databases to include newer fields.

---

## 🔄 Application Flow Overview

1. **User uploads** an audio or video file via `/new-transcription`.
2. **Job is created** in `jobs.db` with `status = Queued`.
3. **Background thread** starts transcription using `transcribe.py`.
4. **Job status updates** (`Running`, `Completed`, or `Failed`) in database.
5. **Results displayed** on `/active-jobs` and `/past-jobs`.
6. **Transcript available** for download after job completion.

---

## 📢 Current Stability Status

✅ Flask routes functional and error-handled  
✅ Database schema future-proofed for additional metadata  
✅ Frontend templates fully synchronized with backend data structures  
✅ Migration tooling and inspection tooling available  
✅ Professional absolute path management enforced via `paths.py`

---

## 🎯 Next Steps (Optional Enhancements)

- Add download link for completed transcripts
- Improve UI (progress bars, better timestamp formatting)
- Dockerize app for easier deployment
- Improve word-by-word timestamp display (post-transcription)
