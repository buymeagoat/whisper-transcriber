import { useEffect, useState } from "react";
import { ROUTES } from "../routes";
export default function AdminPage() {
  const [logs, setLogs] = useState([]);
  const [uploads, setUploads] = useState([]);
  const [transcripts, setTranscripts] = useState([]);
  const [error, setError] = useState(null);
  const [feedback, setFeedback] = useState(null);
  const [refreshToggle, setRefreshToggle] = useState(false);
 const API_HOST = ROUTES.API;

  const fetchFiles = async () => {
    try {
      const res = await fetch(`${API_HOST}/admin/files`);
      if (!res.ok) throw new Error();
      const raw = await res.text();
      console.log("Raw /admin/files response:", raw);

      try {
        const data = JSON.parse(raw);
        setLogs(data.logs || []);
        setUploads(data.uploads || []);
        setTranscripts(data.transcripts || []);
        setError(null);  // ✅ clear error if successful
      } catch (parseError) {
        console.error("JSON parse failed:", parseError);
        setError("Failed to parse server response.");
      }
      setError(null); // clear any old error
    } catch {
      setError("Failed to load file listings.");
    }
  };

  useEffect(() => {
    fetchFiles();
  }, [refreshToggle]);

  useEffect(() => {
    if (feedback) {
      const timeout = setTimeout(() => setFeedback(null), 5000);
      return () => clearTimeout(timeout);
    }
  }, [feedback]);

  const handleDelete = async (dir, filename) => {
    const confirmed = window.confirm(`Delete ${filename} from ${dir}?`);
    if (!confirmed) return;
    try {
      const res = await fetch(`${API_HOST}/admin/files`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ folder: dir, filename }),
      });
      if (!res.ok) throw new Error();
      setFeedback(`Deleted ${filename} from ${dir}.`);
      setRefreshToggle(prev => !prev);
    } catch {
      setFeedback(`Failed to delete ${filename} from ${dir}.`);
    }
  };

  const handleReset = async () => {
    const confirmed = window.confirm(
      "This will erase ALL jobs, uploads, logs, and transcripts. Continue?"
    );
    if (!confirmed) return;
    try {
      const res = await fetch(`${API_HOST}/admin/reset`, { method: "POST" });
      if (!res.ok) throw new Error();
      setFeedback("System reset complete.");
      setRefreshToggle(prev => !prev);
    } catch {
      setFeedback("Reset failed.");
    }
  };

  const handleDownloadAll = () => {
    window.open(`${API_HOST}/admin/download-all`);
  };

  const renderFileList = (title, list, dir) => (
    <div style={{ marginBottom: "2rem" }}>
      <h3 style={{ fontSize: "1.125rem", marginBottom: "0.5rem" }}>{title}</h3>
      {list.length === 0 ? (
        <p style={{ color: "#a1a1aa" }}>No files in {dir}/</p>
      ) : (
        <ul style={{ listStyle: "none", paddingLeft: 0 }}>
          {list.map((name) => (
            <li key={`${dir}-${name}`} style={{ marginBottom: "0.25rem" }}>
              {name}
              <a
                href={
                  dir === "logs"
                    ? `${API_HOST}/logs/${encodeURIComponent(name)}`
                    : dir === "transcripts"
                      ? `${API_HOST}/transcript/${encodeURIComponent(name.split("/")[0])}/view`
                      : `${API_HOST}/${dir}/${encodeURIComponent(name)}`
                }
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  marginLeft: "1rem",
                  backgroundColor: "#10b981", // green
                  color: "white",
                  border: "none",
                  padding: "0.25rem 0.5rem",
                  borderRadius: "0.25rem",
                  textDecoration: "none",
                  cursor: "pointer"
                }}
              >
                View
              </a>
              <button
                onClick={() => handleDelete(dir, name)}
                style={{
                  marginLeft: "0.5rem",
                  backgroundColor: "#dc2626",
                  color: "white",
                  border: "none",
                  padding: "0.25rem 0.5rem",
                  borderRadius: "0.25rem",
                  cursor: "pointer"
                }}
              >
                Delete
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );

  return (
    <div style={{ padding: "2rem", color: "white", backgroundColor: "#18181b", minHeight: "100vh" }}>
      <h2 style={{ fontSize: "1.875rem", marginBottom: "1rem" }}>Admin Controls</h2>

      {error && <p style={{ color: "red" }}>{error}</p>}
      {feedback && <p style={{ color: "#22c55e", marginBottom: "1rem" }}>{feedback}</p>}

      {renderFileList("Logs", logs, "logs")}
      {renderFileList("Uploads", uploads, "uploads")}
      {renderFileList("Transcripts", transcripts, "transcripts")}

      <div style={{ marginTop: "2rem", display: "flex", gap: "1rem" }}>
        <button
          onClick={handleReset}
          style={{
            backgroundColor: "#dc2626",
            color: "white",
            border: "none",
            padding: "0.5rem 1rem",
            borderRadius: "0.25rem",
            cursor: "pointer"
          }}
        >
          Reset System
        </button>

        <button
          onClick={handleDownloadAll}
          style={{
            backgroundColor: "#2563eb",
            color: "white",
            border: "none",
            padding: "0.5rem 1rem",
            borderRadius: "0.25rem",
            cursor: "pointer"
          }}
        >
          Download All Data (ZIP)
        </button>
      </div>
    </div>
  );
}
