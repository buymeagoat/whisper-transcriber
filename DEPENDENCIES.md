# Dependency Analysis

## Backend Dependencies Overview

### Production Dependencies (requirements.txt)

#### Core Framework Stack
```
fastapi==0.111.0
├── Used by: main.py, all route files, service files
├── Purpose: Web framework providing async API endpoints
├── Key Features: Automatic OpenAPI docs, request validation, dependency injection
└── Critical: Core application framework

uvicorn[standard]==0.29.0
├── Used by: main.py and deployment process managers
├── Purpose: ASGI server for running FastAPI application
├── Includes: websockets, watchfiles, colorama, python-dotenv
└── Critical: Application server

pydantic==2.6.4
├── Used by: schemas.py, models validation, API request/response
├── Purpose: Data validation and serialization
├── Integration: FastAPI automatic validation
└── Critical: Data integrity
```

#### Database & ORM
```
SQLAlchemy==2.0.30
├── Used by: models.py, all service files, database operations
├── Purpose: Object-relational mapping and database abstraction
├── Features: Async support, relationship management, query building
└── Critical: Data persistence

alembic==1.12.0
├── Used by: migrations/ directory, database schema management
├── Purpose: Database migration and versioning
├── Integration: SQLAlchemy schema changes
└── Important: Schema evolution
```

#### Audio Processing Stack
```
openai-whisper==20240930
├── Used by: worker.py, transcription processing
├── Purpose: Core transcription AI model
├── Models: tiny.pt, small.pt, medium.pt, large-v3.pt
└── Critical: Primary functionality

torch==2.2.2
├── Used by: Whisper model inference, GPU acceleration
├── Purpose: Machine learning framework
├── Size: ~800MB installed
└── Critical: AI model execution

librosa==0.10.0
├── Used by: audio_processing.py, audio analysis
├── Purpose: Audio feature extraction and analysis
├── Features: Spectral analysis, rhythm, pitch detection
└── Important: Audio preprocessing

pydub==0.25.1
├── Used by: audio format conversion, audio manipulation
├── Purpose: Audio file format handling
├── Dependencies: ffmpeg for format support
└── Important: File compatibility

soundfile==0.12.1
├── Used by: Audio I/O operations
├── Purpose: Reading/writing audio files
├── Formats: WAV, FLAC, OGG support
└── Supporting: Audio pipeline
```

#### Task Queue & Caching
```
celery==5.3.0
├── Used by: worker.py, background task processing
├── Purpose: Distributed task queue for async processing
├── Integration: Redis broker, result backend
└── Critical: Background processing

redis==5.0.0
├── Used by: Celery broker, session storage, caching
├── Purpose: In-memory data structure store
├── Features: Pub/sub, persistence, clustering
└── Critical: Queue and cache
```

#### Authentication & Security
```
PyJWT==2.8.0
├── Used by: auth routes, middleware, token validation
├── Purpose: JSON Web Token implementation
├── Security: HS256/RS256 algorithms, expiration
└── Critical: Authentication

passlib[bcrypt]==1.7.4
├── Used by: User registration, password verification
├── Purpose: Password hashing and verification
├── Algorithm: bcrypt with salt rounds
└── Critical: Security

cryptography==41.0.0
├── Used by: JWT signing, encryption operations
├── Purpose: Cryptographic operations
├── Features: Symmetric/asymmetric encryption
└── Important: Security foundation
```

#### HTTP & Networking
```
httpx==0.27.0
├── Used by: External API calls, HTTP client operations
├── Purpose: Async HTTP client
├── Features: HTTP/2 support, connection pooling
└── Supporting: External integrations

websockets==12.0
├── Used by: Real-time communication, job status updates
├── Purpose: WebSocket server implementation
├── Integration: FastAPI WebSocket endpoints
└── Important: Real-time features
```

#### Data Processing
```
numpy==1.24.3
├── Used by: Audio processing, numerical computations
├── Purpose: Array operations and mathematical functions
├── Integration: librosa, torch dependencies
└── Supporting: Audio pipeline

scipy==1.10.1
├── Used by: Audio signal processing, scientific computing
├── Purpose: Advanced mathematical algorithms
├── Features: Signal filtering, statistical functions
└── Supporting: Audio enhancement
```

## Frontend Dependencies Overview

### Production Dependencies (package.json)

#### Core React Ecosystem
```
react@18.2.0
├── Used by: All component files, main application
├── Purpose: Core UI library for component-based development
├── Features: Hooks, context, virtual DOM
└── Critical: Frontend framework

react-dom@18.2.0
├── Used by: main.jsx, DOM rendering
├── Purpose: React DOM bindings for web applications
├── Integration: React component rendering to browser DOM
└── Critical: Web rendering

react-router-dom@6.16.0
├── Used by: App.jsx, navigation, page routing
├── Purpose: Client-side routing for single-page application
├── Features: Nested routes, lazy loading, navigation guards
└── Critical: Navigation
```

#### UI Framework & Styling
```
@mui/material@5.18.0
├── Used by: All UI components, layout, forms
├── Purpose: React UI component library with Material Design
├── Components: Buttons, forms, tables, navigation
└── Critical: UI foundation

@mui/icons-material@5.18.0
├── Used by: Icons throughout application
├── Purpose: Material Design icon set
├── Integration: MUI theming system
└── Important: Visual consistency

@emotion/react@11.14.0
├── Used by: MUI styling, CSS-in-JS
├── Purpose: CSS-in-JS library for component styling
├── Features: Theme support, performance optimization
└── Supporting: MUI dependency

@emotion/styled@11.14.1
├── Used by: Custom styled components
├── Purpose: Styled component creation
├── Integration: Emotion CSS-in-JS system
└── Supporting: Component styling
```

#### HTTP & Data Management
```
axios@1.5.0
├── Used by: services/api.js, HTTP requests
├── Purpose: HTTP client for API communication
├── Features: Interceptors, request/response transformation
└── Critical: API communication

react-query@3.39.3 (if present)
├── Used by: Data fetching, caching, synchronization
├── Purpose: Server state management
├── Features: Caching, background updates, optimistic updates
└── Important: Data management
```

#### Visualization & Charts
```
chart.js@4.5.1
├── Used by: Admin dashboard, statistics visualization
├── Purpose: Chart rendering library
├── Types: Line, bar, pie, doughnut charts
└── Important: Data visualization

react-chartjs-2@5.3.0
├── Used by: React integration for Chart.js
├── Purpose: React wrapper for Chart.js
├── Integration: React component lifecycle
└── Important: Chart components
```

#### File Handling
```
react-dropzone@14.3.8
├── Used by: File upload components
├── Purpose: Drag-and-drop file upload interface
├── Features: File validation, preview, progress
└── Important: Upload UX

lucide-react@0.287.0
├── Used by: Additional icons, UI elements
├── Purpose: Lightweight icon library
├── Features: Tree-shakeable, customizable
└── Supporting: Icon variety
```

#### Build & Development Tools
```
vite@4.4.5
├── Used by: Build process, development server
├── Purpose: Fast build tool and development server
├── Features: Hot module replacement, tree shaking
└── Critical: Build system

@vitejs/plugin-react@4.0.3
├── Used by: Vite React integration
├── Purpose: React support in Vite build system
├── Features: JSX compilation, Fast Refresh
└── Critical: React build support

typescript@5.0.2 (if present)
├── Used by: Type checking, development experience
├── Purpose: Static type checking for JavaScript
├── Benefits: Better IDE support, error prevention
└── Important: Development quality
```

## Dependency Relationships

### Critical Path Dependencies
```
Application Startup:
FastAPI → uvicorn → main.py → router_setup.py → routes/

Authentication Flow:
PyJWT → cryptography → passlib → user authentication

Audio Processing Pipeline:
pydub → librosa → numpy → scipy → whisper → torch

Task Queue:
celery → redis → worker.py → transcription jobs

Frontend Build:
react → vite → @vitejs/plugin-react → production bundle
```

### Service Integration Map
```
api/main.py
├── fastapi (web framework)
├── uvicorn (ASGI server)
├── sqlalchemy (database)
├── redis (caching/sessions)
└── router_setup.py
    ├── routes/ (API endpoints)
    └── services/ (business logic)

worker.py
├── celery (task queue)
├── openai-whisper (transcription)
├── torch (AI inference)
├── librosa (audio processing)
└── redis (result storage)

frontend/src/
├── react (UI framework)
├── @mui/material (components)
├── axios (API client)
├── react-router-dom (navigation)
└── chart.js (visualization)
```

### Database Dependencies
```
SQLAlchemy Models (models.py)
├── Jobs table → User relationship
├── Transcripts table → Job relationship
├── User sessions → Redis storage
└── Migration tracking → Alembic versions

Database Operations
├── Create: SQLAlchemy Core + ORM
├── Read: Query optimization, pagination
├── Update: Version tracking, audit logs
├── Delete: Soft delete with cleanup
```

### Security Dependencies
```
Authentication Chain:
User credentials → passlib.hash → bcrypt verification
User data → PyJWT.encode → JWT token → Redis session

API Security:
Request → JWT middleware → token validation → user context
File upload → security validation → type checking → storage

Encryption:
Sensitive data → cryptography → AES encryption → secure storage
```

### Performance Dependencies
```
Caching Strategy:
API responses → Redis cache → TTL expiration
Session data → Redis storage → automatic cleanup
File metadata → Memory cache → LRU eviction

Audio Processing:
Large files → chunked processing → memory management
Whisper models → GPU acceleration (torch.cuda)
Background tasks → Celery workers → parallel processing
```

## Version Compatibility Matrix

### Python Compatibility
```
Python 3.8+ Required
├── FastAPI 0.111.0 → Python 3.8+
├── SQLAlchemy 2.0.30 → Python 3.7+
├── Whisper 20240930 → Python 3.8+
└── Torch 2.2.2 → Python 3.8+

Recommended: Python 3.11 (best performance)
```

### Node.js Compatibility
```
Node.js 18+ Required
├── React 18.2.0 → Node 16+
├── Vite 4.4.5 → Node 14.18+
├── MUI 5.18.0 → Node 12+
└── Chart.js 4.5.1 → Node 16+

Recommended: Node.js 20 LTS
```

### System Dependencies
```
Audio Processing:
├── ffmpeg (required for pydub format conversion)
├── libsndfile (required for soundfile)
├── CUDA Toolkit (optional, for GPU acceleration)

Database:
├── SQLite 3.31+ (built into Python)
├── Redis 6.0+ (for queue and caching)

Process Management:
├── systemd or supervisord for long-running API and worker services
├── Reverse proxy (nginx, Caddy, or equivalent) for TLS termination (optional)
```

## Security Dependencies

### Authentication Security
```
Password Security:
passlib + bcrypt → Salt rounds: 12 → Secure hashing
PyJWT → HS256 algorithm → Secret key rotation

Session Security:
Redis → Secure session storage → TTL expiration
FastAPI → CORS middleware → Origin validation
```

### File Security
```
Upload Validation:
File type checking → MIME validation → Extension verification
Size limits → Memory protection → Storage quotas
Path sanitization → Directory traversal prevention
```

### Network Security
```
HTTPS Required:
TLS 1.2+ → Certificate validation → Secure transport
WebSocket Security:
WSS protocol → Token authentication → Connection validation
```

## Monitoring Dependencies

### Application Monitoring
```
Health Checks:
/health endpoint → Service availability → Dependency status
System Metrics:
CPU/Memory monitoring → Performance tracking → Alert thresholds

Logging:
Python logging → Structured logs → Centralized collection
Error Tracking:
Exception handling → Error categorization → Alert notification
```

### Performance Monitoring
```
Database Performance:
SQLAlchemy query logging → Slow query detection
API Performance:
Request timing → Response size → Throughput metrics
Background Tasks:
Celery monitoring → Queue depth → Processing time
```

This dependency analysis provides a complete picture of how all components interact and depend on each other in the streamlined application.