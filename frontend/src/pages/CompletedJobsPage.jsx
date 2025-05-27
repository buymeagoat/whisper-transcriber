import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

export default function CompletedJobsPage() {
  const [jobs, setJobs] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch("http://localhost:8000/jobs?status=completed")
      .then((res) => res.json())
      .then((data) => setJobs(data))
      .catch(() => setError("Failed to load completed jobs"));
  }, []);

  const downloadTranscript = (jobId) => {
    window.open(`http://localhost:8000/transcript/${jobId}`);
  };

  const restartJob = async (jobId) => {
    const model = prompt("Enter model (e.g., tiny, base, small, medium, large):", "base");
    if (model) {
      const formData = new FormData();
      formData.append("model", model);
      try {
        const res = await fetch(`http://localhost:8000/jobs/${jobId}/restart`, {
          method: "POST",
          body: formData,
        });
        if (!res.ok) throw new Error("Failed to restart job");
        alert("Job restart requested");
      } catch (err) {
        alert("Error restarting job");
      }
    }
  };

  const deleteJob = async (jobId) => {
    try {
      const res = await fetch(`http://localhost:8000/jobs/${jobId}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Failed to delete job");
      setJobs(jobs.filter((j) => j.id !== jobId));
    } catch (err) {
      alert("Error deleting job");
    }
  };

  const downloadAudio = (jobId) => {
    window.open(`http://localhost:8000/audio/${jobId}`);
  };

  if (error) return <div className="text-red-500">{error}</div>;

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-2xl font-bold">Completed Jobs</h2>
      <table className="w-full table-auto border-collapse border border-zinc-700">
        <thead>
          <tr className="bg-zinc-800">
            <th className="border border-zinc-700 px-2 py-1 text-left">Filename</th>
            <th className="border border-zinc-700 px-2 py-1 text-left">Model</th>
            <th className="border border-zinc-700 px-2 py-1 text-left">Completed</th>
            <th className="border border-zinc-700 px-2 py-1 text-left">Actions</th>
          </tr>
        </thead>
        <tbody>
          {jobs.length === 0 ? (
            <tr>
              <td colSpan="4" className="text-center py-4 text-zinc-400">
                No completed jobs found.
              </td>
            </tr>
          ) : (
            jobs.map((job) => (
              <tr key={job.id} className="hover:bg-zinc-800">
                <td className="border border-zinc-700 px-2 py-1">
                  <Link
                    className="text-blue-400 hover:underline"
                    to={`/transcript/${job.id}/view`}
                  >
                    {job.original_filename}
                  </Link>
                </td>
                <td className="border border-zinc-700 px-2 py-1">{job.model}</td>
                <td className="border border-zinc-700 px-2 py-1">{new Date(job.created_at).toLocaleString()}</td>
                <td className="border border-zinc-700 px-2 py-1 space-x-1">
                  <button
                    className="px-2 py-1 bg-blue-500 text-white rounded"
                    onClick={() => window.open(`/transcript/${job.id}/view`, '_blank')}
                  >
                    View
                  </button>
                  <button
                    className="px-2 py-1 bg-green-500 text-white rounded"
                    onClick={() => downloadTranscript(job.id)}
                  >
                    Download
                  </button>
                  <button
                    className="px-2 py-1 bg-gray-500 text-white rounded"
                    onClick={() => downloadAudio(job.id)}
                  >
                    Audio
                  </button>
                  <button
                    className="px-2 py-1 bg-yellow-500 text-white rounded"
                    onClick={() => restartJob(job.id)}
                  >
                    Restart
                  </button>
                  <button
                    className="px-2 py-1 bg-red-600 text-white rounded"
                    onClick={() => deleteJob(job.id)}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
