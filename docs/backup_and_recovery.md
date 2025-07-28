# Backup and Recovery

👤 Target Audience: Admins and Operators

This project stores uploads, transcripts, logs and a PostgreSQL database. Preserve these assets regularly to avoid data loss.

## Important Data
- `uploads/` – source audio files
- `transcripts/` – generated SRT and metadata
- `logs/` – application and build logs
- PostgreSQL database specified by `DB_URL`

## Backup Procedures
### Manual
1. Stop the Docker stack so files are consistent:
   ```bash
   docker compose down
   ```
2. Archive the data directories:
   ```bash
   tar czf backup_$(date +%F).tar.gz uploads transcripts logs
   pg_dump "$DB_URL" > db_$(date +%F).sql
   ```

### Automated
- Schedule `pg_dump` and `tar` commands via cron.
- When `STORAGE_BACKEND=cloud`, sync the `uploads/` and `transcripts/` directories to S3:
   ```bash
   aws s3 sync uploads s3://mybucket/uploads
   aws s3 sync transcripts s3://mybucket/transcripts
   ```
- Rotate old backups and verify integrity periodically.

## Restore Procedures
1. Extract archived files back to the project root:
   ```bash
   tar xzf backup_2025-07-28.tar.gz -C .
   psql "$DB_URL" < db_2025-07-28.sql
   ```
2. Restart the application stack:
   ```bash
   docker compose up -d
   ```

Ensure the same version of Whisper Transcriber is used when restoring from backups to avoid migration conflicts.
