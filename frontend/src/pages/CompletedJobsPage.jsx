import { useEffect, useState } from "react";
import { ROUTES } from "../routes";

export default function CompletedJobsPage() {
  const [jobs, setJobs] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${ROUTES.API}/jobs`)
      .then(res => res.json())
      .then(data => setJobs(data.filter(job => job.status === "completed")))
      .catch(() => setError("Failed to load completed jobs"));
  }, []);

  const handleView = (jobId) => {
    window.open(`${ROUTES.API}/transcript/${jobId}/view`, "_blank");
  };

  const handleDownloadTranscript = (jobId) => {
    window.open(`${ROUTES.API}/jobs/${jobId}/download`, "_blank");
  };

  const handleDelete = async (jobId) => {
    try {
      const res = await fetch(`${ROUTES.API}/jobs/${jobId}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error();
      setJobs(jobs.filter(job => job.id !== jobId));
    } catch {
      alert("Error deleting job");
    }
  };

  if (error) {
    return (
      <div style={{ color: "red", padding: "1rem" }}>
        {error}
      </div>
    );
  }

  return (
    <div style={{
      backgroundColor: "#18181b", // zinc-900
      color: "white",
      padding: "2rem",
      minHeight: "100vh"
    }}>
      <h2 style={{
        fontSize: "1.875rem",
        fontWeight: "bold",
        color: "#f4f4f5" // zinc-100
      }}>
        Completed Jobs
      </h2>

      <table style={{
        width: "100%",
        borderCollapse: "collapse",
        fontSize: "0.875rem",
        marginTop: "2rem"
      }}>
        <thead style={{ backgroundColor: "#27272a" }}> {/* zinc-800 */}
          <tr>
            <th style={thStyle}>Filename</th>
            <th style={thStyle}>Model</th>
            <th style={thStyle}>Completed</th>
            <th style={thStyle}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {jobs.length === 0 ? (
            <tr>
              <td colSpan="4" style={{ textAlign: "center", padding: "1.5rem", color: "#a1a1aa" }}>
                No completed jobs found.
              </td>
            </tr>
          ) : (
            jobs.map((job, index) => (
              <tr
                key={job.id}
                style={{
                  backgroundColor: index % 2 === 0 ? "#18181b" : "#27272a",
                  transition: "background-color 0.2s ease"
                }}
                onMouseOver={(e) => e.currentTarget.style.backgroundColor = "#3f3f46"}
                onMouseOut={(e) => e.currentTarget.style.backgroundColor = index % 2 === 0 ? "#18181b" : "#27272a"}
              >
                <td style={{ ...tdStyle, color: "#60a5fa", textDecoration: "underline", maxWidth: "250px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {job.original_filename}
                </td>
                <td style={tdStyle}>{job.model}</td>
                <td style={tdStyle}>{new Date(job.created_at).toLocaleString()}</td>
                <td style={{ ...tdStyle, display: "flex", gap: "0.5rem" }}>
                  <button title={`Job ID: ${job.id}`} style={buttonStyle("#2563eb")} onClick={() => handleView(job.id)}>View</button>
                  <button style={buttonStyle("#16a34a")} onClick={() => handleDownloadTranscript(job.id)}>Download</button>
                  <button style={buttonStyle("#dc2626")} onClick={() => handleDelete(job.id)}>Delete</button>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

// Shared styles

const thStyle = {
  padding: "1rem 1.5rem",
  textAlign: "left",
  color: "#d4d4d8", // zinc-300
  borderBottom: "1px solid #3f3f46"
};

const tdStyle = {
  padding: "0.75rem 1.5rem",
  borderBottom: "1px solid #3f3f46"
};

const buttonStyle = (bgColor) => ({
  backgroundColor: bgColor,
  color: "white",
  border: "none",
  borderRadius: "0.25rem",
  padding: "0.5rem 0.75rem",
  cursor: "pointer",
  fontSize: "0.85rem",
  boxShadow: "0 1px 2px rgba(0,0,0,0.2)"
});
