# HTTP API Reference

## Jobs

### POST /jobs
Upload an audio file and start transcription. Parameter `file` is multipart form data; optional `model` selects the Whisper model. Returns job ID.
🔐 Auth Required: user

### GET /jobs
List jobs. Optional query params `search` and `status`.
🔐 Auth Required: user

### GET /jobs/{id}
Get status for a single job.
🔐 Auth Required: user

### DELETE /jobs/{id}
Remove a job and its files.
🔐 Auth Required: user

### POST /jobs/{id}/restart
Requeue a failed job.
🔐 Auth Required: user

### GET /jobs/{id}/download
Download transcript with optional `format` (`srt`, `txt`, `vtt`).
🔐 Auth Required: user

### GET /metadata/{id}
Retrieve generated metadata for a job.
🔐 Auth Required: user

### POST /jobs/{id}/analyze
Summarize and analyze a transcript using OpenAI.
🔐 Auth Required: user

## Admin

### GET /admin/files
List log, upload and transcript files.
🔐 Auth Required: admin

### DELETE /admin/files
Delete a single file (JSON body: `{"folder":"logs","filename":"foo.log"}`).
🔐 Auth Required: admin

### GET /admin/browse
Browse directories via `folder` and optional `path` query.
🔐 Auth Required: admin

### POST /admin/reset
Remove all data and database records.
🔐 Auth Required: admin

### GET /admin/download-all
Download a zip archive of all logs and transcripts.
🔐 Auth Required: admin

### GET /admin/stats
CPU, memory and job statistics.
🔐 Auth Required: admin

### POST /admin/shutdown
Shut down the running server when `ENABLE_SERVER_CONTROL=true`.
🔐 Auth Required: admin

### POST /admin/restart
Restart the server process.
🔐 Auth Required: admin

### GET /admin/cleanup-config
View cleanup settings.
🔐 Auth Required: admin

### POST /admin/cleanup-config
Update cleanup settings.
🔐 Auth Required: admin

### GET /admin/concurrency
View worker concurrency.
🔐 Auth Required: admin

### POST /admin/concurrency
Update worker concurrency.
🔐 Auth Required: admin

## Logs

### GET /log/{job_id}
Retrieve a job log file.
🔐 Auth Required: user

### GET /logs/{filename}
Fetch arbitrary log file by name.
🔐 Auth Required: user

### GET /logs/access
Access log if enabled.
🔐 Auth Required: user

### WebSocket /ws/logs/{job_id}
Stream log output for a running job.
🔐 Auth Required: user

### WebSocket /ws/logs/system
Stream system or access log in real time.
🔐 Auth Required: admin

## Auth

### POST /register
Create a new user account when `ALLOW_REGISTRATION=true`.
🔐 Auth Required: none

### POST /token
Obtain a JWT for subsequent requests.
🔐 Auth Required: none

### POST /change-password
Update the current user's password.
🔐 Auth Required: user

Example request to submit a job:
```bash
curl -F 'file=@audio.wav' http://localhost:8000/jobs -H 'Authorization: Bearer <token>'
```
Example response from `/jobs/{id}`:
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
