// frontend/src/pages/TranscriptViewPage.jsx
import { useEffect, useRef, useState } from "react";
import { ROUTES } from "../routes";
import { useParams } from "react-router-dom";
import { useApi } from "../api";

export default function TranscriptViewPage() {
  const { jobId } = useParams();
  const api = useApi();
  const [transcript, setTranscript] = useState("");
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const [showMatchesOnly, setShowMatchesOnly] = useState(false);
  const containerRef = useRef(null);

  useEffect(() => {
    api
      .get(`/transcript/${jobId}/view`)
      .then((data) => {
        if (typeof data === "string") setTranscript(data);
        else setTranscript(JSON.stringify(data));
      })
      .catch((err) => setError(err.message));
  }, [jobId]);

  useEffect(() => {
    if (!search) return;
    const el = containerRef.current?.querySelector("mark");
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
    }
  }, [search]);

  const escapeRegExp = (string) =>
    string.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

  const highlight = (text, query) => {
    if (!query) return text;
    const regex = new RegExp(`(${escapeRegExp(query)})`, "gi");
    const parts = text.split(regex);
    return parts.map((part, i) =>
      regex.test(part) ? (
        <mark key={i} style={{ backgroundColor: "yellow", color: "black" }}>
          {part}
        </mark>
      ) : (
        part
      )
    );
  };

  const transcriptLines = transcript.split(/\r?\n/);
  const filteredLines = search && showMatchesOnly
    ? transcriptLines.filter((line) =>
        line.toLowerCase().includes(search.toLowerCase())
      )
    : transcriptLines;

  return (
    <div style={{ padding: "1.5rem", color: "white" }}>

      <h1 style={{ fontSize: "1.5rem", fontWeight: "bold", marginBottom: "1rem" }}>
        Transcript Viewer
      </h1>

      <input
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search transcript..."
        style={{ marginBottom: "0.5rem", padding: "0.5rem", width: "100%" }}
      />
      <label style={{ display: "block", marginBottom: "1rem" }}>
        <input
          type="checkbox"
          checked={showMatchesOnly}
          onChange={(e) => setShowMatchesOnly(e.target.checked)}
          style={{ marginRight: "0.5rem" }}
        />
        Show matches only
      </label>

      {error ? (
        <div style={{ color: "red", fontSize: "0.9rem" }}>{error}</div>
      ) : (
        <pre
          ref={containerRef}
          style={{
            whiteSpace: "pre-wrap",
            backgroundColor: "#27272a", // zinc-800 equivalent
            padding: "1rem",
            borderRadius: "0.5rem",
            maxHeight: "60vh",
            overflowY: "auto"
          }}
        >
          {filteredLines.map((line, idx) => (
            <span key={idx}>
              {highlight(line, search)}
              {"\n"}
            </span>
          ))}
        </pre>
      )}
    </div>
  );
}
