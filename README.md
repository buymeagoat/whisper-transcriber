# Whisper Transcriber

This project provides a FastAPI backend with a React frontend for running OpenAI Whisper transcription jobs.

## Requirements & Installation

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Install frontend dependencies from the `frontend` directory:
   ```bash
   cd frontend
   npm install
   ```

## Optional Environment Variables

- `DB` – path to the SQLite database file (defaults to `api/jobs.db`).
- `VITE_API_HOST` – base URL used by the frontend to reach the API (defaults to `http://localhost:8000`).
- `LOG_LEVEL` – logging level for job/system logs (`DEBUG` by default).
- `LOG_TO_STDOUT` – set to `true` to also mirror logs to the console.

## Running

Start the backend with `uvicorn`:

```bash
uvicorn api.main:app
```

To build the React frontend for production run:

```bash
cd frontend
npm run build
```

This outputs static files under `api/static/`.

## Usage Notes

- `models/` is intentionally excluded from version control. Populate it by running
  `./download_models.sh` or by providing a directory when building the Docker
  image via `--build-arg MODELS_DIR=/path/to/models`. The Docker build and
  application startup fail if this directory is missing or empty. The download
  script writes progress to `logs/model_download.log`.
- Uploaded files are stored under `uploads/` while transcripts and metadata are
  written to `transcripts/`. Per-job logs and the system log live in `logs/`.

