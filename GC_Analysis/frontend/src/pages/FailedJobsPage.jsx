import { useEffect } from "react";
import { ROUTES } from "../routes";
import { STATUS_LABELS } from "../statusLabels";
import { useDispatch, useSelector } from "react-redux";
import { fetchJobs, deleteJob, restartJob, selectJobs, addToast } from "../store";

export default function FailedJobsPage() {
  const dispatch = useDispatch();
  const jobs = useSelector(selectJobs);

  useEffect(() => {
    dispatch(fetchJobs({ status: "failed" }))
      .unwrap()
      .catch(() => dispatch(addToast("Failed to load failed jobs", "error")));
  }, [dispatch]);

  const handleRestart = async (jobId) => {
    dispatch(restartJob(jobId))
      .unwrap()
      .then(() => dispatch(addToast("Job restarted", "success")))
      .catch(() => dispatch(addToast("Error restarting job", "error")));
  };

  const handleDelete = async (jobId) => {
    dispatch(deleteJob(jobId))
      .unwrap()
      .then(() => dispatch(addToast("Job deleted", "success")))
      .catch(() => dispatch(addToast("Error deleting job", "error")));
  };

  return (
    <div
      className="page-content"
      style={{ backgroundColor: "#18181b", color: "white", minHeight: "100vh" }}
    >
      <h2 style={{
        fontSize: "1.875rem",
        fontWeight: "bold",
        color: "#f4f4f5"
      }}>
        Failed Jobs
      </h2>

      <table style={{
        width: "100%",
        borderCollapse: "collapse",
        fontSize: "0.875rem",
        marginTop: "2rem"
      }}>
        <thead style={{ backgroundColor: "#27272a" }}>
          <tr>
            <th style={thStyle}>Filename</th>
            <th style={thStyle}>Model</th>
            <th style={thStyle}>Created</th>
            <th style={thStyle}>Status</th>
            <th style={thStyle}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {jobs.length === 0 ? (
            <tr>
              <td colSpan="5" style={{ textAlign: "center", padding: "1.5rem", color: "#a1a1aa" }}>
                No failed jobs found.
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
                <td style={{ ...tdStyle, color: "#f87171" }}>{job.original_filename}</td>
                <td style={tdStyle}>{job.model}</td>
                <td style={tdStyle}>{new Date(job.created_at + 'Z').toLocaleString()}</td>
                <td style={tdStyle}>{STATUS_LABELS[job.status] || job.status}</td>
                <td style={{ ...tdStyle, display: "flex", gap: "0.5rem" }}>
                  <button style={buttonStyle("#2563eb")} onClick={() => handleRestart(job.id)}>Restart</button>
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

const thStyle = {
  padding: "1rem 1.5rem",
  textAlign: "left",
  color: "#d4d4d8",
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
