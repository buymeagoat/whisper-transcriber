# Whisper Transcriber

> **For architecture, Docker build details and script internals, see [docs/design_scope.md](docs/design_scope.md).**
> **For repository standards, automation, and governance, see [docs/OPERATING_BLUEPRINT.md](docs/OPERATING_BLUEPRINT.md).**

Self-hosted transcription service with a FastAPI backend and a React frontend. It wraps the OpenAI Whisper CLI so you can upload audio, monitor progress and retrieve transcripts.

All Docker builds now use `scripts/whisper_build.sh`. Previous helper scripts were removed.<!-- # Codex: build entrypoint clarified -->

For a step-by-step setup guide, see [docs/help.md](docs/help.md).

## Repository Governance & Automation

This repository follows a Copilot-centric, automation-first model. All changes must:
- Adhere to the standards in [docs/OPERATING_BLUEPRINT.md](docs/OPERATING_BLUEPRINT.md)
- Update the changelog and per-change logs in `/logs/`
- Use the PR template and CI/CD gates for all merges
- Store build and change logs for historical analysis

## Requirements & Installation

For prerequisites and installation steps, follow the instructions in
[docs/help.md](docs/help.md). The guide covers Python and system
dependencies as well as optional Docker usage. Node.js 18 is required to build
the frontend. Install the React dependencies with:

```bash
cd frontend && npm install
```

To build offline, prime a cache directory and run `npm ci --cache <path>` before
invoking `npm run build`.
## Optional Environment Variables

`api/settings.py` reads the following environment variables at startup. `SECRET_KEY` has no default and must be set. When using Docker Compose, variables in a `.env` file at the project root are automatically loaded. Create this file by copying `.env.example` and replacing the placeholder with a unique value.

- `DB_URL` – SQLAlchemy connection string for the required PostgreSQL database in the form
  `postgresql+psycopg2://user:password@host:port/database`. The default
  `postgresql+psycopg2://whisper:whisper@db:5432/whisper` works with
  `docker-compose.yml` because it references the `db` service. Override it for
  a local instance, for example
  `DB_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/whisper`.
- `VITE_API_HOST` – base URL used by the frontend to reach the API. Leave blank to use the site's origin and set a URL when the API is hosted remotely.
- `PORT` – TCP port used by the Uvicorn server (defaults to `8000`).
- `VITE_DEFAULT_TRANSCRIPT_FORMAT` – default download format used by the web UI (defaults to `txt`).
- `LOG_LEVEL` – logging level for job/system logs (`DEBUG` by default).
- `LOG_FORMAT` – set to `json` for structured logs or `plain` for text (defaults
  to `plain`).
- `LOG_TO_STDOUT` – set to `true` to also mirror logs to the console.
- `LOG_MAX_BYTES` – maximum size of each log file before rotation (defaults to
  `10000000`).
- `LOG_BACKUP_COUNT` – how many rotated log files to keep (defaults to `3`).
- `MAX_UPLOAD_SIZE` – maximum allowed upload size in bytes (defaults to
  `2147483648`).
- `DB_CONNECT_ATTEMPTS` – how many times to retry connecting to the database on
  startup (defaults to `10`).
- `BROKER_CONNECT_ATTEMPTS` – how many times to retry pinging the Celery broker
  on startup (defaults to `20`). Increase this value if the API exits before the
  worker is ready.
- `BROKER_PING_TIMEOUT` – how many seconds the worker entrypoint waits for
  RabbitMQ to respond before exiting (defaults to `60`).
- `API_HEALTH_TIMEOUT` – how many seconds to wait for the API container to
  become healthy (defaults to `300`).
- `AUTH_USERNAME` and `AUTH_PASSWORD` – *(deprecated)* previous static credentials.
- `ALLOW_REGISTRATION` – enable the `/register` endpoint (defaults to `true`).
 - `SECRET_KEY` – **required** secret used to sign JWT tokens. The application
   exits on startup when this variable is missing.
  Generate one with:

  ```bash
  # generate a 64-character key
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
  Set `SECRET_KEY` to this value before starting the API or worker containers.
  The key signs JWT tokens and should be kept private.
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
python worker.py
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

The application ships with a built-in `admin` account using the password
`admin`. Logging in with these credentials returns a token with
`must_change_password=true`. Call `/change-password` with the new password and
the token to update it before continuing.

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

## Codex Analyst GPT Workflow

Repository introspection and patch creation are handled entirely by **Codex Analyst GPT (CAG)**. When contributors request changes, CAG retrieves file lists and contents through prompt-driven commands and returns the necessary diffs inside the conversation. Approved patches are applied automatically and the full diff is saved under `docs/patch_logs/` for reference. Manual ZIP uploads are no longer required—patch logs accumulate in that directory and serve as the canonical history.

## Contributing

Run `black .` before committing changes. When adding features or changing configuration, update both `docs/design_scope.md`, `docs/future_updates.md`, and `README.md` so the documentation stays consistent.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
