# Whisper Transcriber

An audio transcription service powered by OpenAI Whisper.

## Quick Start (local runtime)

1. Copy the environment template and populate values:
   ```bash
   cp env.template .env
   # edit .env with development secrets
   ```
2. Create a virtual environment and install backend dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
3. Install frontend dependencies and build assets (served by the API):
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```
4. Start the Celery worker in a separate terminal so transcription jobs are processed:
   ```bash
   source .venv/bin/activate
   celery -A api.worker.celery_app worker --loglevel=info
   ```
5. Run the API server:
   ```bash
   source .venv/bin/activate
   uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload
   ```

### Access endpoints
- Web interface: http://localhost:8001
- OpenAPI docs: http://localhost:8001/docs
- Prometheus metrics: http://localhost:8001/metrics/

### Authentication defaults
- Administrator username: `admin`
- Administrator email: `admin@admin.admin`
- Administrator password: `super-secret-password-!123` (configurable via `ADMIN_BOOTSTRAP_PASSWORD`)
- The application intentionally runs in single-user mode. Additional accounts remain a future enhancement even though the database schema still supports them.

Use the **Settings → Change Password** panel in the web UI to rotate the admin credential after the first login.

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

The `ci` workflow located in `.github/workflows/ci.yml` runs linting (`flake8`), static type checks, security tooling
(`bandit` and `pip-audit`), and the test suite on every push and pull request.

To keep `main` protected:

1. Navigate to **Settings → Branches → Branch protection rules**.
2. Add or edit the rule for `main` and enable **Require status checks to pass before merging**.
3. Select the `build` job from the `ci` workflow as a required status check.
4. Optionally enforce admins so every merge confirms the full pipeline remains green.

With branch protection in place, every pull request must complete the security and quality gates run by the workflow before it
can be merged.

## Deployment

Package managers such as `pipx`, `uv`, or systemd services can host the application. At a minimum:

1. Provision the secrets listed below via environment variables or a secrets manager.
2. Build the frontend bundle (`npm run build`) and ensure `api/static/` contains the generated assets.
3. Install Python dependencies in a virtual environment and run `uvicorn api.main:app` behind your preferred process manager.

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
- `METRICS_TOKEN` – shared secret presented via the `X-Metrics-Token` header when scraping `/metrics/`

### Secret provisioning and rotation

1. **Provision secrets in a vault** – Store runtime secrets in a secure secret manager and scope access to the deployment service account.
2. **Inject secrets at runtime** – Configure your process manager or host environment to export the secret values before the application starts. Avoid checking secrets into source control.
3. **Rotate regularly** – Rotate `SECRET_KEY` and `JWT_SECRET_KEY` together at least quarterly; rotate database and Redis credentials according to your infrastructure policy and revoke old credentials immediately.
4. **Bootstrap administrator safely** – Generate `ADMIN_BOOTSTRAP_PASSWORD` just-in-time, use it once to create a permanent admin, then trigger rotation to invalidate the bootstrap credential.
5. **Verify during deploys** – Monitor deployment logs to confirm validation succeeds before routing traffic.

## Production Deployment

Provide the following environment variables with non-placeholder values before starting the application:

- `SECRET_KEY` – application signing key used for session data
- `JWT_SECRET_KEY` – signing key for API tokens
- `DATABASE_URL` – SQLAlchemy DSN for the primary database
- `REDIS_URL` – Redis connection string (also used for the Celery broker when set)
- `REDIS_PASSWORD` – password supplied to the Redis instance
- `METRICS_TOKEN` – shared secret presented via the `X-Metrics-Token` header when scraping `/metrics/`
- `ADMIN_BOOTSTRAP_PASSWORD` – temporary administrator credential used once at bootstrap

For local development you can use SQLite and a loopback Redis instance, for example:
```bash
DATABASE_URL=sqlite:///./data/dev.db
REDIS_PASSWORD=local-redis-password
REDIS_URL=redis://:local-redis-password@127.0.0.1:6379/0
```

Transcription jobs are executed through a **Celery-backed distributed task queue** defined in
`api/services/job_queue.py` and `api/worker.py`. The Celery worker processes transcription jobs
asynchronously, allowing the API to remain responsive while handling long-running transcription tasks.
Redis serves as both the message broker and result backend. The worker is defined in `worker.py` at
the repository root and executes tasks from `api.services.app_worker.py`, which performs the actual
Whisper model inference.

When deploying to an orchestrator, ensure the job queue (Redis + Celery worker) and storage paths mirror the local configuration described above.

## Observability

- **Structured logging** – All FastAPI services use the JSON logger provided by `api/utils/logger.py`. Each entry
  includes the timestamp, severity, request ID (when available), caller metadata, and any additional context supplied
  via the logging API.
- **Metrics** – The `/metrics/` endpoint exposes RED/USE style Prometheus metrics. Scrape requests must include
  the `X-Metrics-Token` header with the `METRICS_TOKEN` secret; unauthenticated requests are rejected with 401 responses.

## Dormant features

Some capabilities remain in the codebase but are intentionally disabled in production builds so they can mature off-line:

- **Multi-user accounts** – Only the bootstrap `admin` account is active. Set `MULTI_USER_MODE_ENABLED=1` to re-enable
  account-level scoping and the associated regression tests.
- **Legacy header auth** – Historical clients that relied on the `X-User-ID` header can be supported temporarily by
  toggling `LEGACY_USER_HEADER_ENABLED=1`. The header is otherwise ignored, and administrators authenticate with JWTs
  or session cookies.
- **Container delivery** – Terraform and Ansible still describe ECS/ECR-focused container rollouts, but deployments now
  run directly on hosts. Opt back in with `CONTAINER_BUILDS_ENABLED=1` when the Docker workflow returns.

## API Usage

Authenticate as the admin user to obtain a bearer token and then include it on subsequent requests:

```bash
TOKEN=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "X-Requested-With: XMLHttpRequest" \
  -d '{"username": "admin", "password": "super-secret-password-!123"}' \
  http://localhost:8001/auth/login | jq -r '.access_token')

curl -X POST \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "file=@audio.wav" \
  -F "model=small" \
  http://localhost:8001/jobs/
```

> **Legacy clients:** set `LEGACY_USER_HEADER_ENABLED=1` if you must continue sending `X-User-ID`. This compatibility
> switch will be removed once a new multi-user design lands.

## Supported Audio Formats

- WAV, MP3, M4A, FLAC
- Maximum file size: 100MB

## Models

Available Whisper models:
- tiny, small, medium, large, large-v3

Default model: small (best balance of speed/accuracy)