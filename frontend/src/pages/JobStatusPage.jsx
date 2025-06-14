// frontend/src/pages/JobStatusPage.jsx

import { useEffect, useState } from "react";
import { ROUTES } from "../routes";
import { useParams } from "react-router-dom";

export default function JobStatusPage() {
  const { jobId } = useParams();
  const [job, setJob] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isCancelled = false;

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

    fetchJob();
    const interval = setInterval(fetchJob, 3000);

    return () => {
      isCancelled = true;
      clearInterval(interval);
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
          <p><strong>Status:</strong> {job.status}</p>
          <p><strong>Created:</strong> {new Date(job.created_at).toLocaleString()}</p>
          <p><strong>Updated:</strong> {job.updated ? new Date(job.updated).toLocaleString() : "N/A"}</p>

          {job.status === "completed" && (
            <a
              href={`${ROUTES.API}/jobs/${jobId}/download`}
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
