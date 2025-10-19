# API Integration Documentation

## Authentication Endpoints

### POST /register
Register a new user account.

**Request:**
```json
{
  "username": "user@example.com",
  "password": "password123",
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "message": "User registered successfully",
  "user_id": "123",
  "username": "user@example.com"
}
```

### POST /auth/login
Authenticate user and receive JWT token.

**Request:**
```json
{
  "username": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### GET /auth/me
Get current authenticated user information.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": "123",
  "username": "user@example.com",
  "is_active": true
}
```

## Jobs/Transcription Endpoints

### POST /jobs/
Create a new transcription job.

**Request:** (multipart/form-data)
- `file`: Audio file
- `model`: Whisper model (small, medium, large-v3)
- `language`: Optional language code

**Response:**
```json
{
  "job_id": "uuid-here",
  "status": "queued",
  "created_at": "2025-10-19T17:00:00Z"
}
```

### GET /jobs/
List all transcription jobs for authenticated user.

**Response:**
```json
{
  "jobs": [...],
  "total": 10,
  "skip": 0,
  "limit": 100
}
```

### GET /jobs/{job_id}
Get specific job details and results.

### GET /progress/{job_id}
Get real-time transcription progress.

## Admin Endpoints

### GET /admin/stats
Get system statistics (requires authentication).

### GET /admin/events
Get audit logs with filtering options.

### POST /admin/backup/create
Create system backup.

All admin endpoints require Bearer token authentication.
