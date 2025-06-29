# Whisper Transcriber

This project provides a FastAPI backend with a React frontend for running OpenAI Whisper transcription jobs.

## Requirements & Installation

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Install system dependencies. `ffmpeg` (providing `ffprobe`) must be present
   for audio processing features. On Linux you can install it with:
   ```bash
   sudo apt-get install -y ffmpeg
   ```
3. Install frontend dependencies from the `frontend` directory. The build
   requires **Node.js 18** or newer:
   ```bash
cd frontend
  npm install
  ```
   # install Redux packages for global state and toasts
4. Install Celery if you plan to set `JOB_QUEUE_BACKEND=broker` or use Docker
   Compose:
   ```bash
   pip install celery
   ```

## Optional Environment Variables

`api/settings.py` reads the following environment variables at startup:

- `DB_URL` – SQLAlchemy connection string for the required PostgreSQL
  database. The default `postgresql+psycopg2://whisper:whisper@db:5432/whisper`
  points to the `db` service (running the `postgres:15-alpine` image) defined in
  `docker-compose.yml`.
- `VITE_API_HOST` – base URL used by the frontend to reach the API (defaults to `http://localhost:8000`).
- `VITE_DEFAULT_TRANSCRIPT_FORMAT` – default download format used by the web UI (defaults to `txt`).
- `LOG_LEVEL` – logging level for job/system logs (`DEBUG` by default).
- `LOG_TO_STDOUT` – set to `true` to also mirror logs to the console.
- `LOG_MAX_BYTES` – maximum size of each log file before rotation (defaults to
  `10000000`).
- `LOG_BACKUP_COUNT` – how many rotated log files to keep (defaults to `3`).
- `DB_CONNECT_ATTEMPTS` – how many times to retry connecting to the database on
  startup (defaults to `10`).
- `AUTH_USERNAME` and `AUTH_PASSWORD` – *(deprecated)* previous static credentials.
- `ALLOW_REGISTRATION` – enable the `/register` endpoint (defaults to `true`).
- `SECRET_KEY` – secret used to sign JWT tokens.
- `ACCESS_TOKEN_EXPIRE_MINUTES` – token lifetime in minutes.
- `MAX_CONCURRENT_JOBS` – number of worker threads when using the built-in job
  queue. Defaults to `2`. The value can also be changed at runtime via
  `/admin/concurrency` and limits how many jobs can run in parallel so heavy
  workloads don't overwhelm the host.
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
- `CLEANUP_INTERVAL_SECONDS` – how often the cleanup task runs
  (defaults to `86400`).
- `ENABLE_SERVER_CONTROL` – allow `/admin/shutdown` and `/admin/restart`
  endpoints (defaults to `false`).
- `TIMEZONE` – local timezone name used for log timestamps (defaults to `UTC`).
- `CORS_ORIGINS` – comma-separated list of origins allowed for CORS (defaults to `*`).
- `WHISPER_BIN` – path to the Whisper CLI executable (defaults to `whisper`).
- `WHISPER_LANGUAGE` – language code passed to Whisper (defaults to `en`).
- `MODEL_DIR` – directory containing Whisper model files (defaults to `models/`).
- `OPENAI_API_KEY` – API key enabling transcript analysis via OpenAI.
- `OPENAI_MODEL` – model name used when `OPENAI_API_KEY` is set (defaults to `gpt-3.5-turbo`).

Configuration values are provided by `api/settings.py` using
`pydantic_settings.BaseSettings`. An instance named `settings` is imported by the rest of the
application so environment variables are loaded only once.

## Running

Start the backend with `uvicorn`:

```bash
uvicorn api.main:app
```

PostgreSQL must be available. The default `DB_URL` targets the `db` service
(based on the `postgres:15-alpine` image) from `docker-compose.yml`.

If startup fails, set `LOG_LEVEL=DEBUG` and `LOG_TO_STDOUT=true` for verbose
logs before launching the API.

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

### User Settings

Authenticated users can store personal defaults.
- `GET /user/settings` – retrieve saved preferences.
- `POST /user/settings` – update preference values.
The upload page uses the returned `default_model` to choose the Whisper model automatically.

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

### Listing Jobs

`GET /jobs` now accepts optional `search` and `status` query parameters. The
`search` filter matches the job ID, original filename or transcript keywords
case-insensitively. The `status` value may include one or more pipe separated
states (e.g. `queued|processing`). A value of `failed` matches any failure
status. The Completed, Failed and Active Jobs pages use these parameters to
request only the relevant jobs from the backend.

### Transcript Downloads

Use `/jobs/{id}/download` to retrieve the transcript. The optional `format`
parameter supports `srt` (default), `txt` for plain text, and `vtt` for WebVTT.

The React UI downloads transcripts in plain text by default using
`?format=txt`. This default can be overridden with the `VITE_DEFAULT_TRANSCRIPT_FORMAT`
build variable or by storing a `downloadFormat` value in `localStorage`.

To obtain all artifacts for a single job, call `/jobs/{id}/archive`. This returns
 a `.zip` file containing the transcript, metadata and job log.

### Audio Editing

Send a file to `/edit` to perform basic operations on the clip. Provide optional
`trim_start` and `trim_end` values (seconds) to crop the audio and `volume` to
adjust loudness. The endpoint saves the modified file under `uploads/` and
returns the path to this new file.

Use `/convert` to change an uploaded clip to another format. Supply the file and
a `target_format` form field set to `mp3`, `m4a`, `wav` or `flac`. The endpoint
saves the re-encoded file under `uploads/` and returns its path.

### Admin Endpoints

- The API offers several management routes that are restricted to users with the
`admin` role:

- `GET /admin/files` – list top-level folders for logs, uploads and transcripts.
- `GET /admin/browse` – return the contents of a folder. Pass `folder` (`logs`,
  `uploads` or `transcripts`) and an optional `path` to drill down into
  subdirectories. The Admin page now features a file browser powered by this
  endpoint where files can be viewed, downloaded or deleted. The previous inline
  file lists have been removed.
- `POST /admin/reset` – remove all jobs and related files.
- `GET /admin/download-all` – download every file as a single ZIP archive.
- `GET /admin/download-app/{os}` – download a packaged binary for `windows` or `linux`.
- `GET /admin/cleanup-config` – retrieve current cleanup settings.
- `POST /admin/cleanup-config` – update cleanup settings.
- `GET /admin/concurrency` – show the current worker concurrency limit.
- `POST /admin/concurrency` – update the concurrency limit.
- `GET /admin/stats` – return CPU/memory usage along with completed job count, average processing time and queue length.
- `POST /admin/shutdown` – stop the server process.
- `POST /admin/restart` – restart the running server.

The Admin page provides a full file browser built on these endpoints. Choose a
folder and click directories to drill down. Each file entry includes buttons to
view, download or delete it. This replaces the old inline lists that previously
displayed all files at once.

## Usage Notes

- Real-time job status messages appear in the UI via the progress WebSocket with
  friendlier labels for each state.
- Job logs stream live to the browser using `/ws/logs/{job_id}` on the log view page.
- The Admin page shows the system log via `/ws/logs/system`.
- Toast notifications show the result of actions across all pages.
- Admins can manage user roles from the Settings page.
- A left-side navigation bar lists each section, including a **Download Desktop App** tab linking to `/download-app`.
- The Completed Jobs page provides a search box that filters results using the
  `search` query parameter on `/jobs`.
- The Transcript Viewer page includes a search field to highlight text and can
  optionally display only matching lines.
- Clicking the "Generate Insights" button on the Transcript Viewer sends the
  transcript to an LLM via `POST /jobs/{id}/analyze` and shows the returned
  summary and keywords.
- Cleanup options can be toggled and saved from the Admin page.
- `MODEL_DIR` points to the directory that holds the Whisper `.pt` files. The default is `models/`, ignored by Git. **This directory must contain `base.pt`, `small.pt`, `medium.pt`, `large-v3.pt` and `tiny.pt` before you build or start the server.**
- `frontend/dist/` is not tracked by Git. Build it from the `frontend` directory with `npm run build` before any `docker build`.
- Uploaded files are stored under `uploads/` while transcripts and metadata are
  written to `transcripts/`. Per-job logs and the system log live in `logs/`.
When `STORAGE_BACKEND=cloud`, these folders act as a cache and transcript files
  are downloaded from S3 when accessed.

## Building Packages

Helper scripts under `scripts/` produce distributable binaries:

```bash
scripts/build_windows_exe.sh  # creates dist/whisper-transcriber.exe
scripts/build_rpm.sh          # creates dist/whisper-transcriber.rpm
```

Admins can fetch these files from `/admin/download-app/{os}` by specifying
`windows` or `linux`.

## Docker Usage

Docker builds expect a populated directory containing the Whisper models specified by `MODEL_DIR` along with the compiled
`frontend/dist/` folder. During the build the Python script
`validate_models_dir()` checks this directory so missing Whisper
models fail the build early. **Ensure that `models/` contains `base.pt`, `small.pt`, `medium.pt`, `large-v3.pt` and `tiny.pt` before invoking `docker build`.** Both directories are ignored by Git so they must
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
uploads, transcripts and logs persist on the host. Set `VITE_API_HOST` to
the URL where the backend is reachable. Ensure `DB_URL` points to your
PostgreSQL instance; the compose file defaults to the `db` service
(using the `postgres:15-alpine` image):

```bash
docker run -p 8000:8000 \
  -e VITE_API_HOST=http://localhost:8000 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/transcripts:/app/transcripts \
  -v $(pwd)/logs:/app/logs \
  whisper-app
```

## Docker Compose

A `docker-compose.yml` is included to start the API together with the
PostgreSQL and RabbitMQ services required by the default configuration. The
`db` service runs PostgreSQL for the API while RabbitMQ provides a broker for
Celery when using the `broker` job queue backend.

Prepare `models/` with `base.pt`, `small.pt`, `medium.pt`, `large-v3.pt` and `tiny.pt` and build the frontend before running compose:

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
directories so data and models persist between runs. It defines a `db` service
using the `postgres:15-alpine` image and sets `DB_URL` on the API and worker so
they connect to it. It also configures
Celery with RabbitMQ by setting `JOB_QUEUE_BACKEND=broker`,
`CELERY_BROKER_URL` and `CELERY_BACKEND_URL` on the API and worker services.

Start everything with:

```bash
docker compose up --build api worker broker db
```

The worker container runs `celery -A api.services.celery_app worker` to process jobs from RabbitMQ.
An optional helper script `scripts/start_containers.sh` automates these steps. Run it from the repository root to build the frontend if needed and launch the compose stack in detached mode. Use `docker compose down` to stop all services.
Once running, access the API at `http://localhost:8000`.

## Testing

Install the development requirements and run the test suite with coverage. The
tests use `pytest-postgresql` to launch a temporary PostgreSQL instance:

```bash
pip install -r requirements-dev.txt
coverage run -m pytest
coverage report
```


## Contributing

Run `black .` before committing changes. When adding features or changing configuration, update both `docs/design_scope.md`, `docs/future_updates.md`, and `README.md` so the documentation stays consistent.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
