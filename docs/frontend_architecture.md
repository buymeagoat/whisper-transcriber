# Frontend Architecture

## Overview
Modern React application with TypeScript, Vite build system, and TailwindCSS styling.

## Key Components

### Authentication
- `src/context/AuthContext.jsx` - Global authentication state management
- `src/services/authService.js` - API integration for auth endpoints
- `src/pages/auth/LoginPage.jsx` - User login interface
- `src/pages/auth/RegisterPage.jsx` - User registration interface

### Transcription Workflow
- `src/pages/user/TranscribePage.jsx` - File upload and job creation
- `src/pages/user/JobsPage.jsx` - Job management and history
- `src/components/DragDropUpload.jsx` - File upload component
- `src/components/ProgressBar.jsx` - Progress tracking

### Admin Interface
- `src/pages/admin/AdminDashboard.jsx` - System overview
- `src/pages/admin/UserManagement.jsx` - User administration
- `src/pages/admin/SystemMonitoring.jsx` - System health monitoring
- `src/pages/admin/AuditLogs.jsx` - Security audit trail

### Services
- `src/services/jobsService.js` - Transcription job API integration
- `src/services/adminService.js` - Admin functionality API integration
- `src/services/apiClient.js` - Shared HTTP client configuration

## Build System
- Vite for fast development and optimized production builds
- TailwindCSS for utility-first styling
- React Router for client-side routing
- Axios for HTTP requests with interceptors

## Deployment
Production build generates optimized static assets in `dist/` directory.
