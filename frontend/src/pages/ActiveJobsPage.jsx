import { useEffect, useState } from "react";

export default function ActiveJobsPage() {
  const [jobs, setJobs] = useState([]);

  useEffect(() => {
    fetch("/jobs")
      .then(res => res.json())
      .then(data => setJobs(data))
      .catch(() => setJobs([]));
  }, []);

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-xl font-bold">⏳ Active Jobs</h2>
      <table className="w-full table-auto border-collapse border border-zinc-700">
        <thead>
          <tr className="bg-zinc-800">
            <th className="border border-zinc-700 px-2 py-1 text-left">Filename</th>
            <th className="border border-zinc-700 px-2 py-1 text-left">Model</th>
            <th className="border border-zinc-700 px-2 py-1 text-left">Status</th>
            <th className="border border-zinc-700 px-2 py-1 text-left">Created</th>
          </tr>
        </thead>
        <tbody>
          {jobs.length === 0 ? (
            <tr>
              <td colSpan="4" className="text-center py-4 text-zinc-400">
                No active jobs found.
              </td>
            </tr>
          ) : (
            jobs.map(job => (
              <tr key={job.id} className="hover:bg-zinc-800">
                <td className="border border-zinc-700 px-2 py-1">{job.original_filename}</td>
                <td className="border border-zinc-700 px-2 py-1">{job.model}</td>
                <td className="border border-zinc-700 px-2 py-1">{job.status}</td>
                <td className="border border-zinc-700 px-2 py-1">{new Date(job.created_at).toLocaleString()}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
