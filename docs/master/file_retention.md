# File Retention Policy

This document explains how Whisper Transcriber retains or cleans up artifacts generated during transcription.

## Transcript Artifacts
- Completed transcripts and metadata are written under `transcripts/{job_id}`.
- Original uploads remain in `uploads/`.
- When `CLEANUP_ENABLED=true`, a background task removes uploads and transcript folders older than `CLEANUP_DAYS`.
- Disable cleanup by setting `CLEANUP_ENABLED=false` or adjust the number of days with `CLEANUP_DAYS`.

## Logs
- Runtime and build logs live in `logs/`.
- Files rotate at `LOG_MAX_BYTES` with `LOG_BACKUP_COUNT` backups retained.
- When cleanup is enabled, log files older than the cutoff are deleted.
- If `LOG_TO_STDOUT=true` the same output is also streamed to the container logs.

## Abandoned Jobs
- Jobs that were in progress when the server stopped are automatically requeued at startup.
- Failed or missing uploads are marked accordingly so the cleanup task can remove their artifacts.

## Cleanup Mechanism
- The API spawns a cleanup thread at startup when enabled. It runs every `CLEANUP_INTERVAL_SECONDS`.
- Administrators can view or update the current settings via the `/admin/cleanup-config` endpoint.

See also: [observability.md](observability.md) and the admin endpoints in [api_reference.md](api_reference.md).
