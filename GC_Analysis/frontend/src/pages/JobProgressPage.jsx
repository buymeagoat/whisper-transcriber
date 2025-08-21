import { useEffect, useState, useContext } from "react";
import { ROUTES } from "../routes";
import { useParams } from "react-router-dom";
import { AuthContext } from "../context/AuthContext";
import { useApi } from "../api";

export default function JobProgressPage() {
  const { jobId } = useParams();
  const { token } = useContext(AuthContext);
  const api = useApi();
  const [log, setLog] = useState("Loading log...");
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    let ws;

    const fetchLog = () => {
      api
        .get(`/log/${jobId}`)
        .then((data) => {
          if (typeof data === "string") {
            setLog(data);
          } else {
            setLog(JSON.stringify(data));
          }
          setLastUpdated(new Date().toLocaleTimeString());
        })
        .catch(() => setLog("Failed to load log"));
    };

    fetchLog();

    const wsUrl = `${ROUTES.API.replace(/^http/, "ws")}/ws/logs/${jobId}?token=${token}`;
    ws = new WebSocket(wsUrl);
    ws.onmessage = (ev) => {
      setLog((prev) => prev + ev.data);
      setLastUpdated(new Date().toLocaleTimeString());
    };

    return () => {
      if (ws) ws.close();
    };
  }, [jobId]);

  return (
    <div style={{ padding: "2rem", backgroundColor: "#111", color: "#eee", fontFamily: "monospace" }}>
      <h2>Log for Job {jobId}</h2>
      <div style={{ fontSize: "0.85rem", color: "#a1a1aa", marginBottom: "1rem" }}>
        Streaming log via WebSocket
        {lastUpdated && <span> — Last updated at {lastUpdated}</span>}
      </div>
      <pre style={{
        backgroundColor: "#27272a",
        padding: "1rem",
        maxHeight: "70vh",
        overflowY: "scroll",
        whiteSpace: "pre-wrap"
      }}>
        {log}
      </pre>
    </div>
  );
}
