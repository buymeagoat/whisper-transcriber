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
   # install Redux packages for global state and toasts

## Optional Environment Variables

`api/settings.py` reads the following environment variables at startup:

- `DB_URL` – SQLAlchemy database URL for the main database. Defaults to
  `postgresql+psycopg2://whisper:whisper@db:5432/whisper`.
- `DB` – path to a SQLite database file used mainly for tests. When set it
  overrides `DB_URL`.
- `VITE_API_HOST` – base URL used by the frontend to reach the API (defaults to `http://localhost:8000`).
- `VITE_DEFAULT_TRANSCRIPT_FORMAT` – default download format used by the web UI (defaults to `txt`).
- `LOG_LEVEL` – logging level for job/system logs (`DEBUG` by default).
- `LOG_TO_STDOUT` – set to `true` to also mirror logs to the console.
- `AUTH_USERNAME` and `AUTH_PASSWORD` – *(deprecated)* previous static credentials.
- `ALLOW_REGISTRATION` – enable the `/register` endpoint (defaults to `true`).
- `SECRET_KEY` – secret used to sign JWT tokens.
- `ACCESS_TOKEN_EXPIRE_MINUTES` – token lifetime in minutes.
- `MAX_CONCURRENT_JOBS` – number of worker threads when using the built-in job
  queue. Defaults to `2`. This value limits how many jobs can run in parallel
  so heavy workloads don't overwhelm the host.
- `JOB_QUEUE_BACKEND` – select the queue implementation. `thread` uses an
  internal worker pool while `broker` allows hooking into an external system
  like Celery.
- `STORAGE_BACKEND` – choose where uploads and transcripts are stored. The
  default `local` backend writes to the filesystem. Set `cloud` to use an
  S3 bucket via the `CloudStorage` backend.
- `LOCAL_STORAGE_DIR` – base directory used by the local backend. Defaults to
  the repository root when unset.
- `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` – credentials for accessing
  the bucket when using the cloud backend.
- `S3_BUCKET` – name of the bucket to store uploads and transcripts.
- `CELERY_BROKER_URL` and `CELERY_BACKEND_URL` – message broker and result
  backend used when `JOB_QUEUE_BACKEND` is set to `broker`.
- `CLEANUP_ENABLED` – toggle periodic cleanup of old transcripts. Defaults to
  `true`.
- `CLEANUP_DAYS` – how many days to keep transcripts when cleanup is enabled
  (defaults to `30`).
- `ENABLE_SERVER_CONTROL` – allow `/admin/shutdown` and `/admin/restart`
  endpoints (defaults to `false`).

Configuration values are provided by `api/settings.py` using Pydantic's
`BaseSettings`. An instance named `settings` is imported by the rest of the
application so environment variables are loaded only once.

## Running

Start the backend with `uvicorn`:

```bash
uvicorn api.main:app
```

When `JOB_QUEUE_BACKEND` is set to `broker` a Celery worker must also be
started:

```bash
python worker.py
```

To build the React frontend for production run:

```bash
cd frontend
npm run build
```

This outputs static files under `frontend/dist/`.
The Dockerfile copies this directory into `api/static/` so the React
application can be served with the backend.

### User Registration

Create an account by sending your desired username and password to `/register`.
Every account has a role of either `user` or `admin`. Registration always
creates regular users. Set `ALLOW_REGISTRATION=false` in production to disable
this endpoint. Obtain a token from `/token` using the same credentials. JWT
payloads now include the user role so clients can inspect their privileges.

### User Management

Admins can manage accounts via two endpoints:

- `GET /users` lists all users.
- `PUT /users/{id}` updates a user's role.

The React Settings page at `/settings` provides a simple interface for these actions.

## Metrics


The backend exposes Prometheus metrics at `/metrics`. This and all `/admin`
endpoints require an `admin` role. Authenticate with the JWT token obtained from
the `/token` endpoint and send it as `Authorization: Bearer <token>`.

Available metrics:

- `jobs_queued_total` – Counter of jobs submitted to the queue
- `jobs_in_progress` – Gauge tracking currently executing jobs
- `job_duration_seconds` – Histogram of job execution time

### Health & Version

Use `/health` to check server status. `/version` returns the current application version.

### Progress WebSocket

Connect to `/ws/progress/{job_id}` with the same JWT credentials as other
endpoints. The server now pushes real-time status messages so the UI updates
immediately with friendlier labels. Messages reflect the `queued`, `processing`,
`enriching` and final `completed` or `failed` states.

### Logs WebSocket

Open `/ws/logs/{job_id}` to stream log output for a running job. The frontend's log viewer subscribes to this socket and appends new lines as they arrive.
Admins can also connect to `/ws/logs/system` to monitor the access or system log in real time. The Admin page displays this feed in a built-in viewer.

### Example Job Response

Calls like `GET /jobs/{id}` now return Pydantic models. A typical response
resembles:

```json
{
  "id": "123abc",
  "original_filename": "audio.wav",
  "model": "base",
  "created_at": "2024-01-01T12:00:00Z",
  "updated": "2024-01-01T12:05:00Z",
  "status": "completed"
}
```

Timestamps returned by the API are in UTC (note the trailing `Z`).
The web UI converts them to your local timezone for display.

### Transcript Downloads

Use `/jobs/{id}/download` to retrieve the transcript. The optional `format`
parameter supports `srt` (default), `txt` for plain text, and `vtt` for WebVTT.

The React UI downloads transcripts in plain text by default using
`?format=txt`. This default can be overridden with the `VITE_DEFAULT_TRANSCRIPT_FORMAT`
build variable or by storing a `downloadFormat` value in `localStorage`.

To obtain all artifacts for a single job, call `/jobs/{id}/archive`. This returns
 a `.zip` file containing the transcript, metadata and job log.

### Admin Endpoints

The API offers several management routes that are restricted to users with the
`admin` role:

- `GET /admin/files` – list log, upload and transcript files on the server.
- `POST /admin/reset` – remove all jobs and related files.
- `GET /admin/download-all` – download every file as a single ZIP archive.
- `GET /admin/cleanup-config` – retrieve current cleanup settings.
- `POST /admin/cleanup-config` – update cleanup settings.
- `GET /admin/stats` – return CPU/memory usage along with completed job count, average processing time and queue length.
- `POST /admin/shutdown` – stop the server process.
- `POST /admin/restart` – restart the running server.

## Usage Notes

- Real-time job status messages appear in the UI via the progress WebSocket with
  friendlier labels for each state.
- Job logs stream live to the browser using `/ws/logs/{job_id}` on the log view page.
- The Admin page shows the system log via `/ws/logs/system`.
- Toast notifications show the result of actions across all pages.
- Admins can manage user roles from the Settings page.
- Cleanup options can be toggled and saved from the Admin page.
- `models/` exists locally only and is never stored in Git. It must contain the Whisper `.pt` files before building or running the app. Ensure the files are present before building the Docker image.
- `frontend/dist/` is not tracked by Git. Build it from the `frontend` directory with `npm run build` before any `docker build`.
- Uploaded files are stored under `uploads/` while transcripts and metadata are
  written to `transcripts/`. Per-job logs and the system log live in `logs/`.
When `STORAGE_BACKEND=cloud`, these folders act as a cache and transcript files
  are downloaded from S3 when accessed.

## Docker Usage

Docker builds expect a populated `models/` directory and the compiled
`frontend/dist/` folder. During the build the Python script
`validate_models_dir()` checks the `models/` directory so missing Whisper
models fail the build early. Both directories are ignored by Git so they must
be prepared manually before running `docker build`. Example:
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

The compose file mounts the `uploads`, `transcripts`, `logs` and `models`
directories so data and models persist between runs. It also configures
Celery with RabbitMQ by setting `JOB_QUEUE_BACKEND=broker`,
`CELERY_BROKER_URL` and `CELERY_BACKEND_URL` on the API and worker services.

Start everything with:

```bash
docker compose up --build api worker broker db
```

The worker container runs `celery -A api.services.celery_app worker` to process
jobs from RabbitMQ. Once running, access the API at `http://localhost:8000`.

## Testing

Install the development requirements and run the test suite with coverage:

```bash
pip install -r requirements-dev.txt
coverage run -m pytest
coverage report
```


## Contributing

Run `black .` before committing changes. When adding features or changing configuration, update both `docs/design_scope.md` and `README.md` so the documentation stays consistent.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
