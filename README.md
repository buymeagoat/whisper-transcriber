# Whisper Transcriber - Production

A production-ready audio transcription service using OpenAI Whisper.

## Quick Start

1. **Set up environment variables:**
   ```bash
   cp env.template .env
   # Edit .env with your production values
   ```

2. **Build and run with Docker:**
   ```bash
   docker-compose up --build
   ```

3. **Access the application:**
   - Web Interface: http://localhost:8001
   - Interactive OpenAPI docs: http://localhost:8001/docs
   - Prometheus metrics: http://localhost:8001/metrics/

## Testing

The API includes deterministic smoke tests that exercise authentication, file uploads, the health endpoint, Prometheus metrics,
and job queue integration. Run the full suite with coverage locally using:

```bash
pytest
```

Pytest is configured (see `pytest.ini`) to fail when coverage for the API and tests drops below 25%. The CI workflow runs the
same command on every push and pull request, so new changes must keep the smoke tests and coverage budget green.

Refer to [docs/api/routes.md](docs/api/routes.md) for endpoint-level usage examples and
[docs/traceability.md](docs/traceability.md) to see how the critical requirements map to tests and documentation.

## Continuous Integration and Branch Protection

The `ci` workflow located in `.github/workflows/ci.yml` runs linting (`flake8`), static type checks, security tooling (`bandit`
and `pip-audit`), the test suite, a Docker build, and Syft-powered CycloneDX SBOM generation on every push and pull request.
Both the container image tarball (`whisper-transcriber-image`) and generated SBOM (`sbom`) are uploaded as workflow artifacts
and exposed via the job outputs (`image-artifact-id`, `image-artifact-url`, `sbom-artifact-id`, `sbom-artifact-url`) for
downstream automation.

To keep `main` protected:

1. Navigate to **Settings → Branches → Branch protection rules**.
2. Add or edit the rule for `main` and enable **Require status checks to pass before merging**.
3. Select the `build` job from the `ci` workflow as a required status check.
4. Optionally enforce admins so every merge confirms the full pipeline remains green.

With branch protection in place, every pull request must complete the security and quality gates run by the workflow before it
can be merged.

## Deployment

Build the production image with the multi-stage Dockerfile and provide build metadata so the entrypoint validation passes:

```bash
docker build \
  --target production \
  --build-arg BUILD_VERSION=$(git describe --tags --always) \
  --build-arg BUILD_SHA=$(git rev-parse HEAD) \
  --build-arg BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ) \
  -t whisper-transcriber:latest .
```

The runtime container runs as a non-root user, exposes port 8001, and publishes a healthcheck at `/` via `scripts/healthcheck.sh`.
The entrypoint (`scripts/docker-entrypoint.sh`) validates the build metadata file (`/etc/whisper-build.info`), failing fast if it is missing and issuing a warning when placeholder values are detected so you know to rebuild with the expected Docker build arguments.

## Versioning

We follow [Semantic Versioning](https://semver.org/) and document our release workflow, tagging conventions, and rollback guidance in [docs/releases.md](docs/releases.md).

## Configuration

Required environment variables in `.env.production` (provision via a secrets manager):
- `SECRET_KEY` – 64+ character application signing key
- `JWT_SECRET_KEY` – dedicated JWT signing key
- `DATABASE_URL` – production database connection string
- `REDIS_URL` / `REDIS_PASSWORD` – Redis connection details
- `ADMIN_BOOTSTRAP_PASSWORD` – temporary administrator credential for first run
- `ADMIN_METRICS_TOKEN` – token for the `/admin/uploads/metrics` endpoint that reports chunked upload statistics

### Secret provisioning and rotation

1. **Provision secrets in a vault** – Store all runtime secrets in your cloud provider's secret manager (AWS Secrets Manager, HashiCorp Vault, etc.) and scope access to the deployment service account.
2. **Inject secrets at runtime** – Configure your orchestrator (Docker Swarm, Kubernetes, ECS) to mount the vault values as environment variables before the container entrypoint runs. Avoid baking secrets into images or `.env` files in source control.
3. **Rotate regularly** – Rotate `SECRET_KEY` and `JWT_SECRET_KEY` together at least quarterly; rotate database and Redis credentials according to your infrastructure policy and immediately revoke old credentials.
4. **Bootstrap administrator safely** – Generate `ADMIN_BOOTSTRAP_PASSWORD` just-in-time, use it once to create a permanent admin, then trigger rotation to invalidate the bootstrap credential.
5. **Verify during deploys** – The Docker entrypoint and production startup scripts now fail fast when required secrets are missing or use placeholder values. Monitor deployment logs to confirm validation before rolling traffic.

## Production Deployment

Production images now fail fast unless the following environment variables are provided with non-placeholder values:

- `SECRET_KEY` – application signing key used for session data.
- `JWT_SECRET_KEY` – signing key for API tokens.
- `DATABASE_URL` – SQLAlchemy DSN for the primary database.
- `REDIS_URL` – Redis connection string (also used for the Celery broker when set).
- `REDIS_PASSWORD` – password supplied to the Redis container/instance.
- `ADMIN_BOOTSTRAP_PASSWORD` – temporary administrator credential used once at bootstrap.

To prepare a secure deployment:

1. Copy the template to a local secrets file and keep it out of version control:
   ```bash
   cp env.template .env
   ```
2. Generate the signing keys (rotate them in your secrets manager on a schedule):
   ```bash
   openssl rand -hex 64
   openssl rand -hex 64
   ```
   Use two different outputs to populate `SECRET_KEY` and `JWT_SECRET_KEY` in `.env`.
3. Provision `DATABASE_URL`, `REDIS_URL`, and `ADMIN_BOOTSTRAP_PASSWORD` using your secrets manager. For local
   experiments you can set `DATABASE_URL=sqlite:////app/data/app.db`,
   `REDIS_PASSWORD=local-redis-password`, and
   `REDIS_URL=redis://:local-redis-password@redis:6379/0`.
4. Store the populated `.env` in your orchestrator's secret store and inject it as environment variables. The
   Docker Compose file expects these keys via `.env` and refuses to start without them.

Transcription jobs are executed through a **Celery-backed distributed task queue** defined in
`api/services/job_queue.py` and `api/worker.py`. The Celery worker processes transcription jobs
asynchronously, allowing the API to remain responsive while handling long-running transcription tasks.
Redis serves as both the message broker and result backend. The worker is defined in `worker.py` at
the repository root and executes tasks from `api.services.app_worker.py`, which performs the actual
Whisper model inference.

The provided Docker Compose file starts the following containers:
- **app** – FastAPI backend + React frontend (port 8001) that submits jobs to the Celery queue.
- **worker** – Celery worker that processes transcription jobs asynchronously.
- **redis** – Message broker and result backend for Celery, also used for caching.

If you deploy to another orchestrator, carry across the same environment variables and mount points used by the
Compose definition and ensure secrets are injected through a secure mechanism (vault, secret manager, etc.).

## Observability

- **Structured logging** – All FastAPI services use the JSON logger provided by `api/utils/logger.py`. Each entry
  includes the timestamp, severity, request ID (when available), caller metadata, and any additional context supplied
  via the logging API.
- **Metrics** – The `/metrics/` endpoint exposes RED/USE style Prometheus metrics by default without additional
  authentication. Network layer controls should therefore guard access to the endpoint in production environments.

## API Usage

Upload audio files via the web interface or API:
```bash
curl -X POST -F "file=@audio.wav" http://localhost:8001/upload
```

## Supported Audio Formats

- WAV, MP3, M4A, FLAC
- Maximum file size: 100MB

## Models

Available Whisper models:
- tiny, small, medium, large, large-v3

Default model: small (best balance of speed/accuracy)