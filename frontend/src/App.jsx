import { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import CompletedJobsPage from "./CompletedJobsPage";
import AdminLogsPage from "./AdminLogsPage";
import ActiveJobsPage from "./ActiveJobsPage";
import TranscriptViewPage from "./TranscriptViewPage";

function UploadPage() {
  const [file, setFile] = useState(null);
  const [model, setModel] = useState("tiny");
  const [status, setStatus] = useState(null);

  const handleUpload = async () => {
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    formData.append("model", model);

    setStatus("Uploading and transcribing...");
    try {
      const res = await fetch("/jobs", { method: "POST", body: formData });
      const data = await res.json();
      if (res.ok) {
        setStatus(`✅ Job started: ${data.job_id}`);
      } else {
        setStatus(`❌ Error: ${data.error}`);
      }
    } catch (err) {
      setStatus(`❌ Network error`);
    }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold">Upload Audio File for Transcription</h2>

      <input type="file" onChange={(e) => setFile(e.target.files[0])} />

      <div>
        <label className="block mb-1">Select Model</label>
        <select
          className="text-black p-1"
          value={model}
          onChange={(e) => setModel(e.target.value)}
        >
          <option value="tiny">tiny</option>
          <option value="base">base</option>
          <option value="small">small</option>
          <option value="medium">medium</option>
          <option value="large">large</option>
        </select>
      </div>

      <button
        onClick={handleUpload}
        className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded"
      >
        Transcribe
      </button>

      {status && <p>{status}</p>}
    </div>
  );
}

function AdminPage() {
  const [logs, setLogs] = useState("");

  useEffect(() => {
    fetch("/log/access")
      .then(res => res.text())
      .then(data => setLogs(data))
      .catch(() => setLogs("Unable to load logs."));
  }, []);

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-xl font-bold">🛠️ Admin Logs</h2>
      <pre className="bg-zinc-800 p-4 rounded overflow-x-auto whitespace-pre-wrap text-sm border border-zinc-700">
        {logs || "No logs available."}
      </pre>
    </div>
  );
}

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