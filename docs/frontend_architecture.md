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
- `src/pages/AdminPanel.jsx` - Main administrative interface with tabbed navigation
- `src/components/SystemHealth.jsx` - Real-time system health monitoring component
- **Features Implemented (T007)**:
  - System health dashboard with server status, database connectivity, queue monitoring
  - Live statistics display (job counts, app version, configuration details)
  - Real-time updates with 30-second auto-refresh
  - Admin-only access protection via ProtectedRoute component
  - Responsive design with dark mode support
  - Integration with backend `/admin/health` and `/admin/stats` endpoints

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
