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

- `models/` will never be checked into Git. Ensure the five Whisper model files (tiny, base, small, medium and large) exist locally before building or running the application. Populate the folder with `./download_models.sh` or supply a populated directory when running `docker build --build-arg MODELS_DIR=/path/to/models`. If using a prebuilt container, mount the same directory at runtime. The build and application fail if this directory is missing or empty. The download script writes progress to `logs/model_download.log`.
- Uploaded files are stored under `uploads/` while transcripts and metadata are
  written to `transcripts/`. Per-job logs and the system log live in `logs/`.

## Docker Usage

Docker builds require `--build-arg MODELS_DIR=/path/to/models` pointing to the populated models directory. If you use a prebuilt image instead, mount the same directory at runtime.
```bash
docker build --build-arg MODELS_DIR=/path/to/models -t whisper-app .
# The build will fail if the models directory is empty. When running an image built elsewhere, mount the populated models directory with `-v /path/to/models:/app/models`.
```

Run the container with the application directories mounted so that
uploads, transcripts and logs persist on the host. The front end needs
`VITE_API_HOST` set to the URL where the backend is reachable:

```bash
docker run -p 8000:8000 \
  -e VITE_API_HOST=http://localhost:8000 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/transcripts:/app/transcripts \
  -v $(pwd)/logs:/app/logs \
  whisper-app
```

