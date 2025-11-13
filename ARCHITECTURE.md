# Whisper Transcriber Architecture Documentation

## System Overview

Whisper Transcriber is a production-ready audio transcription service built with FastAPI backend and React frontend. The application uses OpenAI's Whisper models for audio transcription with a streamlined, production-focused architecture.

## Application Stack

### Backend (Python)
- **Framework**: FastAPI (async web framework)
- **Database**: SQLite with SQLAlchemy ORM
- **Task Queue**: Celery with Redis broker
- **Audio Processing**: Whisper, librosa, pydub
- **Authentication**: JWT tokens with secure session management

### Frontend (JavaScript/TypeScript)
- **Framework**: React 18 with Vite
- **UI Library**: Material-UI (MUI)
- **State Management**: Context API
- **HTTP Client**: Axios
- **Charts**: Chart.js with react-chartjs-2

### Infrastructure
- **Process orchestration**: Host-managed services (systemd, supervisord, etc.) running uvicorn and Celery directly
- **Web Server**: Uvicorn (ASGI server)
- **Caching**: Redis for session and API caching
- **File Storage**: Local filesystem with organized directory structure

## Core Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌────────────────┐
│   React Frontend│    │   FastAPI Backend│    │  Celery Worker │
│                 │    │                  │    │                │
│ • Upload UI     │◄──►│ • REST API       │◄──►│ • Transcription│
│ • Job Management│    │ • Authentication │    │ • Audio Process│
│ • Admin Panel   │    │ • File Handling  │    │ • Background   │
└─────────────────┘    └──────────────────┘    └────────────────┘
         │                        │                        │
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌────────────────┐
│   Static Files  │    │   SQLite Database│    │     Redis      │
│                 │    │                  │    │                │
│ • Built React   │    │ • Jobs           │    │ • Task Queue   │
│ • Assets        │    │ • Users          │    │ • Caching      │
│ • Uploads       │    │ • Transcripts    │    │ • Sessions     │
└─────────────────┘    └──────────────────┘    └────────────────┘
```

## Directory Structure

```
whisper-transcriber/
├── api/                          # Backend application
│   ├── routes/                   # API endpoints (24 files)
│   ├── services/                 # Business logic (20 files)
│   │   ├── consolidated_transcript_service.py  # Unified transcript ops
│   │   ├── consolidated_upload_service.py      # Unified upload ops
│   │   └── ...                   # Supporting services
│   ├── middlewares/              # Request/response processing
│   ├── models.py                 # Database models
│   ├── schemas.py                # Pydantic schemas
│   ├── main.py                   # Application entry point
│   └── settings.py               # Configuration
├── frontend/                     # React application
│   ├── src/
│   │   ├── components/           # React components
│   │   ├── pages/               # Main pages
│   │   ├── services/            # API clients
│   │   └── context/             # State management
│   └── dist/                    # Built static files
├── scripts/                     # CI tooling and security helpers
├── models/                      # Whisper model files (5GB)
├── storage/                     # Runtime file storage
└── observability/               # Prometheus and Grafana assets
```

## Core Services (Consolidated)

### 1. Consolidated Transcript Service
**File**: `api/services/consolidated_transcript_service.py`

**Purpose**: Unified transcript operations combining search, management, and export

**Key Functions**:
- `search_transcripts()` - Advanced search with filtering
- `export_transcript()` - Generate exports (txt, json)
- `batch_delete_transcripts()` - Bulk operations
- `manage_versions()` - Version control for transcripts

**Dependencies**: SQLAlchemy, FastAPI, logging

### 2. Consolidated Upload Service  
**File**: `api/services/consolidated_upload_service.py`

**Purpose**: Unified upload handling for all file types and sizes

**Key Functions**:
- `upload_single_file()` - Standard file upload
- `chunked_upload()` - Large file handling
- `batch_upload()` - Multiple file processing
- `validate_file()` - File type and size validation

**Dependencies**: FastAPI, WebSocket service, file validation

### 3. Audio Processing Service
**File**: `api/services/audio_processing.py`

**Purpose**: Audio enhancement and format conversion

**Key Functions**:
- `enhance_audio()` - Noise reduction, normalization
- `convert_format()` - Format standardization
- `extract_features()` - Audio analysis

**Dependencies**: librosa, pydub, scipy, numpy

## API Architecture

### Core Endpoints

#### Authentication
- `POST /auth/login` - User authentication
- `POST /register` - User registration
- `GET /auth/me` - Current user info
- `POST /auth/logout` - Session termination

#### Job Management
- `POST /jobs/` - Create transcription job
- `GET /jobs/` - List user jobs
- `GET /jobs/{job_id}` - Get job details
- `DELETE /jobs/{job_id}` - Delete job

#### Upload Operations
- `POST /api/uploads/single` - Single file upload
- `POST /api/uploads/batch` - Multiple file upload
- `POST /api/uploads/chunked/start` - Chunked upload start
- `POST /api/uploads/chunked/{id}/chunk/{num}` - Upload chunk

#### Transcript Management
- `POST /transcripts/search` - Advanced search
- `GET /api/export/transcript/{id}` - Export transcript
- `POST /transcripts/{id}/versions` - Create version
- `POST /transcripts/tags` - Tag management

#### Admin & Monitoring
- `GET /admin/stats` - System statistics
- `GET /health` - Health check
- `GET /admin/jobs` - Admin job management
- `GET /admin/system/metrics` - Performance metrics

## Database Schema

### Core Tables

#### Jobs Table
```sql
CREATE TABLE jobs (
    id INTEGER PRIMARY KEY,
    job_id VARCHAR(36) UNIQUE,     -- UUID
    filename VARCHAR(255),
    status VARCHAR(50),            -- pending, processing, completed, failed
    model VARCHAR(50),             -- whisper model used
    language VARCHAR(10),          -- detected/specified language
    audio_duration FLOAT,          -- in seconds
    transcript_text TEXT,          -- full transcript
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    user_id VARCHAR(36)           -- foreign key to users
);
```

#### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    user_id VARCHAR(36) UNIQUE,   -- UUID
    username VARCHAR(100) UNIQUE,
    email VARCHAR(255),
    password_hash VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    created_at TIMESTAMP
);
```

## Dependencies Map

### Backend Dependencies

#### Core Framework
```
fastapi >= 0.111.0
├── uvicorn[standard] >= 0.29.0      # ASGI server
├── pydantic >= 2.6.0                # Data validation
└── starlette                        # Web framework base
```

#### Database
```
sqlalchemy >= 2.0.30
├── alembic >= 1.12.0                # Database migrations
└── sqlite3                          # Database engine (built-in)
```

#### Audio Processing
```
openai-whisper == 20240930
├── torch >= 2.2.2                  # ML framework
├── librosa >= 0.10.0                # Audio analysis
├── pydub >= 0.25.1                  # Audio manipulation
├── soundfile >= 0.12.1              # Audio I/O
└── numpy >= 1.24.0                  # Numerical computing
```

#### Task Queue
```
celery >= 5.3
├── redis >= 5.0.0                   # Message broker
└── kombu                            # Messaging library
```

#### Security & Auth
```
PyJWT >= 2.8.0                      # JWT tokens
├── cryptography >= 41.0.0          # Encryption
├── passlib[bcrypt] >= 1.7.4         # Password hashing
└── bcrypt >= 4.0.1                  # Hashing algorithm
```

### Frontend Dependencies

#### Core React
```
react @ 18.2.0
├── react-dom @ 18.2.0               # DOM rendering
├── react-router-dom @ 6.16.0        # Routing
└── @vitejs/plugin-react @ 4.0.3     # Vite integration
```

#### UI Framework
```
@mui/material @ 5.18.0
├── @mui/icons-material @ 5.18.0     # Icon set
├── @emotion/react @ 11.14.0         # CSS-in-JS
└── @emotion/styled @ 11.14.1        # Styled components
```

#### Utilities
```
axios @ 1.5.0                        # HTTP client
├── chart.js @ 4.5.1                 # Charts
├── react-chartjs-2 @ 5.3.0          # React charts
├── react-dropzone @ 14.3.8          # File uploads
└── lucide-react @ 0.287.0           # Icons
```

## Data Flow

### File Upload Flow
1. **Frontend**: User selects audio file(s)
2. **Upload Service**: Validates file type/size
3. **Job Creation**: Creates database record
4. **Queue**: Adds to Celery task queue
5. **Worker**: Processes with Whisper model
6. **Storage**: Saves transcript to database
7. **Notification**: Updates job status

### Authentication Flow
1. **Login**: User submits credentials
2. **Validation**: Checks against database
3. **Token**: Generates JWT with claims
4. **Session**: Stores secure session data
5. **Requests**: Token validates API access
6. **Middleware**: Checks permissions per endpoint

### Search Flow
1. **Query**: User submits search criteria
2. **Service**: Builds SQL query with filters
3. **Database**: Executes optimized search
4. **Results**: Returns paginated results
5. **Frontend**: Displays with metadata

## Configuration

### Environment Variables
```bash
# Security (Required)
SECRET_KEY=<32-character-secret>
JWT_SECRET_KEY=<32-character-jwt-secret>
REDIS_PASSWORD=<redis-password>

# Database
DATABASE_URL=sqlite:///./whisper.db

# Services
REDIS_URL=redis://:password@redis:6379/0
CELERY_BROKER_URL=redis://:password@redis:6379/0

# Application
HOST=0.0.0.0
PORT=8001
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Whisper Models
Located in `/app/models/`:
- `tiny.pt` (73MB) - Fastest, basic accuracy
- `small.pt` (462MB) - Default, balanced
- `medium.pt` (1.5GB) - Better accuracy
- `large-v3.pt` (2.9GB) - Best accuracy

## Performance Characteristics

### Resource Usage
- **Memory**: 2-8GB depending on Whisper model
- **CPU**: Optimized for multi-core processing
- **Storage**: ~5GB for models + runtime data
- **Network**: Minimal (local processing)

### Scalability
- **Horizontal**: Multiple worker processes or hosts
- **Vertical**: Larger models for better accuracy
- **Caching**: Redis for API responses
- **Database**: SQLite suitable for moderate loads

### Security Features
- JWT authentication with secure sessions
- File type validation and size limits
- SQL injection prevention (SQLAlchemy ORM)
- CORS middleware configuration
- Secure headers middleware
- API rate limiting

## Deployment

### Runtime Services
- **API service** – `uvicorn api.main:app` hosted by a process manager such as systemd or supervisord.
- **Worker service** – `celery -A api.worker.celery_app worker` processing queued transcription jobs.
- **Redis** – broker/result backend. Use a managed offering or install it on the target host.

### Health Monitoring
- `/health` - Basic health check
- `/admin/stats` - System statistics
- Configure your process manager to restart services when `/readyz` fails or when the worker health task reports issues.
- Rotate logs via systemd journald or logrotate depending on your hosting environment.

## Development vs Production

This codebase is **production-only** after streamlining:
- Removed development/debugging features
- Eliminated complex backup systems
- Simplified configuration
- Production-optimized builds
- Security-focused deployment

## Troubleshooting

### Common Issues
1. **Model Loading**: Ensure models directory is mounted
2. **Redis Connection**: Check Redis password configuration
3. **File Uploads**: Verify storage directory permissions
4. **Transcription Fails**: Check model compatibility with audio format

### Logs
- Application logs: `logs/api.log` (if `logs/` exists alongside the application root)
- Security audit: `logs/security_audit.log`
- Worker output: review journalctl or your process manager logs for the Celery worker service