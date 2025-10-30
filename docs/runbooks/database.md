# Database Migration Runbook

This runbook walks release engineers through performing database migrations for the Whisper Transcriber service. It emphasizes safety controls such as pre-flight validation, automated backups, and repeatable rollback instructions.

## 1. Preconditions

1. **Change review** – Confirm the Alembic migration files under `api/migrations/versions/` have passed code review and CI (including `pytest tests/test_migrations.py`).
2. **Environment access** – Ensure you have bastion or VPN access to the production network and credentials for the managed PostgreSQL cluster.
3. **Maintenance window** – Announce the planned maintenance window in the operations channel and status page.
4. **Monitoring** – Pin dashboards for database CPU, replication lag, and API latency. Enable alert acknowledgements.

## 2. Required tooling

- `psql` or an equivalent PostgreSQL client (for running administrative commands).
- Access to the secrets manager storing `DATABASE_URL` or individual Postgres credentials.
- The application repository at the target release tag.

## 3. Backup procedure

1. Resolve the current production connection string:
   ```bash
   export DATABASE_URL="$(secretctl read prod/whisper-transcriber/DATABASE_URL)"
   ```
2. Capture a logical backup using `pg_dump` with consistent snapshots:
   ```bash
   pg_dump \
     --format=custom \
     --file="whisper-transcriber-$(date +%Y%m%d%H%M%S).dump" \
     "$DATABASE_URL"
   ```
3. Upload the dump to encrypted object storage and record the object URI in the change ticket.
4. Verify the backup by listing relations inside the archive:
   ```bash
   pg_restore --list whisper-transcriber-*.dump | less
   ```

## 4. Migration dry run

1. Run migrations against a staging environment with production-like data:
   ```bash
   export $(cat .env.staging | xargs)
   alembic upgrade head
   pytest tests/test_migrations.py
   ```
2. Validate the application boots and critical flows succeed (transcription upload, playback, admin login).
3. Capture before/after schema diffs using `pg_dump --schema-only` if required by compliance.

## 5. Applying migrations in production

1. Freeze new deployments and pause scheduled jobs.
2. Confirm replication is healthy (`SELECT now() - pg_last_xact_replay_timestamp()`).
3. Apply migrations from the release tag:
   ```bash
   export DATABASE_URL="$(secretctl read prod/whisper-transcriber/DATABASE_URL)"
   alembic upgrade head
   ```
4. Watch the migration logs for errors. Typical runtime should be under one minute; abort if exceeding the change window limits.
5. Run smoke tests (API health endpoint, Celery task dispatch, transcription workflow).

## 6. Post-migration validation

1. Review monitoring dashboards for regressions (latency, error rate, deadlocks).
2. Confirm new schema elements exist (`\d tablename` in `psql`).
3. Hand off to QA for exploratory testing if required.

## 7. Rollback and restoration

If you must undo the migration:

1. Evaluate whether the migration is reversible. Check the downgrade logic in the corresponding file under `api/migrations/versions/`.
2. Execute a logical rollback using Alembic:
   ```bash
   export DATABASE_URL="$(secretctl read prod/whisper-transcriber/DATABASE_URL)"
   alembic downgrade -1  # or specify the previous revision hash
   ```
3. If data corruption occurred or downgrade is unsafe, perform a full restore:
   ```bash
   pg_restore \
     --clean \
     --if-exists \
     --dbname="$DATABASE_URL" \
     whisper-transcriber-<timestamp>.dump
   ```
4. After rollback or restore, rerun smoke tests and inform stakeholders.

## 8. Closeout

1. Resume automated deployments and background jobs.
2. Document the migration outcome (success, rollback, issues) in the change ticket.
3. Schedule a retrospective if manual intervention was required.
