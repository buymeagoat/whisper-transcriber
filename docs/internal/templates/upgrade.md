# Upgrade Guide

The project follows semantic versioning. Review `CHANGELOG.md` before upgrading to see if any breaking changes are noted.

## When to Upgrade

Check the `CHANGELOG.md` file for new releases. Minor and patch versions are usually safe drops in. Major versions may require additional steps.

## Backup First

Follow the steps in [backup_and_recovery.md](backup_and_recovery.md) to archive the database, `uploads/`, `transcripts/` and `logs/` directories before applying an update.

## Validate Models and Dependencies

After pulling a new version, run `scripts/whisper_build.sh --purge-cache` to refresh cached packages and verify Whisper models are present. If the cache is already populated and you are offline, use `--offline`.

## Database Migrations

The backend uses Alembic. Run:
```bash
alembic upgrade head
```
from the project root or allow `uvicorn` to run migrations automatically on startup.

## Post-upgrade Steps

1. Rebuild images with `scripts/whisper_build.sh --purge-cache`.
2. Re-run `scripts/run_tests.sh` to ensure all tests pass.
3. Restart the Docker Compose stack using `scripts/whisper_build.sh`.
