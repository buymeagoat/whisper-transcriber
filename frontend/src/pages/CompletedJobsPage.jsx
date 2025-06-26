import { useEffect, useState } from "react";
import { ROUTES, getTranscriptDownloadUrl } from "../routes";
import { STATUS_LABELS } from "../statusLabels";
import PageContainer from "../components/PageContainer";
import Button from "../components/Button";
import { Table, Th, Td } from "../components/Table";

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
    window.open(getTranscriptDownloadUrl(jobId), "_blank");
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
    <PageContainer>
      <h2 className="page-title">Completed Jobs</h2>

      <Table style={{ marginTop: "2rem" }}>
        <thead style={{ backgroundColor: "#27272a" }}> {/* zinc-800 */}
          <tr>
            <Th>Filename</Th>
            <Th>Model</Th>
            <Th>Completed</Th>
            <Th>Actions</Th>
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
                <Td style={{ color: "#60a5fa", textDecoration: "underline", maxWidth: "250px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {job.original_filename}
                </Td>
                <Td>{job.model}</Td>
                <Td>{new Date(job.created_at + 'Z').toLocaleString()}</Td>
                <Td style={{ display: "flex", gap: "0.5rem" }}>
                  <Button title={`Job ID: ${job.id}`} onClick={() => handleView(job.id)}>View</Button>
                  <Button color="#16a34a" onClick={() => handleDownloadTranscript(job.id)}>Download</Button>
                  <Button color="#dc2626" onClick={() => handleDelete(job.id)}>Delete</Button>
                </Td>
              </tr>
            ))
          )}
        </tbody>
      </Table>
    </PageContainer>
  );
}

// styles moved to shared components
