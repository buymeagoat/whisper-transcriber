import { useEffect, useState } from "react";
import { ROUTES } from "../routes";
import { useDispatch, useSelector } from "react-redux";
import { fetchJobs, selectJobs, addToast } from "../store";
import { STATUS_LABELS } from "../statusLabels";
import Button from "../components/Button";
import { Table, Th, Td } from "../components/Table";
export default function ActiveJobsPage() {
  const dispatch = useDispatch();
  const jobs = useSelector(selectJobs);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  useEffect(() => {
    const load = () =>
      dispatch(fetchJobs({ status: 'queued|processing|enriching' }))
        .unwrap()
        .then(() => setLastUpdated(new Date()))
        .catch(() => dispatch(addToast("Failed to load jobs", "error")));
    load();
    const interval = setInterval(load, 30000); // refresh every 30 seconds
    return () => clearInterval(interval);
  }, [dispatch]);

  return (
    <div className="page-content">
      <h2 style={{ fontSize: "1.25rem", fontWeight: "bold", marginBottom: "1rem" }}>
        ⏳ Active Jobs <span style={{ fontSize: "0.875rem", color: "#a1a1aa" }}>(auto-refreshing every 30s)</span>
      </h2>

      <Table>
        <thead>
          <tr style={{ backgroundColor: "#27272a" }}>
            <Th>Filename</Th>
            <Th>Model</Th>
            <Th>Status</Th>
            <Th>Created</Th>
            <Th>Actions</Th>
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
                <Td>{job.original_filename}</Td>
                <Td>{job.model}</Td>
                <Td>{STATUS_LABELS[job.status] || job.status}</Td>
                <Td>{new Date(job.created_at + 'Z').toLocaleString()}</Td>
                <Td style={{ display: "flex", gap: "0.5rem" }}>
                  <Button
                    color="#eab308"
                    title={`Job ID: ${job.id}`}
                    style={{ padding: "0.4rem 0.6rem", fontSize: "0.8rem" }}
                    onClick={() => window.open(ROUTES.PROGRESS.replace(":jobId", job.id), "_blank")}
                  >
                    View Progress
                  </Button>
                </Td>
              </tr>
            ))
          )}
        </tbody>
      </Table>

      <p style={{ marginTop: "1rem", fontSize: "0.75rem", color: "#a1a1aa" }}>
        Last updated: {lastUpdated.toLocaleTimeString()}
      </p>
    </div>
  );
}

