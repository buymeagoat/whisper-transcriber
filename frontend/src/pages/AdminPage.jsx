import React, { useState, useEffect, useContext } from "react";
import { ROUTES } from "../routes";
import { useApi } from "../api";
import { useDispatch } from "react-redux";
import { addToast } from "../store";
import StatsPanel from "../components/StatsPanel";
import { AuthContext } from "../context/AuthContext";
export default function AdminPage() {
  const api = useApi();
  const dispatch = useDispatch();
  const { token } = useContext(AuthContext);
  const [logs, setLogs] = useState([]);
  const [uploads, setUploads] = useState([]);
  const [transcripts, setTranscripts] = useState([]);
  const [stats, setStats] = useState(null);
  const [refreshToggle, setRefreshToggle] = useState(false);
  const [cleanupEnabled, setCleanupEnabled] = useState(false);
  const [cleanupDays, setCleanupDays] = useState(30);
  const [systemLog, setSystemLog] = useState("Loading log...");
  const [systemUpdated, setSystemUpdated] = useState(null);
 const API_HOST = ROUTES.API;

  const fetchStats = async () => {
    try {
      const data = await api.get("/admin/stats");
      setStats(data);
    } catch {
      setStats(null);
      dispatch(addToast("Failed to load server stats.", "error"));
    }
  };
// NEW – poll every 30 s
useEffect(() => {
  fetchStats();                                // first call on mount
  const id = setInterval(fetchStats, 30000);   // 30 000 ms = 30 s
  return () => clearInterval(id);              // cleanup on unmount
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, []);

  const fetchFiles = async () => {
    try {
      const data = await api.get("/admin/files");
      setLogs(data.logs || []);
      setUploads(data.uploads || []);
      setTranscripts(data.transcripts || []);
      dispatch(addToast("File lists refreshed.", "success"));
    } catch {
      dispatch(addToast("Failed to load file listings.", "error"));
    }
  };

  const fetchCleanupConfig = async () => {
    try {
      const data = await api.get("/admin/cleanup-config");
      setCleanupEnabled(data.cleanup_enabled);
      setCleanupDays(data.cleanup_days);
    } catch {
      dispatch(addToast("Failed to load cleanup settings.", "error"));
    }
  };

  useEffect(() => {
    let ws;
    const fetchLog = async () => {
      try {
        const data = await api.get("/logs/access");
        if (typeof data === "string") {
          setSystemLog(data);
        }
      } catch {
        try {
          const data = await api.get("/logs/system.log");
          if (typeof data === "string") {
            setSystemLog(data);
          }
        } catch {
          setSystemLog("Failed to load log");
        }
      }
    };

    fetchLog();

    const wsUrl = `${ROUTES.API.replace(/^http/, "ws")}/ws/logs/system?token=${token}`;
    ws = new WebSocket(wsUrl);
    ws.onmessage = (ev) => {
      setSystemLog((prev) => prev + ev.data);
      setSystemUpdated(new Date().toLocaleTimeString());
    };
    return () => {
      if (ws) ws.close();
    };
  }, [token]);

  useEffect(() => {
    fetchFiles();
    fetchCleanupConfig();
  }, [refreshToggle]);


  const handleDelete = async (dir, filename) => {
    const confirmed = window.confirm(`Delete ${filename} from ${dir}?`);
    if (!confirmed) return;
    try {
      await api.del("/admin/files", {
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ folder: dir, filename })
      });
      dispatch(addToast(`Deleted ${filename} from ${dir}.`, "success"));
      setRefreshToggle(prev => !prev);
    } catch {
      dispatch(addToast(`Failed to delete ${filename} from ${dir}.`, "error"));
    }
  };

  const handleReset = async () => {
    const confirmed = window.confirm(
      "This will erase ALL jobs, uploads, logs, and transcripts. Continue?"
    );
    if (!confirmed) return;
    try {
      await api.post("/admin/reset");
      dispatch(addToast("System reset complete.", "success"));
      setRefreshToggle(prev => !prev);
    } catch {
      dispatch(addToast("Reset failed.", "error"));
    }
  };

  const handleDownloadAll = () => {
    window.open(`${API_HOST}/admin/download-all`);
  };

  const handleShutdown = async () => {
    const confirmed = window.confirm("Shut down the server?");
    if (!confirmed) return;
    try {
      await api.post("/admin/shutdown");
      dispatch(addToast("Server shutting down...", "success"));
    } catch {
      dispatch(addToast("Failed to shut down server.", "error"));
    }
  };

  const handleRestart = async () => {
    const confirmed = window.confirm("Restart the server?");
    if (!confirmed) return;
    try {
      await api.post("/admin/restart");
      dispatch(addToast("Server restarting...", "success"));
    } catch {
      dispatch(addToast("Failed to restart server.", "error"));
    }
  };

  const handleSaveCleanup = async () => {
    try {
      const data = await api.post("/admin/cleanup-config", {
        cleanup_enabled: cleanupEnabled,
        cleanup_days: cleanupDays,
      });
      setCleanupEnabled(data.cleanup_enabled);
      setCleanupDays(data.cleanup_days);
      dispatch(addToast("Cleanup settings saved.", "success"));
    } catch {
      dispatch(addToast("Failed to save cleanup settings.", "error"));
    }
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
    <div className="page-content" style={{ color: "white", backgroundColor: "#18181b", minHeight: "100vh" }}>
      <h2 style={{ fontSize: "1.875rem", marginBottom: "1rem" }}>Admin Controls</h2>
            {/* NEW stats read-out */}
      <StatsPanel stats={stats} />

      <div style={{ marginTop: "1rem" }}>
        <h3 style={{ fontSize: "1.125rem", marginBottom: "0.5rem" }}>System Log</h3>
        <div style={{ fontSize: "0.85rem", color: "#a1a1aa", marginBottom: "0.5rem" }}>
          Streaming log via WebSocket
          {systemUpdated && <span> — Last updated at {systemUpdated}</span>}
        </div>
        <pre
          style={{
            backgroundColor: "#27272a",
            padding: "1rem",
            maxHeight: "40vh",
            overflowY: "scroll",
            whiteSpace: "pre-wrap",
          }}
        >
          {systemLog}
        </pre>
      </div>


      {renderFileList("Logs", logs, "logs")}
      {renderFileList("Uploads", uploads, "uploads")}
      {renderFileList("Transcripts", transcripts, "transcripts")}

      <div style={{ marginTop: "2rem" }}>
        <h3 style={{ fontSize: "1.125rem", marginBottom: "0.5rem" }}>Cleanup Settings</h3>
        <label style={{ display: "block", marginBottom: "0.5rem" }}>
          <input
            type="checkbox"
            checked={cleanupEnabled}
            onChange={(e) => setCleanupEnabled(e.target.checked)}
            style={{ marginRight: "0.5rem" }}
          />
          Enable automatic cleanup
        </label>
        <label style={{ display: "block", marginBottom: "0.5rem" }}>
          Retention Days:
          <input
            type="number"
            value={cleanupDays}
            onChange={(e) => setCleanupDays(Number(e.target.value))}
            style={{ marginLeft: "0.5rem", width: "80px" }}
          />
        </label>
        <button
          onClick={handleSaveCleanup}
          style={{
            backgroundColor: "#2563eb",
            color: "white",
            border: "none",
            padding: "0.5rem 1rem",
            borderRadius: "0.25rem",
            cursor: "pointer",
          }}
        >
          Save Cleanup Settings
        </button>
      </div>

      <div style={{ marginTop: "2rem", display: "flex", gap: "1rem" }}>
        <button onClick={handleReset}
          style={{ backgroundColor:"#dc2626", color:"white", border:"none",
                  padding:"0.5rem 1rem", borderRadius:"0.25rem", cursor:"pointer" }}>
          Reset System
        </button>

        <button onClick={handleDownloadAll}
          style={{ backgroundColor:"#2563eb", color:"white", border:"none",
                  padding:"0.5rem 1rem", borderRadius:"0.25rem", cursor:"pointer" }}>
          Download All Data (ZIP)
        </button>

        <button onClick={handleShutdown}
          style={{ backgroundColor:"#6b7280", color:"white", border:"none",
                  padding:"0.5rem 1rem", borderRadius:"0.25rem", cursor:"pointer" }}>
          Shutdown Server
        </button>

        <button onClick={handleRestart}
          style={{ backgroundColor:"#6b7280", color:"white", border:"none",
                  padding:"0.5rem 1rem", borderRadius:"0.25rem", cursor:"pointer" }}>
          Restart Server
        </button>

      </div>
    </div>
  );
}
