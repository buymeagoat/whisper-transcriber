import { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import UploadPage from "./pages/UploadPage";
import CompletedJobsPage from "./pages/CompletedJobsPage";
import AdminLogsPage from "./pages/AdminLogsPage";
import ActiveJobsPage from "./pages/ActiveJobsPage";
import TranscriptViewPage from "./pages/TranscriptViewPage";

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
      <div className="min-h-screen bg-zinc-900 text-white">
        <nav className="bg-zinc-800 p-4 flex space-x-4 border-b border-zinc-700">
          <Link className="hover:underline" to="/upload">Upload</Link>
          <Link className="hover:underline" to="/active">Active Jobs</Link>
          <Link className="hover:underline" to="/completed">Completed Jobs</Link>
          <Link className="hover:underline" to="/admin">Admin</Link>
        </nav>

        <main className="p-6">
          <Routes>
            <Route path="/" element={<Navigate to="/upload" replace />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/active" element={<ActiveJobsPage />} />
            <Route path="/completed" element={<CompletedJobsPage />} />
            <Route path="/admin" element={<AdminLogsPage />} />
            <Route path="/transcript/:jobId/view" element={<TranscriptViewPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}
