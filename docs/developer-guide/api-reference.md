# API Reference

This document describes the REST API endpoints for the Whisper Transcriber streamlined application.

## Base URL

```
http://localhost:8000
```

## Authentication

The streamlined version does not require authentication for basic transcription features. All endpoints are publicly accessible.

## Endpoints

### Health Check

#### `GET /`

Check service health and get basic information.

**Response:**
```json
{
  "service": "Whisper Transcriber",
  "version": "2.0.0", 
  "status": "online",
  "features": ["audio-upload", "real-time-progress", "mobile-friendly"]
}
```

---

### Transcription

#### `POST /transcribe`

Upload an audio file and start transcription.

**Parameters:**
- `file` (form-data, required): Audio file to transcribe
- `model` (form-data, optional): Whisper model to use (`tiny`, `small`, `medium`, `large-v3`)

**Request Example:**
```bash
curl -X POST http://localhost:8000/transcribe \
  -F "file=@audio.mp3" \
  -F "model=small"
```

**Response:**
```json
{
  "job_id": "abc123",
  "status": "pending",
  "filename": "audio.mp3",
  "model": "small",
  "created_at": "2025-10-10T14:30:00Z"
}
```

**Error Responses:**
- `400` - Invalid file format or missing file
- `413` - File too large
- `500` - Server error

---

### Job Status

#### `GET /jobs/{job_id}`

Get the status and details of a transcription job.

**Parameters:**
- `job_id` (path, required): Job identifier

**Response:**
```json
{
  "id": "abc123",
  "status": "completed",
  "filename": "audio.mp3",
  "original_filename": "my-recording.mp3",
  "model_used": "small",
  "transcript": "Hello, this is a test transcription.",
  "created_at": "2025-10-10T14:30:00Z",
  "completed_at": "2025-10-10T14:32:15Z",
  "file_size": 1024000,
  "duration": 120,
  "error_message": null
}
```

**Status Values:**
- `pending` - Job queued for processing
- `processing` - Currently being transcribed
- `completed` - Transcription finished successfully
- `failed` - Transcription failed (check error_message)

---

### Download Transcript

#### `GET /jobs/{job_id}/download`

Download the transcript in the specified format.

**Parameters:**
- `job_id` (path, required): Job identifier
- `format` (query, optional): Output format (`txt`, `json`). Defaults to `txt`

**Request Examples:**
```bash
# Download as text
curl http://localhost:8000/jobs/abc123/download

# Download as JSON
curl http://localhost:8000/jobs/abc123/download?format=json
```

**Response (format=txt):**
```
Hello, this is a test transcription.
```

**Response (format=json):**
```json
{
  "job_id": "abc123",
  "transcript": "Hello, this is a test transcription.",
  "model": "small",
  "duration": 120,
  "language": "en",
  "created_at": "2025-10-10T14:30:00Z"
}
```

---

### List Jobs

#### `GET /jobs`

List all transcription jobs.

**Parameters:**
- `limit` (query, optional): Maximum number of jobs to return (default: 50)
- `offset` (query, optional): Number of jobs to skip (default: 0)

**Response:**
```json
{
  "jobs": [
    {
      "id": "abc123",
      "status": "completed",
      "filename": "audio.mp3",
      "model_used": "small", 
      "created_at": "2025-10-10T14:30:00Z",
      "completed_at": "2025-10-10T14:32:15Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

---

### Delete Job

#### `DELETE /jobs/{job_id}`

Delete a transcription job and its associated files.

**Parameters:**
- `job_id` (path, required): Job identifier

**Response:**
```json
{
  "message": "Job deleted successfully",
  "job_id": "abc123"
}
```

**Error Responses:**
- `404` - Job not found
- `500` - Server error

---

### Real-time Progress

#### `WebSocket /ws/jobs/{job_id}`

Connect to receive real-time progress updates for a transcription job.

**Parameters:**
- `job_id` (path, required): Job identifier

**Connection Example (JavaScript):**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/jobs/abc123');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Progress:', data);
};
```

**Message Format:**
```json
{
  "job_id": "abc123",
  "status": "processing",
  "progress": 75,
  "message": "Transcribing audio...",
  "timestamp": "2025-10-10T14:31:30Z"
}
```

**Progress Values:**
- `0-100` - Percentage complete
- `status` - Current job status
- `message` - Human-readable progress description

---

## Data Models

### Job Object

```json
{
  "id": "string",
  "status": "pending|processing|completed|failed",
  "filename": "string",
  "original_filename": "string", 
  "model_used": "tiny|small|medium|large-v3",
  "transcript": "string|null",
  "created_at": "datetime",
  "completed_at": "datetime|null",
  "file_size": "integer|null",
  "duration": "integer|null",
  "error_message": "string|null"
}
```

## Error Handling

All API endpoints return structured error responses:

```json
{
  "detail": "Error description",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2025-10-10T14:30:00Z"
}
```

Common HTTP status codes:
- `200` - Success
- `400` - Bad Request (validation error)
- `404` - Not Found
- `413` - Payload Too Large
- `422` - Unprocessable Entity
- `500` - Internal Server Error

## Rate Limiting

The application processes transcription jobs based on available worker capacity. No explicit rate limiting is enforced, but concurrent jobs are limited by the `CELERY_CONCURRENCY` setting.

## File Limits

- **Maximum file size**: Configurable via `MAX_FILE_SIZE_MB` (default: 100MB)
- **Supported formats**: MP3, WAV, M4A, FLAC (configurable via `ALLOWED_AUDIO_FORMATS`)
- **Maximum duration**: No explicit limit, but controlled by `WHISPER_TIMEOUT_SECONDS`

## WebSocket Connection

WebSocket connections are automatically closed when:
- Job completes (success or failure)
- Client disconnects
- Server restarts

Clients should handle reconnection if needed.
