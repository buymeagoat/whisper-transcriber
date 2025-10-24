# Whisper Transcriber API Reference

## Table of Contents
- [Overview](#overview)
- [Authentication](#authentication)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [API Endpoints](#api-endpoints)
  - [Authentication & Users](#authentication--users)
  - [Jobs & Transcription](#jobs--transcription)
  - [File Management](#file-management)
  - [Export & Search](#export--search)
  - [Administration](#administration)
  - [API Keys & Security](#api-keys--security)
  - [System Performance](#system-performance)
  - [Advanced Features](#advanced-features)
- [SDK & Integration Examples](#sdk--integration-examples)
- [Troubleshooting](#troubleshooting)

## Overview

The Whisper Transcriber API provides a comprehensive REST interface for audio transcription, file management, user authentication, and system administration. The API supports multiple authentication methods, chunked file uploads, batch processing, and real-time progress tracking.

**Base URL**: `http://localhost:8000` (development) or your deployed domain  
**API Version**: v1  
**Documentation**: Available at `/docs` (Swagger UI) and `/redoc` (ReDoc)

### Key Features
- 🎤 **Audio Transcription**: Multiple Whisper model support (tiny, small, medium, large-v3)
- 🔐 **Security**: JWT authentication, API keys, rate limiting, audit logging
- 📁 **File Management**: Chunked uploads, batch processing, multiple format support
- 🔍 **Search & Export**: Full-text search, multiple export formats (TXT, SRT, VTT, JSON)
- 📊 **Administration**: System monitoring, performance metrics, user management
- 🚀 **Advanced Features**: Real-time collaboration, workspaces, PWA support

## Authentication

### Authentication Methods

The API supports multiple authentication methods:

1. **JWT Bearer Token** (Primary)
2. **API Keys** (For programmatic access)
3. **Session-based** (For web interface)

### JWT Authentication Flow

```bash
# 1. Register a new user
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "securePassword123",
    "email": "user@example.com"
  }'

# 2. Login to get JWT token
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "securePassword123"
  }'

# Response:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIs...",
#   "token_type": "bearer",
#   "expires_in": 3600
# }

# 3. Use token in subsequent requests
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

### API Key Authentication

```bash
# Create API key (requires JWT authentication)
curl -X POST "http://localhost:8000/api/api-keys/" \
  -H "Authorization: Bearer <your-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Integration",
    "permissions": ["jobs:read", "jobs:create"],
    "expires_days": 90
  }'

# Use API key in requests
curl -X GET "http://localhost:8000/api/jobs/" \
  -H "X-API-Key: <your-api-key>"
```

## Error Handling

### Standard Error Response Format

```json
{
  "detail": "Error message",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2025-10-23T22:15:00Z",
  "request_id": "uuid-here"
}
```

### Common HTTP Status Codes

| Status Code | Meaning | Description |
|-------------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

## Rate Limiting

Rate limiting is applied based on user authentication and endpoint type:

- **Anonymous users**: 60 requests per minute
- **Authenticated users**: 300 requests per minute  
- **API key users**: Based on key configuration
- **Admin endpoints**: 100 requests per minute

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 299
X-RateLimit-Reset: 1635724800
```

## API Endpoints

### Authentication & Users

#### POST /auth/register
Register a new user account.

**Request Body:**
```json
{
  "username": "user@example.com",
  "password": "securePassword123",
  "email": "user@example.com"
}
```

**Response (201):**
```json
{
  "message": "User registered successfully",
  "user_id": "123",
  "username": "user@example.com"
}
```

#### POST /auth/login
Authenticate user and receive JWT token.

**Request Body:**
```json
{
  "username": "user@example.com", 
  "password": "securePassword123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "123",
    "username": "user@example.com",
    "email": "user@example.com"
  }
}
```

#### GET /auth/me
Get current authenticated user information.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "id": "123",
  "username": "user@example.com",
  "email": "user@example.com",
  "created_at": "2025-01-15T10:30:00Z",
  "is_active": true
}
```

#### POST /auth/logout
Logout and invalidate current session.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "message": "Successfully logged out"
}
```

#### POST /auth/change-password
Change user password.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "current_password": "oldPassword",
  "new_password": "newSecurePassword123"
}
```

### Jobs & Transcription

#### POST /api/jobs/
Create a new transcription job.

**Headers:** 
- `Authorization: Bearer <token>` or `X-API-Key: <api-key>`
- `Content-Type: multipart/form-data`

**Form Data:**
- `file`: Audio file (MP3, WAV, M4A, etc.)
- `model`: Whisper model (`tiny`, `small`, `medium`, `large-v3`)
- `language`: Language code (optional, auto-detect if not provided)
- `prompt`: Initial prompt for better accuracy (optional)

**Example:**
```bash
curl -X POST "http://localhost:8000/api/jobs/" \
  -H "Authorization: Bearer <token>" \
  -F "file=@audio.mp3" \
  -F "model=medium" \
  -F "language=en"
```

**Response (201):**
```json
{
  "job_id": "job_123456",
  "status": "queued",
  "filename": "audio.mp3",
  "model": "medium",
  "created_at": "2025-10-23T22:15:00Z",
  "estimated_duration": "2-5 minutes"
}
```

#### GET /api/jobs/
List user's transcription jobs.

**Headers:** `Authorization: Bearer <token>` or `X-API-Key: <api-key>`

**Query Parameters:**
- `limit`: Number of jobs to return (default: 50, max: 100)
- `offset`: Pagination offset (default: 0)
- `status`: Filter by status (`queued`, `processing`, `completed`, `failed`)
- `created_after`: ISO timestamp filter

**Response (200):**
```json
{
  "jobs": [
    {
      "job_id": "job_123456",
      "status": "completed",
      "filename": "audio.mp3",
      "model": "medium",
      "created_at": "2025-10-23T22:15:00Z",
      "completed_at": "2025-10-23T22:17:30Z",
      "duration": "2m 30s",
      "transcript_preview": "Hello, this is a sample transcription..."
    }
  ],
  "total": 25,
  "limit": 50,
  "offset": 0
}
```

#### GET /api/jobs/{job_id}
Get specific job details and transcript.

**Headers:** `Authorization: Bearer <token>` or `X-API-Key: <api-key>`

**Response (200):**
```json
{
  "job_id": "job_123456",
  "status": "completed",
  "filename": "audio.mp3",
  "model": "medium",
  "language": "en",
  "created_at": "2025-10-23T22:15:00Z",
  "completed_at": "2025-10-23T22:17:30Z",
  "transcript": {
    "text": "Hello, this is the complete transcription...",
    "segments": [
      {
        "start": 0.0,
        "end": 2.5,
        "text": "Hello, this is"
      }
    ],
    "language": "en",
    "confidence": 0.95
  }
}
```

#### DELETE /api/jobs/{job_id}
Delete a transcription job.

**Headers:** `Authorization: Bearer <token>` or `X-API-Key: <api-key>`

**Response (200):**
```json
{
  "message": "Job deleted successfully"
}
```

#### GET /api/progress/{job_id}
Get real-time job progress.

**Headers:** `Authorization: Bearer <token>` or `X-API-Key: <api-key>`

**Response (200):**
```json
{
  "job_id": "job_123456",
  "status": "processing",
  "progress": 65,
  "stage": "transcribing",
  "estimated_time_remaining": "1m 30s",
  "current_segment": 45,
  "total_segments": 78
}
```

### File Management

#### POST /api/chunked-uploads/initialize
Initialize chunked upload session for large files.

**Headers:** 
- `Authorization: Bearer <token>` or `X-API-Key: <api-key>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "filename": "large_audio.wav",
  "file_size": 104857600,
  "chunk_size": 1048576,
  "content_type": "audio/wav"
}
```

**Response (201):**
```json
{
  "session_id": "upload_session_123",
  "upload_url": "/api/chunked-uploads/upload_session_123/chunks",
  "expires_at": "2025-10-23T23:15:00Z",
  "total_chunks": 100
}
```

#### POST /api/chunked-uploads/{session_id}/chunks/{chunk_number}
Upload a file chunk.

**Headers:** 
- `Authorization: Bearer <token>` or `X-API-Key: <api-key>`
- `Content-Type: application/octet-stream`

**Body:** Raw chunk data

**Response (200):**
```json
{
  "chunk_number": 1,
  "received_size": 1048576,
  "checksum": "sha256hash",
  "progress": 1.0
}
```

#### POST /api/chunked-uploads/{session_id}/finalize
Complete chunked upload and create transcription job.

**Headers:** 
- `Authorization: Bearer <token>` or `X-API-Key: <api-key>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "model": "medium",
  "language": "en",
  "chunk_checksums": ["hash1", "hash2", "..."]
}
```

**Response (201):**
```json
{
  "job_id": "job_123456",
  "status": "queued",
  "message": "File uploaded successfully and transcription queued"
}
```

### Export & Search

#### GET /api/export/formats
Get available export formats.

**Headers:** `Authorization: Bearer <token>` or `X-API-Key: <api-key>`

**Response (200):**
```json
{
  "formats": [
    {
      "name": "txt",
      "description": "Plain text",
      "mime_type": "text/plain",
      "supports_timestamps": false
    },
    {
      "name": "srt",
      "description": "SubRip subtitle format",
      "mime_type": "application/x-subrip",
      "supports_timestamps": true
    },
    {
      "name": "vtt",
      "description": "WebVTT subtitle format", 
      "mime_type": "text/vtt",
      "supports_timestamps": true
    }
  ]
}
```

#### GET /api/export/download/{job_id}/{format}
Download transcript in specified format.

**Headers:** `Authorization: Bearer <token>` or `X-API-Key: <api-key>`

**Path Parameters:**
- `job_id`: Job identifier
- `format`: Export format (`txt`, `srt`, `vtt`, `json`)

**Response:** File download with appropriate content-type

#### POST /api/search/
Search transcripts.

**Headers:** 
- `Authorization: Bearer <token>` or `X-API-Key: <api-key>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "query": "machine learning",
  "filters": {
    "date_range": {
      "start": "2025-10-01",
      "end": "2025-10-23"
    },
    "models": ["medium", "large-v3"],
    "languages": ["en"]
  },
  "limit": 20,
  "offset": 0
}
```

**Response (200):**
```json
{
  "results": [
    {
      "job_id": "job_123456",
      "filename": "ml_lecture.mp3",
      "relevance_score": 0.95,
      "matches": [
        {
          "text": "...discussing machine learning algorithms...",
          "timestamp": 125.5,
          "confidence": 0.92
        }
      ],
      "created_at": "2025-10-15T14:30:00Z"
    }
  ],
  "total": 5,
  "query_time": "0.15s"
}
```

### Administration

#### GET /admin/health
Get system health status.

**Headers:** `Authorization: Bearer <admin-token>`

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-23T22:15:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy", 
    "whisper": "healthy",
    "storage": "healthy"
  },
  "metrics": {
    "uptime": "5d 12h 30m",
    "active_jobs": 3,
    "queue_size": 5,
    "memory_usage": "45%",
    "cpu_usage": "12%"
  }
}
```

#### GET /admin/stats
Get system statistics.

**Headers:** `Authorization: Bearer <admin-token>`

**Response (200):**
```json
{
  "jobs": {
    "total": 1524,
    "completed": 1489,
    "failed": 12,
    "processing": 3,
    "queued": 20
  },
  "users": {
    "total": 45,
    "active_last_24h": 12,
    "new_last_7d": 5
  },
  "storage": {
    "total_files": 1524,
    "total_size_gb": 125.8,
    "avg_file_size_mb": 84.5
  },
  "performance": {
    "avg_processing_time": "2m 15s",
    "success_rate": 97.8,
    "throughput_per_hour": 45
  }
}
```

### API Keys & Security

#### GET /api/api-keys/
List user's API keys.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "api_keys": [
    {
      "key_id": "key_123",
      "name": "My Integration",
      "key_preview": "wt_****_****_1234",
      "permissions": ["jobs:read", "jobs:create"],
      "created_at": "2025-10-15T10:00:00Z",
      "expires_at": "2026-01-15T10:00:00Z",
      "last_used": "2025-10-23T20:15:00Z",
      "usage_count": 1524,
      "is_active": true
    }
  ]
}
```

#### POST /api/api-keys/
Create new API key.

**Headers:** 
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "name": "My Integration",
  "permissions": ["jobs:read", "jobs:create", "export:download"],
  "expires_days": 90,
  "rate_limit": {
    "requests_per_minute": 100,
    "daily_quota": 10000
  }
}
```

**Response (201):**
```json
{
  "key_id": "key_123",
  "api_key": "wt_1234567890abcdef_fedcba0987654321_1234",
  "name": "My Integration",
  "permissions": ["jobs:read", "jobs:create", "export:download"],
  "expires_at": "2026-01-15T10:00:00Z",
  "message": "API key created successfully. Store this key securely - it cannot be retrieved again."
}
```

## SDK & Integration Examples

### Python Integration Example

```python
import requests
import json
from typing import Optional

class WhisperTranscriberClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': api_key,
            'User-Agent': 'WhisperTranscriber-Python-Client/1.0'
        })
    
    def create_job(self, file_path: str, model: str = 'medium', 
                   language: Optional[str] = None) -> dict:
        """Create a new transcription job."""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'model': model}
            if language:
                data['language'] = language
            
            response = self.session.post(
                f'{self.base_url}/api/jobs/',
                files=files,
                data=data
            )
            response.raise_for_status()
            return response.json()
    
    def get_job(self, job_id: str) -> dict:
        """Get job details and transcript."""
        response = self.session.get(f'{self.base_url}/api/jobs/{job_id}')
        response.raise_for_status()
        return response.json()
    
    def wait_for_completion(self, job_id: str, poll_interval: int = 10) -> dict:
        """Wait for job completion with polling."""
        import time
        
        while True:
            job = self.get_job(job_id)
            if job['status'] in ['completed', 'failed']:
                return job
            time.sleep(poll_interval)

# Usage example
client = WhisperTranscriberClient('http://localhost:8000', 'your-api-key')

# Create job
job = client.create_job('audio.mp3', model='medium', language='en')
print(f"Job created: {job['job_id']}")

# Wait for completion
completed_job = client.wait_for_completion(job['job_id'])
print(f"Transcript: {completed_job['transcript']['text']}")
```

### JavaScript/Node.js Integration Example

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

class WhisperTranscriberClient {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.client = axios.create({
            headers: {
                'X-API-Key': apiKey,
                'User-Agent': 'WhisperTranscriber-JS-Client/1.0'
            }
        });
    }

    async createJob(filePath, model = 'medium', language = null) {
        const formData = new FormData();
        formData.append('file', fs.createReadStream(filePath));
        formData.append('model', model);
        if (language) formData.append('language', language);

        const response = await this.client.post('/api/jobs/', formData, {
            headers: formData.getHeaders()
        });
        return response.data;
    }

    async getJob(jobId) {
        const response = await this.client.get(`/api/jobs/${jobId}`);
        return response.data;
    }

    async waitForCompletion(jobId, pollInterval = 10000) {
        while (true) {
            const job = await this.getJob(jobId);
            if (['completed', 'failed'].includes(job.status)) {
                return job;
            }
            await new Promise(resolve => setTimeout(resolve, pollInterval));
        }
    }
}

// Usage example
const client = new WhisperTranscriberClient('http://localhost:8000', 'your-api-key');

async function transcribeAudio() {
    try {
        // Create job
        const job = await client.createJob('audio.mp3', 'medium', 'en');
        console.log(`Job created: ${job.job_id}`);

        // Wait for completion
        const completedJob = await client.waitForCompletion(job.job_id);
        console.log(`Transcript: ${completedJob.transcript.text}`);
    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
    }
}

transcribeAudio();
```

## Troubleshooting

### Common Issues

#### Authentication Errors

**Error 401: Unauthorized**
- Verify JWT token is valid and not expired
- Check API key format and permissions
- Ensure proper Authorization header format

**Error 403: Forbidden** 
- Check user permissions for the endpoint
- Verify API key has required permissions
- Admin endpoints require admin role

#### File Upload Issues

**Error 413: Payload Too Large**
- Use chunked upload for files > 25MB
- Check file size limits in configuration
- Consider compressing audio files

**Error 415: Unsupported Media Type**
- Verify file format is supported (MP3, WAV, M4A, etc.)
- Check content-type header is correct
- Ensure file is not corrupted

#### Transcription Issues

**Error 422: Processing Failed**
- Check audio file quality and format
- Try different Whisper model (smaller models for testing)
- Verify file is valid audio content

### Rate Limiting

If you receive 429 errors:
- Implement exponential backoff in your client
- Check rate limit headers for reset time
- Consider upgrading API key limits
- Use batch processing for multiple files

### Performance Optimization

**For better performance:**
- Use appropriate Whisper model for your needs
- Implement chunked uploads for large files
- Cache results when possible
- Use batch processing for multiple files
- Consider audio preprocessing (noise reduction, normalization)

### Support

- **Documentation**: Available at `/docs` and `/redoc` endpoints
- **Health Check**: Monitor `/admin/health` for system status
- **Logs**: Check application logs for detailed error information
- **API Status**: Monitor rate limits and quotas in response headers

---

*This documentation is automatically generated and updated. For the most current API specification, visit the interactive documentation at `/docs`.*