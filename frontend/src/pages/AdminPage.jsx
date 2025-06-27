import React, { useState, useEffect, useContext } from "react";
import { ROUTES } from "../routes";
import { useApi } from "../api";
import { useDispatch } from "react-redux";
import { addToast } from "../store";
import StatsPanel from "../components/StatsPanel";
import Button from "../components/Button";
import PageContainer from "../components/PageContainer";
import { AuthContext } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
export default function AdminPage() {
  const api = useApi();
  const dispatch = useDispatch();
  const { token } = useContext(AuthContext);
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
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
    fetchCleanupConfig();
  }, []);



  const handleReset = async () => {
    const confirmed = window.confirm(
      "This will erase ALL jobs, uploads, logs, and transcripts. Continue?"
    );
    if (!confirmed) return;
    try {
      await api.post("/admin/reset");
      dispatch(addToast("System reset complete.", "success"));
      fetchCleanupConfig();
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


  return (
    <PageContainer>
      <h2 className="page-title">Admin Controls</h2>
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

      <Button onClick={() => navigate(ROUTES.FILE_BROWSER)} style={{ marginTop: "1rem" }}>
        Browse Files
      </Button>

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
        <Button onClick={handleSaveCleanup} style={{ marginTop: "0.5rem" }}>
          Save Cleanup Settings
        </Button>
      </div>

      <div style={{ marginTop: "2rem", display: "flex", gap: "1rem" }}>
        <Button onClick={handleReset} color="#dc2626">
          Reset System
        </Button>

        <Button onClick={handleDownloadAll}>
          Download All Data (ZIP)
        </Button>

        <Button onClick={handleShutdown} color="#6b7280">
          Shutdown Server
        </Button>

        <Button onClick={handleRestart} color="#6b7280">
          Restart Server
        </Button>
      </div>
    </PageContainer>
  );
}
