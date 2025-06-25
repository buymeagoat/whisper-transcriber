import { useEffect, useState } from "react";
import { ROUTES } from "../routes";
export default function ActiveJobsPage() {
  const [jobs, setJobs] = useState([]);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  const fetchJobs = () => {
    fetch(`${import.meta.env.VITE_API_HOST}/jobs`)
      .then(res => res.json())
      .then(data => {
        setJobs(data);
        setLastUpdated(new Date());
      })
      .catch(() => setJobs([]));
  };

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 30000); // refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ padding: "1rem" }}>
      <h2 style={{ fontSize: "1.25rem", fontWeight: "bold", marginBottom: "1rem" }}>
        ⏳ Active Jobs <span style={{ fontSize: "0.875rem", color: "#a1a1aa" }}>(auto-refreshing every 30s)</span>
      </h2>

      <table style={{
        width: "100%",
        borderCollapse: "collapse",
        fontSize: "0.875rem"
      }}>
        <thead>
          <tr style={{ backgroundColor: "#27272a" }}>
            <th style={thStyle}>Filename</th>
            <th style={thStyle}>Model</th>
            <th style={thStyle}>Status</th>
            <th style={thStyle}>Created</th>
            <th style={thStyle}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {jobs.filter(job => job.status !== "completed" && !job.status.startsWith("failed")).length === 0 ? (
            <tr>
              <td colSpan="5" style={{
                textAlign: "center",
                padding: "1rem",
                color: "#a1a1aa"
              }}>
                No active jobs found.
              </td>
            </tr>
          ) : (
            jobs
              .filter(job => job.status !== "completed" && !job.status.startsWith("failed"))
              .map((job, index) => (
              <tr
                key={job.id}
                style={{ transition: "background-color 0.2s ease" }}
                onMouseOver={(e) => e.currentTarget.style.backgroundColor = "#3f3f46"}
                onMouseOut={(e) => e.currentTarget.style.backgroundColor = "transparent"}
              >
                <td style={tdStyle}>{job.original_filename}</td>
                <td style={tdStyle}>{job.model}</td>
                <td style={tdStyle}>{job.status}</td>
                <td style={tdStyle}>{new Date(job.created_at + 'Z').toLocaleString()}</td>
                <td style={{ ...tdStyle, display: "flex", gap: "0.5rem" }}>
                  <button
                    title={`Job ID: ${job.id}`}
                    style={{
                      backgroundColor: "#eab308", // amber-500
                      color: "white",
                      border: "none",
                      borderRadius: "0.25rem",
                      padding: "0.4rem 0.6rem",
                      cursor: "pointer",
                      fontSize: "0.8rem",
                    }}
                    onClick={() => window.open(ROUTES.PROGRESS.replace(":jobId", job.id), "_blank")}
                  >
                    View Progress
                  </button>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>

      <p style={{ marginTop: "1rem", fontSize: "0.75rem", color: "#a1a1aa" }}>
        Last updated: {lastUpdated.toLocaleTimeString()}
      </p>
    </div>
  );
}

const thStyle = {
  padding: "0.5rem",
  textAlign: "left",
  border: "1px solid #3f3f46",
  color: "#d4d4d8"
};

const tdStyle = {
  padding: "0.5rem",
  border: "1px solid #3f3f46"
};
