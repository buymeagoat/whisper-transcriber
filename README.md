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
   - API Documentation: http://localhost:8001/docs

## Testing

The API includes deterministic smoke tests that exercise authentication, file uploads, the health endpoint, and job queue
integration. Run the full suite with coverage locally using:

```bash
pytest
```

Pytest is configured (see `pytest.ini`) to fail when coverage for the API and tests drops below 25%. The CI workflow runs the
same command on every push and pull request, so new changes must keep the smoke tests and coverage budget green.

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
- `ADMIN_METRICS_TOKEN` – token for secured admin metrics endpoint

### Secret provisioning and rotation

1. **Provision secrets in a vault** – Store all runtime secrets in your cloud provider's secret manager (AWS Secrets Manager, HashiCorp Vault, etc.) and scope access to the deployment service account.
2. **Inject secrets at runtime** – Configure your orchestrator (Docker Swarm, Kubernetes, ECS) to mount the vault values as environment variables before the container entrypoint runs. Avoid baking secrets into images or `.env` files in source control.
3. **Rotate regularly** – Rotate `SECRET_KEY` and `JWT_SECRET_KEY` together at least quarterly; rotate database and Redis credentials according to your infrastructure policy and immediately revoke old credentials.
4. **Bootstrap administrator safely** – Generate `ADMIN_BOOTSTRAP_PASSWORD` just-in-time, use it once to create a permanent admin, then trigger rotation to invalidate the bootstrap credential.
5. **Verify during deploys** – The Docker entrypoint and production startup scripts now fail fast when required secrets are missing or use placeholder values. Monitor deployment logs to confirm validation before rolling traffic.

## Production Deployment

The application runs as three Docker containers:
- **app** - FastAPI backend + React frontend (port 8001)
- **worker** - Celery worker for transcription tasks
- **redis** - Task queue and cache

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