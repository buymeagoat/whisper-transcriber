import { useEffect, useContext, Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ROUTES } from "./routes";
import { AuthContext } from "./context/AuthContext";
import { useApi } from "./api";
import Layout from "./components/Layout";

// Lazy load pages for code splitting
const UploadPage = lazy(() => import("./pages/UploadPage"));
const CompletedJobsPage = lazy(() => import("./pages/CompletedJobsPage"));
const AdminPage = lazy(() => import("./pages/AdminPage"));
const SettingsPage = lazy(() => import("./pages/SettingsPage"));
const ActiveJobsPage = lazy(() => import("./pages/ActiveJobsPage"));
const TranscriptViewPage = lazy(() => import("./pages/TranscriptViewPage"));
const JobStatusPage = lazy(() => import("./pages/JobStatusPage"));
const FailedJobsPage = lazy(() => import("./pages/FailedJobsPage"));
const JobProgressPage = lazy(() => import("./pages/JobProgressPage"));
const LoginPage = lazy(() => import("./pages/LoginPage"));
const ChangePasswordPage = lazy(() => import("./pages/ChangePasswordPage"));
const FileBrowserPage = lazy(() => import("./pages/FileBrowserPage"));

// Loading component for Suspense fallback
const PageLoader = () => (
  <div style={{
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '200px',
    fontSize: '1.1rem',
    color: '#6b7280'
  }}>
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '0.75rem'
    }}>
      {/* Simple loading spinner */}
      <div style={{
        width: '20px',
        height: '20px',
        border: '2px solid #e5e7eb',
        borderTopColor: '#3b82f6',
        borderRadius: '50%',
        animation: 'spin 1s linear infinite'
      }}></div>
      Loading...
    </div>
  </div>
);

export default function App() {
  const api = useApi();
  useEffect(() => {
    api.post('/log_event', {
      event: 'frontend_loaded',
      timestamp: new Date().toISOString()
    }).catch(() => {});
  }, []);

  const { isAuthenticated, role } = useContext(AuthContext);

  return (
    <Router>
      <Layout>
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route path="/" element={<Navigate to={isAuthenticated ? ROUTES.UPLOAD : ROUTES.LOGIN} replace />} />
            <Route path={ROUTES.LOGIN} element={<LoginPage />} />
            <Route path={ROUTES.UPLOAD} element={isAuthenticated ? <UploadPage /> : <Navigate to={ROUTES.LOGIN} replace />} />
            <Route path={ROUTES.ACTIVE} element={isAuthenticated ? <ActiveJobsPage /> : <Navigate to={ROUTES.LOGIN} replace />} />
            <Route path={ROUTES.COMPLETED} element={isAuthenticated ? <CompletedJobsPage /> : <Navigate to={ROUTES.LOGIN} replace />} />
            <Route path={ROUTES.ADMIN} element={isAuthenticated ? <AdminPage /> : <Navigate to={ROUTES.LOGIN} replace />} />
            <Route path={ROUTES.FILE_BROWSER} element={isAuthenticated ? <FileBrowserPage /> : <Navigate to={ROUTES.LOGIN} replace />} />
            <Route path={ROUTES.SETTINGS} element={isAuthenticated && role === "admin" ? <SettingsPage /> : <Navigate to={ROUTES.LOGIN} replace />} />
            <Route path={ROUTES.CHANGE_PASSWORD} element={isAuthenticated ? <ChangePasswordPage /> : <Navigate to={ROUTES.LOGIN} replace />} />
            <Route path={ROUTES.TRANSCRIPT_VIEW} element={isAuthenticated ? <TranscriptViewPage /> : <Navigate to={ROUTES.LOGIN} replace />} />
            <Route path={ROUTES.STATUS} element={isAuthenticated ? <JobStatusPage /> : <Navigate to={ROUTES.LOGIN} replace />} />
            <Route path={ROUTES.FAILED} element={isAuthenticated ? <FailedJobsPage /> : <Navigate to={ROUTES.LOGIN} replace />} />
            <Route path={ROUTES.PROGRESS} element={isAuthenticated ? <JobProgressPage /> : <Navigate to={ROUTES.LOGIN} replace />} />
            <Route path="*" element={<div style={{ color: "red" }}>404 — Page Not Found</div>} />
          </Routes>
        </Suspense>
      </Layout>
    </Router>
  );
}

