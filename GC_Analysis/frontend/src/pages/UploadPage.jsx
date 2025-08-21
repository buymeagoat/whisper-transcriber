import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ROUTES } from "../routes";
import { useApi } from "../api";
const MAX_FILES = 10;
const MAX_SIZE_MB = 2048;
const ALLOWED_TYPES = ["audio/wav", "audio/mpeg", "audio/mp3", "audio/x-m4a", "audio/mp4", "audio/x-wav"];

export default function UploadPage() {
  const api = useApi();
  const [files, setFiles] = useState([]);
  const [model, setModel] = useState("tiny");
  const [status, setStatus] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [showNewJobBtn, setShowNewJobBtn] = useState(false);
  const [submittedJobs, setSubmittedJobs] = useState([]);
  const inputRef = useRef();
  const navigate = useNavigate();

  useEffect(() => {
    const load = async () => {
      try {
        const data = await api.get("/user/settings");
        if (data.default_model) {
          setModel(data.default_model);
        }
      } catch {
        // ignore errors
      }
    };
    load();
  }, []);

  const validateFile = (file) => {
    if (!ALLOWED_TYPES.includes(file.type)) {
      return `❌ Unsupported format: ${file.name}`;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      return `❌ File too large: ${file.name}`;
    }
    return null;
  };

  const handleFileChange = (e) => {
    const selected = Array.from(e.target.files);
    const newFiles = [...files];

    selected.forEach((file) => {
      if (newFiles.length < MAX_FILES) {
        const error = validateFile(file);
        newFiles.push({ file, error });
      }
    });

    setFiles(newFiles.slice(0, MAX_FILES));
    e.target.value = "";
  };

  const handleDelete = (index) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  useEffect(() => {
    const save = async () => {
      try {
        await api.post("/user/settings", { default_model: model });
      } catch {
        // ignore errors
      }
    };
    save();
  }, [model]);
// ── NEW handler (component scope) ─────────────────────────
const handleNewJob = () => {
  setFiles([]);
  setJobId(null);
  setStatus(null);
  setShowNewJobBtn(false);
  setSubmittedJobs([]);
  inputRef.current.value = "";
};
// ──────────────────────────────────────────────────────────
    const handleUploadAll = async () => {
    for (const { file, error } of files) {
      if (error) continue;

      const formData = new FormData();
      formData.append("file", file); // ✅ fixed key
      formData.append("model", model);

      let entryIndex;
      setSubmittedJobs((prev) => {
        const newJobs = [...prev, { fileName: file.name, jobId: null, status: "Uploading..." }];
        entryIndex = newJobs.length - 1;
        return newJobs;
      });

      setStatus(`Uploading: ${file.name}`);
      setJobId(null);

      const updateJob = (updates) =>
        setSubmittedJobs((prev) => {
          const copy = [...prev];
          copy[entryIndex] = { ...copy[entryIndex], ...updates };
          return copy;
        });

      try {
        const data = await api.post("/jobs", formData);
        if (data.job_id) {
          setStatus(`✅ Job started: ${file.name}`);
          setJobId(data.job_id);
          setShowNewJobBtn(true);
          updateJob({ jobId: data.job_id, status: "✅ Started" });
        } else {
          const msg = `❌ ${file.name}: ${data.error || "Unknown error"}`;
          setStatus(msg);
          updateJob({ status: msg });
        }
      } catch {
        setStatus(`❌ Network error for ${file.name}`);
        updateJob({ status: "❌ Network error" });
      }
    }
  };

  return (
    <div className="page-content">
      <h2 style={{ fontSize: "1.25rem", fontWeight: "bold" }}>Upload Audio Files</h2>

      <input
        ref={inputRef}
        type="file"
        accept=".wav,.mp3,.m4a"
        multiple
        onChange={handleFileChange}
        style={{ display: "block", marginTop: "1rem", marginBottom: "1rem" }}
      />

      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "1rem",
        }}
      >
        {files.map(({ file, error }, i) => (
          <div
            key={i}
            className="upload-file-card"
            style={{
              position: "relative",
              padding: "1rem",
              backgroundColor: "#27272a",
              color: "#f4f4f5",
              border: "1px solid #3f3f46",
              borderRadius: "0.5rem",
              fontSize: "0.9rem",
            }}
          >
            <div style={{ fontWeight: "bold", marginBottom: "0.25rem" }}>{file.name}</div>
            <div style={{ color: "#a1a1aa" }}>{(file.size / (1024 * 1024)).toFixed(2)} MB</div>
            {error && <div style={{ color: "red", marginTop: "0.5rem" }}>{error}</div>}
            <button
              onClick={() => handleDelete(i)}
              aria-label={`Delete ${file.name}`}
              style={{
                position: "absolute",
                top: "0.5rem",
                right: "0.5rem",
                background: "transparent",
                border: "none",
                color: "#f87171",
                fontSize: "1.25rem",
                cursor: "pointer",
              }}
            >
              ✕
            </button>
          </div>
        ))}
      </div>

      <div style={{ marginTop: "1.5rem" }}>
        <label style={{ display: "block", marginBottom: "0.5rem" }}>Select Model</label>
        <select
          value={model}
          onChange={(e) => setModel(e.target.value)}
          style={{ padding: "0.5rem", color: "black" }}
        >
          <option value="tiny">tiny</option>
          <option value="base">base</option>
          <option value="small">small</option>
          <option value="medium">medium</option>
          <option value="large">large</option>
        </select>
      </div>

      <button
        onClick={handleUploadAll}
        disabled={files.length === 0}
        style={{
          marginTop: "1rem",
          padding: "0.5rem 1rem",
          backgroundColor: "#2563eb",
          color: "white",
          borderRadius: "0.25rem",
          border: "none",
          cursor: "pointer",
        }}
      >
        Start Transcription Jobs
      </button>

      {status && (
        <div style={{ fontSize: "0.85rem", color: "#ccc", marginTop: "0.75rem" }}>{status}</div>
      )}

      {submittedJobs.length > 0 && (
        <div style={{ marginTop: "1.5rem" }}>
          <h3 style={{ fontSize: "1rem", fontWeight: "bold", marginBottom: "0.5rem" }}>
            Submitted Jobs
          </h3>
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {submittedJobs.map((job, i) => (
              <li key={i} style={{ marginBottom: "0.5rem" }}>
                <span style={{ marginRight: "0.5rem" }}>{job.fileName}:</span>
                <span>{job.status}</span>
                {job.jobId && (
                  <a
                    href={ROUTES.STATUS.replace(":jobId", job.jobId)}
                    style={{ marginLeft: "0.5rem", color: "#60a5fa", textDecoration: "underline" }}
                  >
                    View Status
                  </a>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* --- UploadPage action buttons ---------------------------------- */}
      {jobId && (
        <>
          {/* View Job Status */}
          <button
            onClick={() => navigate(ROUTES.STATUS.replace(":jobId", jobId))}
            style={{
              marginTop: "1.5rem",
              padding: "0.5rem 1rem",
              backgroundColor: "#16a34a",
              color: "white",
              borderRadius: "0.25rem",
              border: "none",
              cursor: "pointer",
            }}
          >
            View Job Status
          </button>

          {/* Start a New Job (appears only after a successful upload) */}
          {showNewJobBtn && (
            <button
              onClick={handleNewJob}
              style={{
                marginTop: "0.75rem",
                marginLeft: "0.75rem",
                padding: "0.5rem 1rem",
                backgroundColor: "#0ea5e9",
                color: "white",
                borderRadius: "0.25rem",
                border: "none",
                cursor: "pointer",
              }}
            >
              Start a New Job
            </button>
          )}
        </>
      )}
    </div>
  );
}
