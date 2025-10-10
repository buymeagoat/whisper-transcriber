# Whisper Transcriber Frontend - Complete Function Test Map

## Overview
This document maps every frontend function to specific user actions for methodical testing. The application has 12 main pages and multiple interactive components.

---

## 🔐 **AUTHENTICATION FUNCTIONS**

### Login Page (`/login`)
**User Actions to Test:**
1. **Login with valid credentials**
   - Enter username and password
   - Click "Login" button
   - Verify redirect to upload page

2. **Login with invalid credentials**
   - Enter wrong username/password
   - Click "Login" button
   - Verify error message appears

3. **First-time login (password change required)**
   - Login with default admin credentials
   - Verify redirect to change password page

### Change Password Page (`/change-password`)
**User Actions to Test:**
1. **Change password successfully**
   - Enter current password
   - Enter new password
   - Confirm new password
   - Click submit

2. **Password validation errors**
   - Try mismatched passwords
   - Try weak passwords
   - Verify error messages

---

## 📁 **FILE UPLOAD FUNCTIONS**

### Upload Page (`/upload`) - Primary Function
**User Actions to Test:**

#### File Selection & Validation
1. **Select single audio file**
   - Click file input
   - Choose .wav, .mp3, or .m4a file
   - Verify file appears in upload list

2. **Select multiple audio files (up to 10)**
   - Select multiple files at once
   - Verify all files appear in list
   - Check file limit enforcement

3. **Upload invalid file types**
   - Try to upload .txt, .jpg, etc.
   - Verify error message: "❌ Unsupported format"

4. **Upload oversized files (>2GB)**
   - Try large files
   - Verify error message: "❌ File too large"

5. **Remove files from upload list**
   - Click "✕" button on file cards
   - Verify file is removed

#### Model Selection
6. **Change transcription model**
   - Select from dropdown: tiny, base, small, medium, large
   - Verify selection persists (saved to user settings)

#### Job Submission
7. **Upload all files**
   - Click "Upload All" button
   - Verify upload progress messages
   - Check job creation confirmation

8. **Start new job after completion**
   - Click "Start New Job" button
   - Verify form resets

---

## 📊 **JOB MANAGEMENT FUNCTIONS**

### Active Jobs Page (`/active`) - Real-time Monitoring
**User Actions to Test:**
1. **View active job list**
   - Navigate to active jobs
   - Verify auto-refresh every 30 seconds
   - Check job status badges

2. **Monitor job progress**
   - Click "View Progress" button
   - Verify opens progress page in new tab
   - Check real-time updates

### Completed Jobs Page (`/completed`) - Results Management
**User Actions to Test:**

#### Job Search & Filtering
1. **Search completed jobs**
   - Type in search box
   - Verify filtered results
   - Test keyword search

#### Job Actions
2. **View transcript**
   - Click "View" button
   - Verify opens transcript in new tab

3. **Download transcript**
   - Click "Download" button
   - Verify file download starts
   - Test different formats (txt, json, etc.)

4. **Listen to TTS audio**
   - Click "Listen" button
   - Verify audio generation and playback

5. **Delete completed job**
   - Click "Delete" button
   - Verify confirmation dialog
   - Check job removal from list

### Failed Jobs Page (`/failed`) - Error Handling
**User Actions to Test:**
1. **View failed job details**
   - Check error messages
   - Verify failure reasons

2. **Retry failed jobs**
   - Click retry options if available
   - Monitor re-processing

---

## 🔧 **ADMIN FUNCTIONS**

### Admin Dashboard (`/admin`) - System Management
**User Actions to Test:**

#### Server Statistics
1. **View system stats**
   - Check server statistics panel
   - Verify auto-refresh every 30 seconds
   - Monitor resource usage

#### System Control
2. **Server restart**
   - Click "Restart Server" button
   - Verify confirmation dialog
   - Check system restart

3. **Server shutdown**
   - Click "Shutdown Server" button
   - Verify shutdown confirmation

4. **Reset all data**
   - Click "Reset All Data" button
   - Verify warning and confirmation
   - Check data cleanup

#### Configuration Management
5. **Cleanup settings**
   - Toggle cleanup enabled/disabled
   - Change cleanup days setting
   - Click "Save Cleanup Settings"

6. **Concurrency settings**
   - Adjust max concurrent jobs
   - Click "Save Concurrency Settings"
   - Verify setting persistence

#### File Management
7. **Download all files**
   - Click "Download All Files" button
   - Verify archive generation
   - Check download starts

#### System Monitoring
8. **View real-time system logs**
   - Check WebSocket log updates
   - Verify timestamps
   - Monitor log streaming

### File Browser Page (`/admin/files`) - File System Access
**User Actions to Test:**

#### Navigation
1. **Browse different folders**
   - Select "logs", "uploads", "transcripts" from dropdown
   - Navigate folder hierarchy
   - Use breadcrumb navigation

2. **File operations**
   - View files in browser
   - Download individual files
   - Delete files (with confirmation)

### Settings Page (`/settings`) - User Management
**User Actions to Test:**
1. **View user list**
   - Check all registered users
   - View user roles and creation dates

2. **Change user roles**
   - Click "Make Admin" / "Make User" buttons
   - Verify role changes
   - Check permission updates

---

## 📋 **JOB DETAILS FUNCTIONS**

### Job Progress Page (`/progress/:jobId`) - Real-time Tracking
**User Actions to Test:**
1. **Monitor job progress**
   - View progress percentage
   - Check status updates
   - Verify WebSocket real-time updates

2. **View processing stages**
   - Monitor: queued → processing → enriching → completed
   - Check time stamps
   - Verify status transitions

### Job Status Page (`/status/:jobId`) - Job Information
**User Actions to Test:**
1. **View job metadata**
   - Check file information
   - View model used
   - Check timestamps

2. **Access job actions**
   - Download results
   - View transcripts
   - Check error details (if failed)

### Transcript View Page (`/transcript/:jobId/view`) - Content Display
**User Actions to Test:**
1. **View formatted transcript**
   - Check text formatting
   - Verify timestamp accuracy
   - Test readability

2. **Navigate transcript content**
   - Scroll through long transcripts
   - Check text search (if available)
   - Verify proper formatting

---

## 🎛️ **NAVIGATION & LAYOUT FUNCTIONS**

### Main Navigation (Sidebar)
**User Actions to Test:**
1. **Navigate between pages**
   - Click each navigation link
   - Verify page loads correctly
   - Check active page highlighting

2. **Role-based navigation**
   - Test as regular user vs admin
   - Verify Settings link only shows for admins
   - Check permission enforcement

### Header Functions
**User Actions to Test:**
1. **Logout**
   - Click logout button
   - Verify session termination
   - Check redirect to login

2. **Application branding**
   - Verify header displays correctly
   - Check responsive design

---

## 🔔 **NOTIFICATION FUNCTIONS**

### Toast Notifications
**User Actions to Test:**
1. **Success notifications**
   - Perform successful actions
   - Verify green success toasts appear
   - Check auto-dismiss timing

2. **Error notifications**
   - Trigger error conditions
   - Verify red error toasts appear
   - Check error message clarity

3. **Info notifications**
   - Check informational messages
   - Verify proper styling
   - Test persistence

---

## 🔌 **REAL-TIME FUNCTIONS**

### WebSocket Connections
**User Actions to Test:**
1. **Job progress updates**
   - Start transcription job
   - Monitor real-time progress updates
   - Verify connection stability

2. **System log streaming**
   - View admin system logs
   - Check real-time log streaming
   - Test connection reconnection

3. **Auto-refresh functions**
   - Verify active jobs auto-refresh (30s)
   - Check admin stats auto-refresh (30s)
   - Monitor background updates

---

## 🎯 **SYSTEMATIC TESTING APPROACH**

### Phase 1: Authentication Flow
1. Test login/logout cycle
2. Test password change flow
3. Verify role-based access

### Phase 2: Core Workflow
1. Upload audio files
2. Monitor active jobs
3. View completed results
4. Download/listen to transcripts

### Phase 3: Admin Functions
1. System monitoring
2. Configuration management
3. File management
4. User management

### Phase 4: Edge Cases
1. Error handling
2. File validation
3. Network issues
4. Permission boundaries

### Phase 5: Real-time Features
1. WebSocket functionality
2. Auto-refresh behaviors
3. Progress monitoring

---

## 🧪 **TEST SCENARIOS BY USER TYPE**

### Regular User Testing
- Upload and transcription workflow
- Job monitoring and results access
- Personal settings management

### Admin User Testing
- All regular user functions
- System administration
- User management
- File system access
- Server control

---

## ✅ **FUNCTIONAL COMPLETENESS CHECKLIST**

Based on the code analysis, the frontend provides:

- ✅ Complete authentication system
- ✅ File upload with validation
- ✅ Real-time job monitoring
- ✅ Multiple download formats
- ✅ TTS audio generation
- ✅ Admin system control
- ✅ File browser functionality
- ✅ User role management
- ✅ WebSocket real-time updates
- ✅ Responsive design
- ✅ Error handling and notifications
- ✅ Search and filtering
- ✅ Auto-refresh capabilities

**Total Functions Mapped: 50+ user actions across 12 pages**

This comprehensive map enables systematic testing of every frontend function through specific user actions.
