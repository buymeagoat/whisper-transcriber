// frontend/src/pages/JobStatusPage.jsx

import { useEffect, useState } from "react";
import { ROUTES, getTranscriptDownloadUrl } from "../routes";
import { STATUS_LABELS } from "../statusLabels";
import Spinner from "../Spinner";
import { useParams } from "react-router-dom";

export default function JobStatusPage() {
  const { jobId } = useParams();
  const [job, setJob] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isCancelled = false;
    let interval;
    let ws;

    const token = localStorage.getItem("token");

    const fetchJob = async () => {
      try {
        const res = await fetch(`${ROUTES.API}/jobs/${jobId}`);
        const data = await res.json();

        if (!isCancelled) {
          if (res.ok) {
            setJob(data);
            setError(null);
          } else {
            setError(data.error || "Failed to fetch job");
          }
        }
      } catch {
        if (!isCancelled) setError("Network error");
      }
    };

    const connectWs = () => {
      const wsUrl = `${ROUTES.API.replace(/^http/, "ws")}/ws/progress/${jobId}?token=${token}`;
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        clearInterval(interval); // stop polling when socket connected
      };

      ws.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data);
          if (data.status && !isCancelled) {
            setJob((prev) => (prev ? { ...prev, status: data.status } : { status: data.status }));
            setError(null);
          }
        } catch {
          // ignore malformed messages
        }
      };

      ws.onclose = () => {
        if (!isCancelled) {
          // fallback to polling if connection closed
          interval = setInterval(fetchJob, 3000);
        }
      };
    };

    fetchJob();
    interval = setInterval(fetchJob, 3000);
    connectWs();

    return () => {
      isCancelled = true;
      clearInterval(interval);
      if (ws) ws.close();
    };
  }, [jobId]);

  return (
    <div style={{ padding: "1rem" }}>
      <h2 style={{ fontSize: "1.25rem", fontWeight: "bold" }}>📊 Job Status</h2>
      <p style={{ fontSize: "0.9rem", color: "#a1a1aa" }}>Job ID: {jobId}</p>

      {error && <p style={{ color: "red" }}>{error}</p>}

      {!job && !error && <p>Loading job data...</p>}

      {job && (
        <div style={{ marginTop: "1rem" }}>
          <p><strong>Filename:</strong> {job.original_filename}</p>
          <p><strong>Model:</strong> {job.model}</p>
          <p><strong>Status:</strong> {STATUS_LABELS[job.status] || job.status}</p>
          <p><strong>Created:</strong> {new Date(job.created_at + 'Z').toLocaleString()}</p>
          <p><strong>Updated:</strong> {job.updated ? new Date(job.updated + 'Z').toLocaleString() : "N/A"}</p>

          {[
            "queued",
            "processing",
            "enriching",
          ].includes(job.status) && <Spinner />}

          {job.status === "completed" && (
              <a
                href={getTranscriptDownloadUrl(jobId)}
                download
              style={{
                display: "inline-block",
                marginTop: "1rem",
                padding: "0.5rem 1rem",
                backgroundColor: "#16a34a",
                color: "white",
                borderRadius: "0.25rem",
                textDecoration: "none"
              }}
            >
              Download Transcript
            </a>
          )}
        </div>
      )}
    </div>
  );
}
