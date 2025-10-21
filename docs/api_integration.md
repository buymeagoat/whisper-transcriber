# API Integration Documentation

## Security Headers

All API responses include comprehensive security headers for OWASP compliance:
- `Content-Security-Policy`: Prevents XSS attacks
- `X-Frame-Options`: Prevents clickjacking
- `X-Content-Type-Options`: Prevents MIME type sniffing
- `Strict-Transport-Security`: Enforces HTTPS
- `X-XSS-Protection`: Browser XSS protection

## Rate Limiting

API endpoints are protected by rate limiting based on endpoint type:
- **Authentication**: 10 requests per 15 minutes
- **API endpoints**: 1000 requests per hour
- **Upload endpoints**: 100 requests per hour  
- **Admin endpoints**: 50 requests per 5 minutes
- **General endpoints**: 100 requests per 5 minutes

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## API Key Authentication

For programmatic access, use API keys instead of JWT tokens:

**Header:**
```
X-API-Key: your-api-key-here
```

API keys can be managed through the admin security dashboard.

## CSRF Protection

State-changing operations require CSRF tokens:

**Headers:**
```
X-CSRF-Token: csrf-token-value
```

Get CSRF tokens from `/admin/security/csrf-token` endpoint.

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

## Admin Security Endpoints

### GET /admin/security/dashboard
Get security monitoring dashboard data.

**Response:**
```json
{
  "active_sessions": 15,
  "failed_attempts_24h": 3,
  "rate_limit_hits_24h": 12,
  "security_incidents": 0,
  "api_keys_active": 5,
  "audit_events_24h": 142
}
```

### GET /admin/security/audit-logs
Get security audit logs with filtering.

**Query Parameters:**
- `event_type`: Filter by event type
- `severity`: Filter by severity level
- `start_date`: Start date filter
- `end_date`: End date filter
- `page`: Page number
- `page_size`: Results per page

### POST /admin/security/api-keys
Create new API key.

**Request:**
```json
{
  "name": "API Key Name",
  "permissions": ["read", "write"],
  "expires_days": 365
}
```

### GET /admin/security/incidents
Get security incidents.

### POST /admin/security/incidents/{incident_id}/resolve
Mark security incident as resolved.

## Admin Endpoints

### GET /admin/stats
Get system statistics (requires authentication).

### GET /admin/events
Get audit logs with filtering options.

### POST /admin/backup/create
Create system backup.

All admin endpoints require Bearer token authentication and admin role.

## Error Responses

Security-related errors include additional context:

```json
{
  "detail": "Rate limit exceeded",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 300,
  "limit_type": "auth"
}
```

```json
{
  "detail": "Input validation failed",
  "error_code": "VALIDATION_FAILED", 
  "validation_errors": ["XSS attempt detected"],
  "risk_score": 8
}
```

## Input Validation

All inputs are validated for security threats:
- XSS attack patterns
- SQL injection attempts
- Command injection patterns
- Path traversal attempts
- Malicious file uploads

Blocked requests are logged with risk scores and details.

````

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
