import React, { Suspense, useEffect } from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import LoadingSpinner from './components/LoadingSpinner'
import ErrorBoundary from './components/ErrorBoundary'
import DevTools from './components/DevTools'
import ProtectedRoute from './components/ProtectedRoute'
import { intelligentPreload, preloadOnIdle, preloadByRoute } from './utils/routePreloader'
import { bundleMonitor } from './utils/bundlePerformance'

// Eager-loaded components (critical for initial load)
import LandingPage from './pages/LandingPage'

// Lazy-loaded components with code splitting
const LoginPage = React.lazy(() => import('./pages/auth/LoginPage'))
const RegisterPage = React.lazy(() => import('./pages/auth/RegisterPage'))

// Protected user pages (lazy-loaded)
const Dashboard = React.lazy(() => import('./pages/user/Dashboard'))
const TranscribePage = React.lazy(() => import('./pages/user/TranscribePage'))
const JobsPage = React.lazy(() => import('./pages/user/JobsPage'))
const SettingsPage = React.lazy(() => import('./pages/user/SettingsPage'))

// T028 Frontend Implementation - New components (lazy-loaded)
const ApiKeyManagement = React.lazy(() => import('./components/ApiKeyManagement'))
const BatchUpload = React.lazy(() => import('./components/BatchUpload'))

// Admin components (lazy-loaded since they're less frequently accessed)
const AdminLayout = React.lazy(() => import('./components/admin/AdminLayout'))
const AdminDashboard = React.lazy(() => import('./pages/admin/AdminDashboard'))
const RealTimePerformanceMonitor = React.lazy(() => import('./components/admin/RealTimePerformanceMonitor'))
const SystemResourceDashboard = React.lazy(() => import('./components/admin/SystemResourceDashboard'))
const AuditLogViewer = React.lazy(() => import('./components/admin/AuditLogViewer'))
const AdminPanel = React.lazy(() => import('./pages/AdminPanel'))

// Loading fallback component
const PageLoader = () => (
  <div className="flex items-center justify-center min-h-screen">
    <LoadingSpinner size="lg" />
  </div>
)

// Suspense wrapper for lazy components
const SuspenseWrapper = ({ children }) => (
  <Suspense fallback={<PageLoader />}>
    {children}
  </Suspense>
)

function App() {
  const { user, loading } = useAuth()
  const location = useLocation()

  // Initialize performance monitoring
  useEffect(() => {
    if (import.meta.env.DEV) {
      // Log bundle performance in development
      setTimeout(() => bundleMonitor.logOptimizationResults(), 2000)
    }
  }, [])

  // Intelligent preloading based on user state and current route
  useEffect(() => {
    if (!loading) {
      // Preload components based on user authentication state
      preloadOnIdle(() => intelligentPreload(user))
      
      // Preload components based on current route
      preloadOnIdle(() => preloadByRoute(location.pathname))
    }
  }, [user, loading, location.pathname])

  if (loading) {
    return <LoadingSpinner />
  }

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Routes>
          {/* Public routes */}
          <Route path="/" element={user ? <Navigate to="/dashboard" replace /> : <LandingPage />} />
          <Route path="/login" element={
            user ? <Navigate to="/dashboard" replace /> : 
            <SuspenseWrapper><LoginPage /></SuspenseWrapper>
          } />
          <Route path="/register" element={
            user ? <Navigate to="/dashboard" replace /> : 
            <SuspenseWrapper><RegisterPage /></SuspenseWrapper>
          } />
          
          {/* Protected user routes */}
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <Layout>
                <SuspenseWrapper>
                  <Dashboard />
                </SuspenseWrapper>
              </Layout>
            </ProtectedRoute>
          } />
          
          <Route path="/transcribe" element={
            <ProtectedRoute>
              <Layout>
                <SuspenseWrapper>
                  <TranscribePage />
                </SuspenseWrapper>
              </Layout>
            </ProtectedRoute>
          } />
          
          <Route path="/jobs" element={
            <ProtectedRoute>
              <Layout>
                <SuspenseWrapper>
                  <JobsPage />
                </SuspenseWrapper>
              </Layout>
            </ProtectedRoute>
          } />
          
          <Route path="/api-keys" element={
            <ProtectedRoute>
              <Layout>
                <SuspenseWrapper>
                  <ApiKeyManagement />
                </SuspenseWrapper>
              </Layout>
            </ProtectedRoute>
          } />
          
          <Route path="/batch-upload" element={
            <ProtectedRoute>
              <Layout>
                <SuspenseWrapper>
                  <BatchUpload />
                </SuspenseWrapper>
              </Layout>
            </ProtectedRoute>
          } />
          
          <Route path="/settings" element={
            <ProtectedRoute>
              <Layout>
                <SuspenseWrapper>
                  <SettingsPage />
                </SuspenseWrapper>
              </Layout>
            </ProtectedRoute>
          } />
          
          {/* Admin routes with dedicated layout */}
          <Route path="/admin/*" element={
            <ProtectedRoute adminRequired>
              <SuspenseWrapper>
                <AdminLayout />
              </SuspenseWrapper>
            </ProtectedRoute>
          }>
            <Route index element={
              <SuspenseWrapper>
                <AdminDashboard />
              </SuspenseWrapper>
            } />
            <Route path="health" element={<div className="p-4 text-center text-gray-500">System Health - Coming Soon</div>} />
            <Route path="jobs" element={<div className="p-4 text-center text-gray-500">Job Management - Coming Soon</div>} />
            <Route path="users" element={<div className="p-4 text-center text-gray-500">User Management - Coming Soon</div>} />
            <Route path="backups" element={<div className="p-4 text-center text-gray-500">Backup Management - Coming Soon</div>} />
            <Route path="monitoring" element={
              <SuspenseWrapper>
                <RealTimePerformanceMonitor />
              </SuspenseWrapper>
            } />
            <Route path="resources" element={
              <SuspenseWrapper>
                <SystemResourceDashboard />
              </SuspenseWrapper>
            } />
            <Route path="audit" element={
              <SuspenseWrapper>
                <AuditLogViewer />
              </SuspenseWrapper>
            } />
          </Route>
          
          {/* Legacy admin route for backward compatibility */}
          <Route path="/admin-legacy" element={
            <ProtectedRoute adminRequired>
              <Layout>
                <AdminPanel />
              </Layout>
            </ProtectedRoute>
          } />
          
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
