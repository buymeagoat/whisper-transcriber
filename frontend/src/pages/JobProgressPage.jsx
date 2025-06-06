import { useEffect, useState } from "react";
import { ROUTES } from "../routes";
import { useParams } from "react-router-dom";

export default function JobProgressPage() {
  const { jobId } = useParams();
  const [log, setLog] = useState("Loading log...");
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    const fetchLog = () => {
      fetch(`${ROUTES.API}/log/${jobId}`)
        .then(res => res.text())
        .then(data => {
          setLog(data);
          setLastUpdated(new Date().toLocaleTimeString());
        })
        .catch(() => setLog("Failed to load log"));
    };

    fetchLog();
    const interval = setInterval(fetchLog, 30000); // 30 sec refresh
    return () => clearInterval(interval);
  }, [jobId]);

  return (
    <div style={{ padding: "2rem", backgroundColor: "#111", color: "#eee", fontFamily: "monospace" }}>
      <h2>Log for Job {jobId}</h2>
      <div style={{ fontSize: "0.85rem", color: "#a1a1aa", marginBottom: "1rem" }}>
        Auto-refreshing every 30 seconds
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
