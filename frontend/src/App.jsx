import { useEffect, useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import { ROUTES } from "./routes";
import UploadPage from "./pages/UploadPage";
import CompletedJobsPage from "./pages/CompletedJobsPage";
import AdminPage from "./pages/AdminPage";
import ActiveJobsPage from "./pages/ActiveJobsPage";
import TranscriptViewPage from "./pages/TranscriptViewPage";
import JobStatusPage from "./pages/JobStatusPage";
import FailedJobsPage from "./pages/FailedJobsPage";
import JobProgressPage from "./pages/JobProgressPage";
import LoginPage from "./pages/LoginPage";
import { AuthContext } from "./context/AuthContext";
import { useApi } from "./api";

export default function App() {
  const api = useApi();
  useEffect(() => {
    api.post('/log_event', {
      event: 'frontend_loaded',
      timestamp: new Date().toISOString()
    }).catch(() => {});
  }, []);

  const { token, logout, isAuthenticated } = useContext(AuthContext);
  const handleLogout = () => {
    logout();
    window.location.href = ROUTES.LOGIN;
  };

  return (
    <Router>
      <div style={{ minHeight: "100vh", backgroundColor: "#18181b", color: "white" }}>
        <nav style={{
          backgroundColor: "#27272a",
          padding: "1rem",
          display: "flex",
          gap: "1rem",
          borderBottom: "1px solid #3f3f46"
        }}>
          <Link to={ROUTES.UPLOAD} style={linkStyle}>Upload</Link>
          <Link to={ROUTES.ACTIVE} style={linkStyle}>Active Jobs</Link>
          <Link to={ROUTES.COMPLETED} style={linkStyle}>Completed Jobs</Link>
          <Link to={ROUTES.FAILED} style={linkStyle}>Failed Jobs</Link>
          <Link to={ROUTES.ADMIN} style={linkStyle}>Admin</Link>
          {isAuthenticated ? (
            <button onClick={handleLogout} style={linkStyle}>Logout</button>
          ) : (
            <Link to={ROUTES.LOGIN} style={linkStyle}>Login</Link>
          )}
        </nav>

        <main style={{ padding: "1.5rem" }}>
          {/* Removed Tailwind test block */}

          <Routes>
            <Route path="/" element={<Navigate to={isAuthenticated ? ROUTES.UPLOAD : ROUTES.LOGIN} replace />} />
            <Route path={ROUTES.LOGIN} element={<LoginPage />} />
            <Route path={ROUTES.UPLOAD} element={isAuthenticated ? <UploadPage /> : <Navigate to={ROUTES.LOGIN} replace />} />
            <Route path={ROUTES.ACTIVE} element={isAuthenticated ? <ActiveJobsPage /> : <Navigate to={ROUTES.LOGIN} replace />} />
            <Route path={ROUTES.COMPLETED} element={isAuthenticated ? <CompletedJobsPage /> : <Navigate to={ROUTES.LOGIN} replace />} />
            <Route path={ROUTES.ADMIN} element={isAuthenticated ? <AdminPage /> : <Navigate to={ROUTES.LOGIN} replace />} />
            <Route path={ROUTES.TRANSCRIPT_VIEW} element={isAuthenticated ? <TranscriptViewPage /> : <Navigate to={ROUTES.LOGIN} replace />} />
            <Route path={ROUTES.STATUS} element={isAuthenticated ? <JobStatusPage /> : <Navigate to={ROUTES.LOGIN} replace />} />
            <Route path={ROUTES.FAILED} element={isAuthenticated ? <FailedJobsPage /> : <Navigate to={ROUTES.LOGIN} replace />} />
            <Route path={ROUTES.PROGRESS} element={isAuthenticated ? <JobProgressPage /> : <Navigate to={ROUTES.LOGIN} replace />} />
            <Route path="*" element={<div style={{ color: "red" }}>404 — Page Not Found</div>} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

const linkStyle = {
  color: "white",
  textDecoration: "none",
  fontWeight: "500",
  padding: "0.25rem 0.5rem"
};
