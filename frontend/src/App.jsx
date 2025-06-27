import { useEffect, useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ROUTES } from "./routes";
import UploadPage from "./pages/UploadPage";
import CompletedJobsPage from "./pages/CompletedJobsPage";
import AdminPage from "./pages/AdminPage";
import SettingsPage from "./pages/SettingsPage";
import ActiveJobsPage from "./pages/ActiveJobsPage";
import TranscriptViewPage from "./pages/TranscriptViewPage";
import JobStatusPage from "./pages/JobStatusPage";
import FailedJobsPage from "./pages/FailedJobsPage";
import JobProgressPage from "./pages/JobProgressPage";
import LoginPage from "./pages/LoginPage";
import { AuthContext } from "./context/AuthContext";
import { useApi } from "./api";
import Layout from "./components/Layout";

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
        <Routes>
          <Route path="/" element={<Navigate to={isAuthenticated ? ROUTES.UPLOAD : ROUTES.LOGIN} replace />} />
          <Route path={ROUTES.LOGIN} element={<LoginPage />} />
          <Route path={ROUTES.UPLOAD} element={isAuthenticated ? <UploadPage /> : <Navigate to={ROUTES.LOGIN} replace />} />
          <Route path={ROUTES.ACTIVE} element={isAuthenticated ? <ActiveJobsPage /> : <Navigate to={ROUTES.LOGIN} replace />} />
          <Route path={ROUTES.COMPLETED} element={isAuthenticated ? <CompletedJobsPage /> : <Navigate to={ROUTES.LOGIN} replace />} />
          <Route path={ROUTES.ADMIN} element={isAuthenticated ? <AdminPage /> : <Navigate to={ROUTES.LOGIN} replace />} />
          <Route path={ROUTES.SETTINGS} element={isAuthenticated && role === "admin" ? <SettingsPage /> : <Navigate to={ROUTES.LOGIN} replace />} />
          <Route path={ROUTES.TRANSCRIPT_VIEW} element={isAuthenticated ? <TranscriptViewPage /> : <Navigate to={ROUTES.LOGIN} replace />} />
          <Route path={ROUTES.STATUS} element={isAuthenticated ? <JobStatusPage /> : <Navigate to={ROUTES.LOGIN} replace />} />
          <Route path={ROUTES.FAILED} element={isAuthenticated ? <FailedJobsPage /> : <Navigate to={ROUTES.LOGIN} replace />} />
          <Route path={ROUTES.PROGRESS} element={isAuthenticated ? <JobProgressPage /> : <Navigate to={ROUTES.LOGIN} replace />} />
          <Route path="*" element={<div style={{ color: "red" }}>404 — Page Not Found</div>} />
        </Routes>
      </Layout>
    </Router>
  );
}

