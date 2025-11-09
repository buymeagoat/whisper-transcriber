# Function Reference

## Core API Functions

### Authentication (`api/routes/auth.py`)

#### `login(credentials: schemas.UserLogin)`
- **Purpose**: Authenticate user and create session
- **Input**: Username/email and password
- **Output**: JWT token and user data
- **Dependencies**: `password_service`, `user_service`
- **Security**: Password hashing verification, rate limiting

#### `register(user_data: schemas.UserCreate)`
- **Purpose**: Create new user account
- **Input**: User registration data
- **Output**: User ID and confirmation
- **Dependencies**: `user_service`, `password_service`
- **Validation**: Email format, password strength

#### `get_current_user(token: str)`
- **Purpose**: Validate JWT and return user info
- **Input**: JWT token from Authorization header
- **Output**: Current user object
- **Dependencies**: `jwt_service`
- **Security**: Token validation and expiry check

### Upload Operations (`api/services/consolidated_upload_service.py`)

#### `ConsolidatedUploadService.upload_single_file(file: UploadFile, user_id: str)`
- **Purpose**: Handle single file upload and validation
- **Input**: File object and user identifier
- **Output**: Job ID and upload status
- **Validation**: File type (audio), size limits, format support
- **Process**: File storage → job creation → queue for processing

#### `ConsolidatedUploadService.chunked_upload_start(metadata: dict)`
- **Purpose**: Initialize chunked upload for large files
- **Input**: File metadata (name, size, total chunks)
- **Output**: Upload session ID and chunk map
- **Storage**: Creates temporary upload directory
- **Tracking**: Progress monitoring and resumable uploads

#### `ConsolidatedUploadService.chunked_upload_chunk(session_id: str, chunk_num: int, chunk_data: bytes)`
- **Purpose**: Process individual chunk in chunked upload
- **Input**: Session ID, chunk number, binary data
- **Output**: Chunk confirmation and next expected chunk
- **Validation**: Chunk order, size, integrity
- **Assembly**: Combines chunks when complete

#### `ConsolidatedUploadService.batch_upload(files: List[UploadFile])`
- **Purpose**: Handle multiple file uploads simultaneously
- **Input**: Array of file objects
- **Output**: Array of job IDs and statuses
- **Processing**: Parallel file validation and storage
- **Error Handling**: Partial success reporting

### Transcript Management (`api/services/consolidated_transcript_service.py`)

#### `ConsolidatedTranscriptService.search_transcripts(query: schemas.SearchQuery)`
- **Purpose**: Advanced search across transcript content
- **Input**: Search parameters (text, filters, pagination)
- **Output**: Paginated search results with metadata
- **Features**: Full-text search, date range, user filtering
- **Performance**: Indexed search with result ranking

#### `ConsolidatedTranscriptService.export_transcript(transcript_id: str, format: str)`
- **Purpose**: Generate transcript exports in various formats
- **Input**: Transcript ID and desired format (txt, json, srt)
- **Output**: Formatted transcript content
- **Formats**: Plain text, JSON with timestamps, SRT subtitles
- **Customization**: Speaker labels, confidence scores

#### `ConsolidatedTranscriptService.batch_delete_transcripts(transcript_ids: List[str])`
- **Purpose**: Bulk deletion of transcript records
- **Input**: Array of transcript IDs
- **Output**: Deletion status and error reports
- **Validation**: User ownership verification
- **Cleanup**: Associated files and metadata removal

#### `ConsolidatedTranscriptService.manage_versions(transcript_id: str, action: str)`
- **Purpose**: Version control for transcript edits
- **Input**: Transcript ID and version action
- **Output**: Version history and current state
- **Actions**: Create version, restore, compare
- **Storage**: Differential storage for efficiency

### Job Management (`api/routes/jobs.py`)

#### `create_job(job_data: schemas.JobCreate)`
- **Purpose**: Create new transcription job
- **Input**: Job parameters (file, model, language) sent with an `X-User-ID` header identifying the caller
- **Output**: Job ID and initial status
- **Workflow**: Database record → queue task → status tracking
- **Options**: Model selection, language hints, custom settings

#### `get_job_status(job_id: str)`
- **Purpose**: Retrieve current job status and progress
- **Input**: Job identifier
- **Output**: Status, progress percentage, results
- **States**: pending, processing, completed, failed
- **Progress**: Real-time updates via WebSocket
- **Security**: Requires matching `X-User-ID` header; mismatched users receive 404

#### `list_user_jobs(user_id: str, filters: dict)`
- **Purpose**: Get paginated list of user's jobs
- **Input**: User ID and optional filters
- **Output**: Job list with metadata
- **Filters**: Status, date range, filename search
- **Sorting**: Creation date, status, filename
- **Security**: Results limited to the authenticated `X-User-ID`

#### `cancel_job(job_id: str)`
- **Purpose**: Cancel pending or running job
- **Input**: Job identifier
- **Output**: Cancellation confirmation
- **Process**: Queue removal → cleanup → status update
- **Limitations**: Cannot cancel completed jobs
- **Security**: Only the job owner (matching `X-User-ID`) may cancel

### Audio Processing (`api/services/audio_processing.py`)

#### `AudioProcessor.enhance_audio(file_path: str, settings: dict)`
- **Purpose**: Improve audio quality before transcription
- **Input**: Audio file path and enhancement settings
- **Output**: Enhanced audio file path
- **Features**: Noise reduction, normalization, filtering
- **Quality**: Configurable enhancement levels

#### `AudioProcessor.convert_format(input_path: str, output_format: str)`
- **Purpose**: Convert audio to Whisper-compatible format
- **Input**: Source file path and target format
- **Output**: Converted file path
- **Formats**: WAV, MP3, FLAC, M4A → WAV (16kHz, mono)
- **Optimization**: Format-specific conversion parameters

#### `AudioProcessor.extract_features(file_path: str)`
- **Purpose**: Analyze audio characteristics
- **Input**: Audio file path
- **Output**: Audio metadata and features
- **Analysis**: Duration, sample rate, channels, loudness
- **Usage**: Model selection hints, quality assessment

#### `AudioProcessor.split_audio(file_path: str, segment_length: int)`
- **Purpose**: Split long audio into manageable segments
- **Input**: Audio path and segment duration (seconds)
- **Output**: Array of segment file paths
- **Features**: Smart splitting at silence, overlap handling
- **Reassembly**: Transcript merging with timing preservation

### Whisper Integration (`worker.py`)

#### `transcribe_audio(job_id: str, audio_path: str, model_name: str)`
- **Purpose**: Core transcription using Whisper model
- **Input**: Job ID, audio file path, model selection
- **Output**: Transcript text with timestamps and metadata
- **Models**: tiny, small, medium, large-v3
- **Features**: Language detection, confidence scores

#### `load_whisper_model(model_name: str)`
- **Purpose**: Load Whisper model into memory
- **Input**: Model name (tiny, small, medium, large-v3)
- **Output**: Loaded model object
- **Caching**: Memory caching for performance
- **Fallback**: Default to 'small' if model unavailable

#### `process_transcription_result(result: dict, job_id: str)`
- **Purpose**: Process raw Whisper output into structured data
- **Input**: Whisper result object and job ID
- **Output**: Formatted transcript with metadata
- **Processing**: Timestamp alignment, confidence scoring
- **Storage**: Database storage with indexing

### Admin Functions (`api/routes/admin.py`)

#### `get_system_stats()`
- **Purpose**: Retrieve system performance metrics
- **Output**: CPU, memory, disk usage, job statistics
- **Metrics**: Active jobs, queue length, processing times
- **History**: Historical data for trend analysis

#### `manage_jobs(action: str, job_ids: List[str])`
- **Purpose**: Administrative job management
- **Input**: Action type and job ID array
- **Actions**: cancel, retry, delete, prioritize
- **Permissions**: Admin-only access
- **Audit**: Action logging for security

#### `cleanup_orphaned_files()`
- **Purpose**: Remove files without database references
- **Output**: Cleanup report with freed space
- **Safety**: Verification before deletion
- **Schedule**: Configurable automatic cleanup

#### `export_audit_logs(date_range: dict)`
- **Purpose**: Generate security audit reports
- **Input**: Start and end dates
- **Output**: Formatted audit log export
- **Content**: Authentication, API access, admin actions
- **Formats**: CSV, JSON for analysis

### WebSocket Functions (`api/services/websocket_service.py`)

#### `WebSocketService.connect(websocket: WebSocket, user_id: str)`
- **Purpose**: Establish real-time connection
- **Input**: WebSocket connection and user identifier
- **Output**: Connection confirmation
- **Authentication**: Token-based connection auth
- **Management**: Connection pool tracking

#### `WebSocketService.broadcast_job_update(job_id: str, status: dict)`
- **Purpose**: Send job status updates to connected clients
- **Input**: Job ID and status information
- **Process**: User lookup → connection find → message send
- **Format**: Structured JSON status messages
- **Reliability**: Connection health monitoring

#### `WebSocketService.send_progress_update(user_id: str, progress: dict)`
- **Purpose**: Real-time progress updates for long operations
- **Input**: User ID and progress data
- **Content**: Percentage, current step, estimated time
- **Throttling**: Rate limiting to prevent spam
- **Fallback**: HTTP polling for unsupported clients

### Security Functions (`api/services/security_service.py`)

#### `SecurityService.validate_file_type(file: UploadFile)`
- **Purpose**: Verify uploaded file is allowed audio format
- **Input**: File upload object
- **Output**: Validation result and file metadata
- **Validation**: MIME type, file signature, extension check
- **Security**: Prevents malicious file uploads

#### `SecurityService.rate_limit_check(user_id: str, endpoint: str)`
- **Purpose**: Enforce API rate limiting per user/endpoint
- **Input**: User identifier and API endpoint
- **Output**: Allow/deny decision and remaining quota
- **Tracking**: Redis-based rate limiting
- **Configuration**: Per-endpoint and per-user limits

#### `SecurityService.audit_log(action: str, user_id: str, details: dict)`
- **Purpose**: Record security-relevant actions
- **Input**: Action type, user ID, action details
- **Storage**: Secure audit log with tamper detection
- **Content**: Timestamps, IP addresses, action results
- **Retention**: Configurable log retention policy

## Utility Functions

### File Operations (`api/utils/file_utils.py`)

#### `calculate_file_hash(file_path: str)`
- **Purpose**: Generate file integrity hash
- **Input**: File path
- **Output**: SHA-256 hash string
- **Usage**: Duplicate detection, integrity verification

#### `get_audio_duration(file_path: str)`
- **Purpose**: Extract audio duration without full loading
- **Input**: Audio file path
- **Output**: Duration in seconds (float)
- **Efficiency**: Metadata-only reading for speed

#### `clean_filename(filename: str)`
- **Purpose**: Sanitize filename for safe storage
- **Input**: Original filename
- **Output**: Sanitized filename
- **Security**: Remove path traversal attempts, special characters

### Database Operations (`api/utils/db_utils.py`)

#### `paginate_query(query: Query, page: int, size: int)`
- **Purpose**: Add pagination to SQLAlchemy queries
- **Input**: Query object, page number, page size
- **Output**: Paginated results with metadata
- **Optimization**: Efficient counting and limiting

#### `soft_delete_record(model: Base, record_id: str)`
- **Purpose**: Mark record as deleted without physical removal
- **Input**: Model class and record identifier
- **Output**: Update confirmation
- **Safety**: Maintains referential integrity

### Response Formatting (`api/utils/response_utils.py`)

#### `format_success_response(data: Any, message: str)`
- **Purpose**: Standardize successful API responses
- **Input**: Response data and success message
- **Output**: Formatted JSON response
- **Structure**: Consistent response format across API

#### `format_error_response(error: Exception, status_code: int)`
- **Purpose**: Standardize error responses with proper codes
- **Input**: Exception object and HTTP status code
- **Output**: Formatted error response
- **Security**: Sanitizes sensitive error details

## Frontend Functions

### API Client (`frontend/src/services/api.js`)

#### `uploadFile(file: File, onProgress: Function)`
- **Purpose**: Upload file with progress tracking
- **Input**: File object and progress callback
- **Output**: Promise with upload result
- **Features**: Progress reporting, error handling, retry logic

#### `getJobStatus(jobId: string)`
- **Purpose**: Poll job status from API
- **Input**: Job identifier
- **Output**: Promise with current job status
- **Caching**: Smart caching to reduce API calls

#### `searchTranscripts(query: SearchParams)`
- **Purpose**: Execute transcript search with filters
- **Input**: Search parameters object
- **Output**: Promise with search results
- **Features**: Debounced search, pagination support

### State Management (`frontend/src/context/AppContext.js`)

#### `useAuth()`
- **Purpose**: Authentication state management
- **Output**: Auth state and functions (login, logout, refresh)
- **Persistence**: Local storage integration
- **Security**: Token refresh handling

#### `useJobs()`
- **Purpose**: Job management state
- **Output**: Job list, status updates, management functions
- **Real-time**: WebSocket integration for live updates
- **Caching**: Optimistic updates for better UX

#### `useNotifications()`
- **Purpose**: App-wide notification system
- **Output**: Notification state and display functions
- **Types**: Success, error, warning, info notifications
- **Features**: Auto-dismiss, action buttons, stacking