import { useEffect } from 'react';
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

export default function App() {
  useEffect(() => {
    fetch('/log_event', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ event: 'frontend_loaded', timestamp: new Date().toISOString() })
    }).catch(() => {});
  }, []);

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
        </nav>

        <main style={{ padding: "1.5rem" }}>
          {/* Removed Tailwind test block */}

          <Routes>
            <Route path="/" element={<Navigate to={ROUTES.UPLOAD} replace />} />
            <Route path={ROUTES.UPLOAD} element={<UploadPage />} />
            <Route path={ROUTES.ACTIVE} element={<ActiveJobsPage />} />
            <Route path={ROUTES.COMPLETED} element={<CompletedJobsPage />} />
            <Route path={ROUTES.ADMIN} element={<AdminPage />} />
            <Route path={ROUTES.TRANSCRIPT_VIEW} element={<TranscriptViewPage />} />
            <Route path={ROUTES.STATUS} element={<JobStatusPage />} />
            <Route path="*" element={<div style={{ color: "red" }}>404 — Page Not Found</div>} />
            <Route path={ROUTES.FAILED} element={<FailedJobsPage />} />
            <Route path={ROUTES.PROGRESS} element={<JobProgressPage />} />
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
