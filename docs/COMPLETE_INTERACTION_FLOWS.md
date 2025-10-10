# Complete User Action → Backend Function Flow Map

## Overview
This document maps every user interaction through the complete technology stack, showing the exact files, functions, and dependencies involved in each action.

---

## 🔐 **AUTHENTICATION FLOWS**

### 1. User Login Process
```
👤 USER ACTION: Enter credentials and click "Login"
    ↓
📱 FRONTEND: pages/LoginPage.jsx
    - handleSubmit() function
    - Validates form input
    - Creates URLSearchParams with username/password
    ↓
🌐 API CALL: POST /token
    - Content-Type: application/x-www-form-urlencoded
    - Body: {username: "admin", password: "changeme"}
    ↓
🔧 BACKEND: api/routes/auth.py
    - @router.post("/token") decorator
    - authenticate_user() function
    ↓
📊 DEPENDENCIES:
    - api/services/users.py::get_user_by_username()
    - api/services/users.py::verify_password()
    - api/settings.py::settings.secret_key
    ↓
🗄️ DATABASE OPERATIONS:
    - SELECT * FROM users WHERE username = ?
    - Password hash verification
    ↓
🔄 BUSINESS LOGIC:
    - create_access_token() in auth.py
    - JWT token generation with expiration
    ↓
📤 RESPONSE: TokenLoginOut
    - access_token: JWT string
    - token_type: "bearer"
    - must_change_password: boolean
    ↓
📱 FRONTEND HANDLING:
    - AuthContext.login() called
    - Token stored in localStorage
    - Redirect to ROUTES.UPLOAD or ROUTES.CHANGE_PASSWORD
```

### 2. Password Change Process  
```
👤 USER ACTION: Enter new password and submit
    ↓
📱 FRONTEND: pages/ChangePasswordPage.jsx
    - handleSubmit() function
    - Validates password strength
    ↓
🌐 API CALL: POST /change-password
    - Authorization: Bearer {token}
    - Body: {password: "newpassword"}
    ↓
🔧 BACKEND: api/routes/auth.py
    - @router.post("/change-password") 
    - get_current_user() dependency injection
    ↓
📊 DEPENDENCIES:
    - api/services/users.py::update_user_password()
    - api/services/users.py::hash_password()
    ↓
🗄️ DATABASE OPERATIONS:
    - UPDATE users SET password_hash = ? WHERE id = ?
    ↓
📤 RESPONSE: 204 No Content
    ↓
📱 FRONTEND HANDLING:
    - Success toast notification
    - Redirect to main application
```

---

## 📁 **FILE UPLOAD & TRANSCRIPTION FLOWS**

### 3. Audio File Upload Process
```
👤 USER ACTION: Select audio file, choose model, click "Upload All"
    ↓
📱 FRONTEND: pages/UploadPage.jsx
    - File validation (validateFile() function)
    - Size check (MAX_SIZE_MB = 2048)
    - Type check (ALLOWED_TYPES array)
    - handleUploadAll() function
    ↓
🌐 API CALL: POST /jobs
    - Content-Type: multipart/form-data
    - FormData: {file: File, model: "tiny"}
    ↓
🔧 BACKEND: api/routes/jobs.py
    - @router.post("/jobs") decorator
    - create_job() function
    - get_current_user() dependency
    ↓
📊 DEPENDENCIES:
    - api/services/storage.py::save_upload()
    - api/models.py::Job (SQLAlchemy model)
    - api/services/job_queue.py::enqueue()
    - api/services/whisper_service.py::handle_whisper()
    ↓
🗄️ DATABASE OPERATIONS:
    - INSERT INTO jobs (original_filename, saved_filename, model, user_id, status)
    - INSERT INTO transcript_metadata (job_id, created_at)
    ↓
🔄 BUSINESS LOGIC:
    - File saved to uploads/ directory with UUID filename
    - Job queued for processing
    - Background worker picks up job
    ↓
🤖 WHISPER PROCESSING:
    - api/worker.py launches Celery worker
    - api/services/celery_app.py::run_callable()
    - Whisper AI model processes audio
    - Transcript saved to transcripts/ directory
    ↓
📤 RESPONSE: JobCreateOut
    - job_id: UUID
    - status: "queued"
    ↓
📱 FRONTEND HANDLING:
    - Job ID displayed
    - Status updates via WebSocket
    - "Start New Job" button appears
```

### 4. Download Transcript Process
```
👤 USER ACTION: Click "Download" button on completed job
    ↓
📱 FRONTEND: pages/CompletedJobsPage.jsx
    - handleDownloadTranscript() function
    - getTranscriptDownloadUrl() from routes.js
    ↓
🌐 API CALL: GET /jobs/{job_id}/download?format=txt
    - Authorization: Bearer {token}
    - Query params: format (txt, json, srt, vtt)
    ↓
🔧 BACKEND: api/routes/jobs.py
    - @router.get("/jobs/{job_id}/download")
    - download_transcript() function
    ↓
📊 DEPENDENCIES:
    - api/services/storage.py::get_transcript_file()
    - api/exporters/txt_exporter.py (or json, srt, vtt)
    - api/models.py::Job
    ↓
🗄️ DATABASE OPERATIONS:
    - SELECT * FROM jobs WHERE id = ? AND user_id = ?
    - SELECT * FROM transcript_metadata WHERE job_id = ?
    ↓
🔄 BUSINESS LOGIC:
    - Load transcript from file system
    - Format according to requested type
    - Set appropriate Content-Type headers
    ↓
📤 RESPONSE: FileResponse
    - Content-Disposition: attachment; filename="transcript.txt"
    - File content streamed to browser
    ↓
📱 FRONTEND HANDLING:
    - Browser initiates download
    - File saved to user's Downloads folder
```

---

## 🎧 **REAL-TIME & MULTIMEDIA FLOWS**

### 5. Job Progress Monitoring (WebSocket)
```
👤 USER ACTION: Click "View Progress" on active job
    ↓
📱 FRONTEND: pages/JobProgressPage.jsx
    - Opens in new tab/window
    - WebSocket connection established
    ↓
🌐 WEBSOCKET: /ws/progress/{job_id}?token={auth_token}
    - Real-time bidirectional connection
    ↓
🔧 BACKEND: api/routes/progress.py
    - @router.websocket("/ws/progress/{job_id}")
    - websocket_progress() function
    ↓
📊 DEPENDENCIES:
    - api/services/job_queue.py::get_job_status()
    - api/models.py::Job
    - WebSocket connection manager
    ↓
🗄️ DATABASE OPERATIONS:
    - Periodic SELECT jobs WHERE id = ? for status updates
    ↓
🔄 BUSINESS LOGIC:
    - Job status polling (queued → processing → enriching → completed)
    - Progress percentage calculation
    - Real-time status broadcasting
    ↓
📤 WEBSOCKET MESSAGES:
    - {status: "processing", progress: 45, message: "Transcribing..."}
    ↓
📱 FRONTEND HANDLING:
    - Real-time progress bar updates
    - Status badge changes color
    - Automatic redirect when completed
```

### 6. Text-to-Speech Generation
```
👤 USER ACTION: Click "Listen" button on completed transcript
    ↓
📱 FRONTEND: pages/CompletedJobsPage.jsx
    - handleListen() function
    - Audio element for playback
    ↓
🌐 API CALL: POST /tts/{job_id}
    - Authorization: Bearer {token}
    ↓
🔧 BACKEND: api/routes/tts.py
    - @router.post("/tts/{job_id}")
    - generate_tts() function
    ↓
📊 DEPENDENCIES:
    - api/services/tts_service.py
    - api/services/storage.py::save_tts_file()
    - External TTS engine (pyttsx3 or cloud service)
    ↓
🗄️ DATABASE OPERATIONS:
    - SELECT transcript_metadata WHERE job_id = ?
    - UPDATE jobs SET tts_path = ? WHERE id = ?
    ↓
🔄 BUSINESS LOGIC:
    - Load transcript text
    - Generate audio using TTS engine
    - Save audio file to storage
    ↓
📤 RESPONSE: TTSOut
    - path: "/static/tts/{job_id}.mp3"
    ↓
📱 FRONTEND HANDLING:
    - new Audio() object created
    - audio.play() called
    - Audio streams to user
```

---

## 🔧 **ADMIN FUNCTIONS FLOWS**

### 7. System Statistics Dashboard
```
👤 USER ACTION: Navigate to Admin page
    ↓
📱 FRONTEND: pages/AdminPage.jsx
    - fetchStats() function (auto-refresh every 30s)
    - StatsPanel component rendering
    ↓
🌐 API CALL: GET /admin/stats
    - Authorization: Bearer {admin_token}
    ↓
🔧 BACKEND: api/routes/admin.py
    - @router.get("/admin/stats")
    - get_admin_stats() function
    - Role-based access control
    ↓
📊 DEPENDENCIES:
    - api/services/storage.py::get_storage_info()
    - api/models.py (all models for counting)
    - psutil for system metrics
    ↓
🗄️ DATABASE OPERATIONS:
    - SELECT COUNT(*) FROM jobs GROUP BY status
    - SELECT COUNT(*) FROM users
    - File system size calculations
    ↓
🔄 BUSINESS LOGIC:
    - Calculate disk usage
    - Count jobs by status
    - System resource monitoring
    ↓
📤 RESPONSE: AdminStatsOut
    - total_jobs, completed_jobs, failed_jobs
    - total_users, disk_usage, uptime
    ↓
📱 FRONTEND HANDLING:
    - StatsPanel displays metrics
    - Auto-refresh every 30 seconds
    - Visual charts and counters
```

### 8. System Reset Operation
```
👤 USER ACTION: Click "Reset All Data" button with confirmation
    ↓
📱 FRONTEND: pages/AdminPage.jsx
    - handleReset() function
    - window.confirm() dialog
    ↓
🌐 API CALL: POST /admin/reset
    - Authorization: Bearer {admin_token}
    ↓
🔧 BACKEND: api/routes/admin.py
    - @router.post("/admin/reset")
    - reset_application() function
    - Admin role verification
    ↓
📊 DEPENDENCIES:
    - api/services/storage.py::cleanup_files()
    - api/orm_bootstrap.py::SessionLocal
    - api/services/users.py::ensure_default_admin()
    ↓
🗄️ DATABASE OPERATIONS:
    - DELETE FROM transcript_metadata
    - DELETE FROM jobs  
    - DELETE FROM user_settings
    - Reset sequences/auto-increment
    ↓
🔄 BUSINESS LOGIC:
    - Remove all files from uploads/
    - Remove all files from transcripts/
    - Recreate default admin user
    - Reset application state
    ↓
📤 RESPONSE: StatusOut
    - status: "success"
    - message: "Application reset successfully"
    ↓
📱 FRONTEND HANDLING:
    - Success toast notification
    - Page refresh to show clean state
```

---

## 👥 **USER MANAGEMENT FLOWS**

### 9. Role Management Process
```
👤 USER ACTION: Admin clicks "Make Admin/User" button
    ↓
📱 FRONTEND: pages/SettingsPage.jsx
    - toggleRole() function
    - Role toggle logic
    ↓
🌐 API CALL: PUT /users/{user_id}
    - Authorization: Bearer {admin_token}
    - Body: {role: "admin"} or {role: "user"}
    ↓
🔧 BACKEND: api/routes/users.py
    - @router.put("/{user_id}")
    - update_user() function
    - Admin role verification
    ↓
📊 DEPENDENCIES:
    - api/services/users.py::update_user()
    - api/models.py::User
    ↓
🗄️ DATABASE OPERATIONS:
    - UPDATE users SET role = ? WHERE id = ?
    ↓
📤 RESPONSE: UserOut
    - Updated user object with new role
    ↓
📱 FRONTEND HANDLING:
    - Success toast notification
    - loadUsers() called to refresh list
    - Button text updates
```

### 10. User Settings Management
```
👤 USER ACTION: Change model preference in upload page
    ↓
📱 FRONTEND: pages/UploadPage.jsx
    - useEffect hook on model change
    - Automatic save to user settings
    ↓
🌐 API CALL: POST /user/settings
    - Authorization: Bearer {token}
    - Body: {default_model: "small"}
    ↓
🔧 BACKEND: api/routes/user_settings.py
    - @router.post("/settings")
    - update_user_settings() function
    ↓
📊 DEPENDENCIES:
    - api/models.py::UserSetting
    - api/services/users.py::get_current_user()
    ↓
🗄️ DATABASE OPERATIONS:
    - INSERT INTO user_settings (user_id, key, value) 
      ON CONFLICT UPDATE value
    ↓
📤 RESPONSE: UserSettingsOut
    - default_model: "small"
    ↓
📱 FRONTEND HANDLING:
    - Setting persisted for future sessions
    - Model dropdown shows saved preference
```

---

## 📂 **FILE MANAGEMENT FLOWS**

### 11. File Browser Navigation
```
👤 USER ACTION: Select folder and navigate directory structure
    ↓
📱 FRONTEND: components/FileBrowser.jsx
    - load() function
    - Breadcrumb navigation
    ↓
🌐 API CALL: GET /admin/browse?folder=logs&path=system/2024
    - Authorization: Bearer {admin_token}
    ↓
🔧 BACKEND: api/routes/admin.py
    - @router.get("/browse")
    - browse_files() function
    ↓
📊 DEPENDENCIES:
    - api/services/storage.py::list_files()
    - api/paths.py (UPLOAD_DIR, TRANSCRIPTS_DIR, etc.)
    - pathlib.Path for file operations
    ↓
🗄️ FILE SYSTEM OPERATIONS:
    - os.listdir() on target directory
    - File stat() for size/dates
    - Permission checks
    ↓
🔄 BUSINESS LOGIC:
    - Separate files from directories
    - Sort by name/date
    - Calculate file sizes
    ↓
📤 RESPONSE: BrowseOut
    - directories: ["subdir1", "subdir2"]
    - files: [{name, size, modified}, ...]
    ↓
📱 FRONTEND HANDLING:
    - Directory list rendered
    - File list with download/delete buttons
    - Breadcrumb navigation updated
```

### 12. File Deletion Process
```
👤 USER ACTION: Click delete button on file with confirmation
    ↓
📱 FRONTEND: components/FileBrowser.jsx
    - handleDelete() function
    - window.confirm() dialog
    ↓
🌐 API CALL: DELETE /admin/files
    - Authorization: Bearer {admin_token}
    - Body: {folder: "logs", filename: "system.log"}
    ↓
🔧 BACKEND: api/routes/admin.py
    - @router.delete("/files")
    - delete_file() function
    ↓
📊 DEPENDENCIES:
    - api/services/storage.py::delete_file()
    - pathlib.Path
    - Security path validation
    ↓
🗄️ FILE SYSTEM OPERATIONS:
    - Path validation (prevent directory traversal)
    - File existence check
    - os.remove() or Path.unlink()
    ↓
📤 RESPONSE: StatusOut
    - status: "success"
    ↓
📱 FRONTEND HANDLING:
    - Success toast notification
    - load() called to refresh directory listing
    - File removed from display
```

---

## 🔍 **JOB SEARCH & FILTERING FLOWS**

### 13. Job Search Process
```
👤 USER ACTION: Type in search box on completed jobs page
    ↓
📱 FRONTEND: pages/CompletedJobsPage.jsx
    - search state change
    - useEffect hook triggers fetchJobs()
    ↓
🌐 API CALL: GET /jobs?search=keyword&status=completed
    - Authorization: Bearer {token}
    ↓
🔧 BACKEND: api/routes/jobs.py
    - @router.get("/jobs")
    - list_jobs() function with filters
    ↓
📊 DEPENDENCIES:
    - api/models.py::Job
    - SQLAlchemy query building
    ↓
🗄️ DATABASE OPERATIONS:
    - SELECT * FROM jobs 
      WHERE (original_filename ILIKE %keyword% OR transcript_text ILIKE %keyword%)
      AND status = 'completed'
      AND user_id = ?
    ↓
📤 RESPONSE: List[JobListOut]
    - Filtered job list
    ↓
📱 FRONTEND HANDLING:
    - Redux store updated
    - Job table re-rendered with filtered results
    - Search term highlighted
```

---

## 🔄 **AUTOMATED TESTING APPROACH**

### Function Chain Testing Strategy
Instead of manually clicking buttons, we can test each complete chain:

1. **Mock User Input**: Simulate form data and user selections
2. **API Testing**: Direct HTTP calls to endpoints with test data
3. **Database Verification**: Check that expected database changes occur
4. **File System Verification**: Confirm files are created/deleted as expected
5. **State Verification**: Ensure frontend state updates correctly

### Test Categories:
- **Authentication Tests**: Login, logout, password change
- **Upload Workflow Tests**: File validation, job creation, processing
- **Admin Function Tests**: System stats, reset, file management
- **Real-time Tests**: WebSocket connections, progress updates
- **Error Handling Tests**: Invalid inputs, permission errors

This approach allows us to verify every function in the application works correctly without manual interaction, giving us confidence in the complete system functionality.
