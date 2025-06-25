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
- `METRICS_TOKEN` – optional bearer token required to access `/metrics`.

All configuration values are parsed once in `api/config.py` and imported by the
rest of the application instead of calling `os.getenv` directly.

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

This outputs static files under `frontend/dist/`.
The Dockerfile copies this directory into `api/static/` so the React
application can be served with the backend.

## Metrics

The backend exposes Prometheus metrics at `/metrics`. When `METRICS_TOKEN` is
set, requests must include `Authorization: Bearer <token>`.

## Usage Notes

- `models/` exists locally only and is never stored in Git. It must contain the Whisper `.pt` files before building or running the app. Ensure the files are present before building the Docker image.
- `frontend/dist/` is not tracked by Git. Build it from the `frontend` directory with `npm run build` before any `docker build`.
- Uploaded files are stored under `uploads/` while transcripts and metadata are
  written to `transcripts/`. Per-job logs and the system log live in `logs/`.

## Docker Usage

Docker builds expect a populated `models/` directory and the compiled
`frontend/dist/` folder. Both directories are ignored by Git so they must be
prepared manually before running `docker build`. Example:
```bash
cd frontend
npm run build
cd ..
```
Build the image with:
```bash
docker build -t whisper-app .
```
If you use a prebuilt image, mount the models directory at runtime.

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

## Docker Compose

A `docker-compose.yml` is included to start the API together with example
PostgreSQL and RabbitMQ services. These additional services are placeholders for
future features but are not required today.

Prepare the models and build the frontend before running compose:

```bash
cd frontend
npm run build
cd ..
```

Build and start all services with:

```bash
docker compose up --build
```

The compose file mounts the `uploads`, `transcripts` and `logs` directories so
data persists between runs. Once running, access the API at
`http://localhost:8000`.


