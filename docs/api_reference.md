# HTTP API Reference

## Jobs
| Method | Endpoint | Auth? | Description |
| --- | --- | --- | --- |
| POST | `/jobs` | Token | Upload an audio file and start transcription. Parameter `file` is multipart form data; optional `model` selects the Whisper model. Returns job ID. |
| GET | `/jobs` | Token | List jobs. Optional query params `search` and `status`. |
| GET | `/jobs/{id}` | Token | Get status for a single job. |
| DELETE | `/jobs/{id}` | Token | Remove a job and its files. |
| POST | `/jobs/{id}/restart` | Token | Requeue a failed job. |
| GET | `/jobs/{id}/download` | Token | Download transcript with optional `format` (`srt`, `txt`, `vtt`). |
| GET | `/metadata/{id}` | Token | Retrieve generated metadata for a job. |
| POST | `/jobs/{id}/analyze` | Token | Summarize and analyze a transcript using OpenAI. |

## Admin (requires admin role)
| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/admin/files` | List log, upload and transcript files. |
| DELETE | `/admin/files` | Delete a single file (JSON body: `{"folder":"logs","filename":"foo.log"}`). |
| GET | `/admin/browse` | Browse directories via `folder` and optional `path` query. |
| POST | `/admin/reset` | Remove all data and database records. |
| GET | `/admin/download-all` | Download a zip archive of all logs and transcripts. |
| GET | `/admin/stats` | CPU, memory and job statistics. |
| POST | `/admin/shutdown` | Shut down the running server when `ENABLE_SERVER_CONTROL=true`. |
| POST | `/admin/restart` | Restart the server process. |
| GET | `/admin/cleanup-config` | View cleanup settings. |
| POST | `/admin/cleanup-config` | Update cleanup settings. |
| GET | `/admin/concurrency` | View worker concurrency. |
| POST | `/admin/concurrency` | Update worker concurrency. |

## Logs
| Method | Endpoint | Auth? | Description |
| --- | --- | --- | --- |
| GET | `/log/{job_id}` | Token | Retrieve a job log file. |
| GET | `/logs/{filename}` | Token | Fetch arbitrary log file by name. |
| GET | `/logs/access` | Token | Access log if enabled. |
| WebSocket | `/ws/logs/{job_id}` | Token | Stream log output for a running job. |
| WebSocket | `/ws/logs/system` | Admin | Stream system or access log in real time. |

## Auth
| Method | Endpoint | Auth? | Description |
| --- | --- | --- | --- |
| POST | `/register` | None (if enabled) | Create a new user account when `ALLOW_REGISTRATION=true`. |
| POST | `/token` | Basic | Obtain a JWT for subsequent requests. |
| POST | `/change-password` | Token | Update the current user's password. |

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
