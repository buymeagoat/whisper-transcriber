# Observability Guide

Whisper Transcriber exposes several endpoints and log files to aid monitoring.

## Health Endpoints

- **`/health`** – returns `{"status": "ok"}` when the API and database are reachable.
- **`/metrics`** – Prometheus metrics. Requires an admin token.
- **`/version`** – current application version from `pyproject.toml`.

Docker Compose defines healthchecks for the `api`, `worker`, `db` and `broker` services. The compose stack waits until each container reports healthy before starting dependent services.

## Logs

- **File paths** – runtime logs live under `logs/`. Job logs are named `<job_id>.log`; the system log is `system.log`.
- **WebSocket feeds** – connect to `/ws/logs/{job_id}` for a running job or `/ws/logs/system` for global logs.
- **Container output** – when `LOG_TO_STDOUT=true`, logs also appear in `docker compose logs`.

## Manual Checks

Run `pgrep -f uvicorn` to verify the API is running or `curl http://localhost:8000/health` for a quick status check. Use `docker ps` or `docker compose ps` to confirm containers are up. The helper script `scripts/diagnose_containers.sh` collects these details automatically.

## Suggested Alerts

Monitor queue length (`queue_length` metric) and job duration (`job_duration_seconds`). Alerts should fire when the queue continues growing or jobs take unusually long. Disk usage under `uploads/`, `transcripts/` and `logs/` should also be watched.

## Frontend Build Status

The build process now verifies that `frontend/dist/index.html` exists before Docker build starts. If missing, the build aborts with an error.

## Cache Location Warnings

When using WSL, `/tmp/docker_cache` may fail due to permission issues. Consider using `/mnt/wsl/shared/docker_cache` instead.

