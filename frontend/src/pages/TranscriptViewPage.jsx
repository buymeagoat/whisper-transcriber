// frontend/src/pages/TranscriptViewPage.jsx
import { useEffect, useState } from "react";
import { ROUTES } from "../routes";
import { useParams } from "react-router-dom";

export default function TranscriptViewPage() {
  const { jobId } = useParams();
  const [transcript, setTranscript] = useState("");
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${ROUTES.API}/transcript/${jobId}/view`)
      .then((res) => {
        if (!res.ok) throw new Error("Transcript not found");
        return res.text();
      })
      .then(setTranscript)
      .catch((err) => setError(err.message));
  }, [jobId]);

  return (
    <div style={{ padding: "1.5rem", color: "white" }}>
      <div
        style={{
          backgroundColor: "red",
          color: "white",
          padding: "1rem",
          borderRadius: "0.5rem",
          marginBottom: "1rem"
        }}
      >
        🧪 Forced Style Test — no Tailwind involved
      </div>

      <h1 style={{ fontSize: "1.5rem", fontWeight: "bold", marginBottom: "1rem" }}>
        Transcript Viewer
      </h1>

      {error ? (
        <div style={{ color: "red", fontSize: "0.9rem" }}>{error}</div>
      ) : (
        <pre
          style={{
            whiteSpace: "pre-wrap",
            backgroundColor: "#27272a", // zinc-800 equivalent
            padding: "1rem",
            borderRadius: "0.5rem"
          }}
        >
          {transcript}
        </pre>
      )}
    </div>
  );
}
