import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";

export default function TranscriptViewPage() {
  const { jobId } = useParams();
  const [transcript, setTranscript] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/transcript/${jobId}/view`)
      .then(res => {
        if (!res.ok) throw new Error("Failed to fetch transcript");
        return res.json();
      })
      .then(data => {
        setTranscript(data.text || "");
        setError(null);
      })
      .catch(() => setError("Transcript could not be loaded."))
      .finally(() => setLoading(false));
  }, [jobId]);

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-xl font-bold">📄 Transcript Viewer</h2>
      <p className="text-sm text-zinc-400">Job ID: {jobId}</p>

      {loading && <p>Loading transcript...</p>}
      {error && <p className="text-red-400">{error}</p>}

      {!loading && !error && (
        <div className="bg-zinc-900 border border-zinc-700 p-4 rounded whitespace-pre-wrap overflow-y-auto max-h-[75vh]">
          {transcript || <em>No transcript data found.</em>}
        </div>
      )}

      <div className="pt-4">
        <Link to="/completed" className="text-blue-400 hover:underline">
          ← Back to Completed Jobs
        </Link>
      </div>
    </div>
  );
}
