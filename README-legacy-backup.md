# Whisper Transcriber

> **Streamlined, mobile-first transcription service built for home servers.**
> **For detailed setup, see [docs/streamlined/SETUP_GUIDE.md](docs/streamlined/SETUP_GUIDE.md).**

Modern self-hosted transcription service with a **FastAPI backend** and **React PWA frontend**. Upload audio files and get transcripts instantly with a beautiful, mobile-optimized interface.

**✨ Key Features:**
- 📱 **Mobile-first PWA** with offline capabilities
- 🎯 **Drag-and-drop uploads** with real-time progress
- 🔄 **Background processing** with Celery workers
- 🗃️ **SQLite database** for simplicity
- 🐳 **Docker Compose** deployment

## Quick Start

### Prerequisites
- **Docker & Docker Compose**
- **Whisper model files** in `models/` directory

### Installation
```bash
# 1. Clone repository
git clone https://github.com/buymeagoat/whisper-transcriber.git
cd whisper-transcriber

# 2. Download Whisper models (required)
# Place base.pt, small.pt, medium.pt, large-v3.pt, tiny.pt in models/

# 3. Start with Docker Compose
docker-compose up -d

# 4. Access the application
# http://localhost:8000
```

The application uses **SQLite** for data storage and **Redis** for task queue management.
## Environment Variables

Key configuration options for the streamlined application:

```bash
# Core settings  
REDIS_URL=redis://localhost:6379/0           # Redis connection
DATABASE_URL=sqlite:///app/data/app.db       # SQLite database path
WHISPER_MODEL_DIR=/app/models                # Model directory

# Optional settings
CELERY_CONCURRENCY=2                         # Worker threads (match CPU cores)  
MAX_FILE_SIZE_MB=100                         # Upload limit
ALLOWED_AUDIO_FORMATS=mp3,wav,m4a,flac     # Supported formats
```

Copy `config/.env.example` to `.env` and customize as needed.
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
- `WHISPER_TIMEOUT_SECONDS` – maximum seconds to wait for Whisper before marking the job failed (0 disables timeout).
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
logs before launching the API. Increase `BROKER_CONNECT_ATTEMPTS` if the API
exits before the Celery worker is ready.

When `JOB_QUEUE_BACKEND` is set to `broker` a Celery worker must also be
started:

```bash
python api/worker.py
```

## Example Usage

### Register and Authenticate
```bash
curl -X POST -d 'username=user&password=secret' http://localhost:8000/register
curl -X POST -d 'username=user&password=secret' http://localhost:8000/token
```
Use the returned JWT token as `Authorization: Bearer <token>` for subsequent requests.

### Submit a Job
```bash
curl -F 'file=@audio.wav' http://localhost:8000/jobs
```

### Check Status
```bash
curl http://localhost:8000/jobs/<id>
```
For real-time updates, connect to `/ws/progress/<id>`.

### Download Transcript
```bash
curl -OJ http://localhost:8000/jobs/<id>/download?format=txt
```
### User Registration

Create an account by sending your desired username and password to `/register`.
Every account has a role of either `user` or `admin`. Registration always
creates regular users. Set `ALLOW_REGISTRATION=false` in production to disable
this endpoint. Obtain a token from `/token` using the same credentials. JWT
payloads now include the user role so clients can inspect their privileges.

On first startup, the application creates an admin account using the
`AUTH_USERNAME` and `AUTH_PASSWORD` environment variables. Logging in with
these credentials returns a token with `must_change_password=true`. Call
`/change-password` with the new password and the token to update it before
continuing.

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

`/health` now verifies the database connection by running a simple query. It returns
`{"status": "ok"}` when the check succeeds or `{"status": "db_error"}` with details
and a 500 status code if the query fails. `/version` returns the current
application version.

### Progress WebSocket

Connect to `/ws/progress/{job_id}` with the same JWT credentials as other
endpoints. The server now pushes real-time status messages so the UI updates
immediately with friendlier labels. Messages reflect the `queued`, `processing`,
`enriching` and final `completed` or `failed` states.

### Logs WebSocket

Open `/ws/logs/{job_id}` to stream log output for a running job. The frontend's log viewer subscribes to this socket and appends new lines as they arrive.
Admins can also connect to `/ws/logs/system` to monitor the access or system log in real time. The Admin page displays this feed in a built-in viewer.

Retrieving log files via `/log/{job_id}`, `/logs/access` and `/logs/{filename}` now requires a valid token.

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
- The worker container's health check uses `pgrep` to ensure a Celery process is running and now runs every 5 minutes.
- The Completed Jobs page provides a search box that filters results using the
  `search` query parameter on `/jobs`.
- The Transcript Viewer page includes a search field to highlight text and can
  optionally display only matching lines.
- Clicking the "Generate Insights" button on the Transcript Viewer sends the
  transcript to an LLM via `POST /jobs/{id}/analyze` and shows the returned
  summary, keywords, detected language and sentiment score.
- Cleanup options can be toggled and saved from the Admin page.
- `MODEL_DIR` points to the directory that holds the Whisper `.pt` files. The default is `models/`, ignored by Git. **This directory must contain `base.pt`, `small.pt`, `medium.pt`, `large-v3.pt` and `tiny.pt` before you build or start the server. Builds will fail if any file is missing.**
- `frontend/dist/` is generated by running `npm run build` inside the `frontend` directory.
- Uploaded files are stored under `uploads/` while transcripts and metadata are
  written to `transcripts/`. Per-job logs and the system log live in `logs/`.
When `STORAGE_BACKEND=cloud`, these folders act as a cache and transcript files
  are downloaded from S3 when accessed.

## Docker Usage

Docker builds require the compiled frontend assets in `frontend/dist/` and the Whisper model files under `models/`. Run `npm run build` or a helper script before invoking `docker build`. The `validate_models_dir()` script checks the models directory so missing files halt the build. **Ensure that `models/` contains `base.pt`, `small.pt`, `medium.pt`, `large-v3.pt` and `tiny.pt` before invoking `docker build`.** Both directories are ignored by Git and must exist before running `docker build`.

### Downloading Whisper Model Files

Obtain the pretrained weights from the [OpenAI Whisper release](https://github.com/openai/whisper/releases) or the [Hugging Face mirror](https://huggingface.co/openai/whisper-large-v3). Place `base.pt`, `small.pt`, `medium.pt`, `large-v3.pt` and `tiny.pt` in `models/` before building the image.

Example:
Build the image with a secret key (using BuildKit secrets is preferred):
```bash
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
printf "%s" "$SECRET_KEY" > secret_key.txt
docker build --secret id=secret_key,src=secret_key.txt -t whisper-app .
rm secret_key.txt
```
If your Docker installation does not support `--secret`, pass the key via build
argument instead:
```bash
docker build --build-arg SECRET_KEY=$SECRET_KEY -t whisper-app .
```
Docker must reach `registry-1.docker.io` during this step. If `docker build`
fails with errors like `failed to resolve source metadata` or `lookup
http.docker.internal ... i/o timeout`, your network is blocking access to the
Docker Hub registry. Check any proxy or firewall configuration and ensure the
host can pull images before retrying the build.
`docker compose build` does not accept the `--network=host` flag, so avoid using
it with Compose services. If you use a prebuilt image, mount the models
directory at runtime.

Run the container with the application directories mounted so that
uploads, transcripts and logs persist on the host. Set `VITE_API_HOST` to
the URL where the backend is reachable. Ensure `DB_URL` points to your
PostgreSQL instance; the compose file defaults to the `db` service
(using the `postgres:15-alpine` image):

```bash
docker run -p 8000:8000 \
  -e VITE_API_HOST=http://localhost:8000 \
  -e SECRET_KEY=<your key> \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/transcripts:/app/transcripts \
  -v $(pwd)/logs:/app/logs \
  -e LOG_LEVEL=DEBUG \
  -e LOG_TO_STDOUT=true \
  whisper-app
```

Generate `SECRET_KEY` with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Alternatively copy `.env.example` to `.env` and replace `CHANGE_ME` with a unique value before launching the container.

Setting `LOG_TO_STDOUT=true` and `LOG_LEVEL=DEBUG` surfaces detailed logs, which
helps diagnose bootstrapping failures when running inside Docker.

The compose file configures the `api` and `worker` services with `restart: on-failure`
so they automatically restart if either container exits unexpectedly.

## Docker Compose

A `docker-compose.yml` is included to start the API together with the
PostgreSQL and RabbitMQ services required by the default configuration. The
compose file now relies on service health checks so the API and worker wait for
the database and broker to become available. The `db` service runs PostgreSQL
for the API while RabbitMQ provides a broker for Celery when using the `broker`
job queue backend.

Prepare `models/` with `base.pt`, `small.pt`, `medium.pt`, `large-v3.pt` and `tiny.pt` before running compose.

Ensure `.env` exists with a valid `SECRET_KEY`. Copy `.env.example` to `.env`
and replace `CHANGE_ME` with your key. Include valid database credentials or a
`DB_URL` override so the containers can connect to PostgreSQL.
When building with Docker Compose, write the key to a temporary file and pass it
using Docker's BuildKit secrets feature (recommended):
```bash
printf "%s" "$SECRET_KEY" > secret_key.txt
docker compose build --secret id=secret_key,src=secret_key.txt api worker
rm secret_key.txt
```
If `docker compose build` does not support `--secret`, use a build argument
instead:
```bash
docker compose build --build-arg SECRET_KEY=$SECRET_KEY api worker
```

Build and start all services with:

```bash
docker compose up --build
```

The compose file mounts the `uploads`, `transcripts`, `logs` and `models`
directories so data and models persist between runs. These directories will be
created automatically inside the containers and ownership fixed to UID `1000`
by the entrypoint script, so no manual `chown` step is required. The compose
file defines a `db` service
using the `postgres:15-alpine` image and sets `DB_URL` on the API and worker so
they connect to it. Because port `5432` is published you can connect from the
host with `psql -h localhost -p 5432 -U whisper`. It also configures Celery with
RabbitMQ by setting `JOB_QUEUE_BACKEND=broker`,
`CELERY_BROKER_URL` and `CELERY_BACKEND_URL` on the API and worker services.

The broker service loads additional settings from `rabbitmq.conf` mounted at
`/etc/rabbitmq/rabbitmq.conf`. This configuration enables collection of
management metrics and other deprecated features required by Celery:

```
deprecated_features.permit.management_metrics_collection = true
deprecated_features.permit.transient_nonexcl_queues = true
deprecated_features.permit.global_qos = true
```

Start everything with:

```bash
docker compose up --build api worker broker db
```

If you edit `docker-compose.yml`, restart the stack so the changes take effect:

```bash
docker compose restart
```

If startup fails, rerun with `LOG_LEVEL=DEBUG` and `LOG_TO_STDOUT=true` to see
the container logs in the console.

## Contributing

Run `black .` before committing changes. When adding features or changing configuration, update both `docs/design_scope.md`, `docs/future_updates.md`, and `README.md` so the documentation stays consistent.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
