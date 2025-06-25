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

`api/settings.py` reads the following environment variables at startup:

- `DB_URL` – SQLAlchemy database URL for the main database. Defaults to
  `postgresql+psycopg2://whisper:whisper@db:5432/whisper`.
- `DB` – path to a SQLite database file used mainly for tests. When set it
  overrides `DB_URL`.
- `VITE_API_HOST` – base URL used by the frontend to reach the API (defaults to `http://localhost:8000`).
- `LOG_LEVEL` – logging level for job/system logs (`DEBUG` by default).
- `LOG_TO_STDOUT` – set to `true` to also mirror logs to the console.
- `METRICS_TOKEN` – optional bearer token required to access `/metrics`.
- `AUTH_USERNAME` and `AUTH_PASSWORD` – credentials for obtaining JWT tokens (defaults `admin`/`admin`).
- `SECRET_KEY` – secret used to sign JWT tokens.
- `ACCESS_TOKEN_EXPIRE_MINUTES` – token lifetime in minutes.
- `MAX_CONCURRENT_JOBS` – number of worker threads when using the built-in job
  queue. Defaults to `2`.
- `JOB_QUEUE_BACKEND` – select the queue implementation. `thread` uses an
  internal worker pool while `broker` allows hooking into an external system
  like Celery. Only `thread` is implemented by default.
- `STORAGE_BACKEND` – choose where uploads and transcripts are stored. The
  default `local` backend writes to the filesystem. A placeholder `cloud`
  backend can be added for remote buckets.

Configuration values are provided by `api/settings.py` using Pydantic's
`BaseSettings`. An instance named `settings` is imported by the rest of the
application so environment variables are loaded only once.

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

The backend exposes Prometheus metrics at `/metrics`. Authenticate with the JWT
token obtained from the `/token` endpoint and send it as `Authorization: Bearer
<token>`.

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


