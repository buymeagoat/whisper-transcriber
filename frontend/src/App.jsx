import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import LoadingSpinner from './components/LoadingSpinner'
import ErrorBoundary from './components/ErrorBoundary'
import DevTools from './components/DevTools'
import ProtectedRoute from './components/ProtectedRoute'

// Public pages
import LoginPage from './pages/auth/LoginPage'
import RegisterPage from './pages/auth/RegisterPage'
import LandingPage from './pages/LandingPage'

// Protected user pages
import Dashboard from './pages/user/Dashboard'
import TranscribePage from './pages/user/TranscribePage'
import JobsPage from './pages/user/JobsPage'
import SettingsPage from './pages/user/SettingsPage'

// Admin pages
import AdminPanel from './pages/AdminPanel'
// TODO: These components will be implemented in future tasks
// import UserManagement from './pages/admin/UserManagement'
// import SystemMonitoring from './pages/admin/SystemMonitoring'
// import AuditLogs from './pages/admin/AuditLogs'

// The ProtectedRoute component is now imported from ./components/ProtectedRoute

function App() {
  const { user, loading } = useAuth()

  if (loading) {
    return <LoadingSpinner />
  }

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Routes>
          {/* Public routes */}
          <Route path="/" element={user ? <Navigate to="/dashboard" replace /> : <LandingPage />} />
          <Route path="/login" element={user ? <Navigate to="/dashboard" replace /> : <LoginPage />} />
          <Route path="/register" element={user ? <Navigate to="/dashboard" replace /> : <RegisterPage />} />
          
          {/* Protected user routes */}
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <Layout>
                <Dashboard />
              </Layout>
            </ProtectedRoute>
          } />
          
          <Route path="/transcribe" element={
            <ProtectedRoute>
              <Layout>
                <TranscribePage />
              </Layout>
            </ProtectedRoute>
          } />
          
          <Route path="/jobs" element={
            <ProtectedRoute>
              <Layout>
                <JobsPage />
              </Layout>
            </ProtectedRoute>
          } />
          
          <Route path="/settings" element={
            <ProtectedRoute>
              <Layout>
                <SettingsPage />
              </Layout>
            </ProtectedRoute>
          } />
          
          {/* Admin routes */}
          <Route path="/admin" element={
            <ProtectedRoute adminRequired>
              <Layout>
                <AdminPanel />
              </Layout>
            </ProtectedRoute>
          } />
          
          {/* TODO: Implement individual admin pages in future tasks
          <Route path="/admin/users" element={
            <ProtectedRoute adminRequired>
              <Layout>
                <UserManagement />
              </Layout>
            </ProtectedRoute>
          } />
          
          <Route path="/admin/monitoring" element={
            <ProtectedRoute adminRequired>
              <Layout>
                <SystemMonitoring />
              </Layout>
            </ProtectedRoute>
          } />
          
          <Route path="/admin/audit" element={
            <ProtectedRoute adminRequired>
              <Layout>
                <AuditLogs />
              </Layout>
            </ProtectedRoute>
          } />
          */}
          
          {/* Fallback route */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        
        {/* Development Tools */}
        <DevTools />
      </div>
    </ErrorBoundary>
  )
}

export default App
