import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ROUTES } from "../routes";
import { useApi } from "../api";
import { useErrorHandler } from "../services/errorHandler";
import ProgressBar from "../components/ProgressBar";
import DragDropUpload from "../components/DragDropUpload";
const MAX_FILES = 10;
const MAX_SIZE_MB = 2048;
const ALLOWED_TYPES = [
  "audio/wav", "audio/wave", "audio/x-wav",
  "audio/mpeg", "audio/mp3", "audio/x-mp3",
  "audio/mp4", "audio/m4a", "audio/x-m4a",
  "audio/flac", "audio/x-flac",
  "audio/ogg", "audio/vorbis",
  "audio/webm",
  "audio/aac",
  "video/mp4",
  "video/quicktime",
  "video/x-msvideo"
];

const ALLOWED_EXTENSIONS = [
  ".wav", ".mp3", ".mp4", ".m4a", ".flac", ".ogg", ".webm", ".aac", ".mov", ".avi"
];

export default function UploadPage() {
  const api = useApi();
  const { handleError, withErrorHandling } = useErrorHandler();
  const [files, setFiles] = useState([]);
  const [model, setModel] = useState("tiny");
  const [status, setStatus] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [showNewJobBtn, setShowNewJobBtn] = useState(false);
  const [submittedJobs, setSubmittedJobs] = useState([]);
  const [uploadProgress, setUploadProgress] = useState({}); // Track progress per file
  const inputRef = useRef();
  const navigate = useNavigate();

  useEffect(() => {
    withErrorHandling(
      async () => {
        const data = await api.get("/user/settings");
        if (data.default_model) {
          setModel(data.default_model);
        }
      },
      "Loading user settings",
      { showToast: false } // Don't show toast for this non-critical operation
    );
  }, []);

  const validateFile = (file) => {
    // Check file size
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      return `❌ File too large: ${file.name} (${(file.size / (1024 * 1024)).toFixed(1)}MB > ${MAX_SIZE_MB}MB)`;
    }
    
    if (file.size === 0) {
      return `❌ Empty file: ${file.name}`;
    }
    
    // Check file extension
    const fileName = file.name.toLowerCase();
    const hasValidExtension = ALLOWED_EXTENSIONS.some(ext => fileName.endsWith(ext));
    
    if (!hasValidExtension) {
      return `❌ Unsupported file extension: ${file.name}. Allowed: ${ALLOWED_EXTENSIONS.join(", ")}`;
    }
    
    // Check MIME type (if available)
    if (file.type && !ALLOWED_TYPES.includes(file.type)) {
      return `❌ Unsupported file type: ${file.name} (${file.type})`;
    }
    
    // Check for dangerous characters in filename
    const dangerousChars = /[<>:"|?*\\\/]/;
    if (dangerousChars.test(file.name)) {
      return `❌ Invalid characters in filename: ${file.name}`;
    }
    
    return null; // Valid file
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

  const handleDragDropFiles = (droppedFiles) => {
    const newFiles = [...files];

    droppedFiles.forEach((file) => {
      if (newFiles.length < MAX_FILES) {
        const error = validateFile(file);
        newFiles.push({ file, error });
      }
    });

    setFiles(newFiles.slice(0, MAX_FILES));
  };

  useEffect(() => {
    withErrorHandling(
      () => api.post("/user/settings", { default_model: model }),
      "Saving model preference",
      { showToast: false } // Don't show toast for this background operation
    );
  }, [model]);
// ── NEW handler (component scope) ─────────────────────────
const handleNewJob = () => {
  setFiles([]);
  setJobId(null);
  setStatus(null);
  setShowNewJobBtn(false);
  setSubmittedJobs([]);
  setUploadProgress({});
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
        const newJobs = [...prev, { 
          fileName: file.name, 
          jobId: null, 
          status: "Preparing upload...",
          progress: 0 
        }];
        entryIndex = newJobs.length - 1;
        return newJobs;
      });

      setStatus(`Preparing: ${file.name}`);
      setJobId(null);

      const updateJob = (updates) =>
        setSubmittedJobs((prev) => {
          const copy = [...prev];
          copy[entryIndex] = { ...copy[entryIndex], ...updates };
          return copy;
        });

      // Progress callback
      const onProgress = (percentComplete, loaded, total) => {
        const progressInfo = {
          percent: percentComplete,
          loaded,
          total,
          status: percentComplete < 100 ? 'Uploading...' : 'Processing...'
        };
        
        setUploadProgress(prev => ({
          ...prev,
          [file.name]: progressInfo
        }));
        
        updateJob({ 
          progress: percentComplete,
          status: progressInfo.status
        });
        
        if (percentComplete < 100) {
          setStatus(`Uploading: ${file.name} (${percentComplete.toFixed(1)}%)`);
        } else {
          setStatus(`Processing: ${file.name}`);
        }
      };

      try {
        updateJob({ status: "Starting upload..." });
        const data = await api.postWithProgress("/jobs", formData, onProgress);
        if (data.job_id) {
          setStatus(`✅ Job started: ${file.name}`);
          setJobId(data.job_id);
          setShowNewJobBtn(true);
          updateJob({ 
            jobId: data.job_id, 
            status: "✅ Started",
            progress: 100 
          });
          
          // Clear progress for this file
          setUploadProgress(prev => {
            const newProgress = { ...prev };
            delete newProgress[file.name];
            return newProgress;
          });
        } else {
          const msg = `❌ ${file.name}: ${data.error || "Unknown error"}`;
          setStatus(msg);
          updateJob({ status: msg });
        }
      } catch (error) {
        const errorInfo = handleError(error, `Upload failed for ${file.name}`, false);
        const errorMsg = `❌ ${file.name}: ${errorInfo.userMessage}`;
        setStatus(errorMsg);
        updateJob({ status: errorMsg, progress: 0 });
        
        // Clear progress for this file
        setUploadProgress(prev => {
          const newProgress = { ...prev };
          delete newProgress[file.name];
          return newProgress;
        });
      }
    }
  };

  return (
    <div className="page-content">
      <h2 style={{ fontSize: "1.25rem", fontWeight: "bold" }}>Upload Audio Files</h2>

      {/* Drag and Drop Upload Area */}
      <div style={{ marginTop: "1rem", marginBottom: "1rem" }}>
        <DragDropUpload
          onFileDrop={handleDragDropFiles}
          accept="audio/*,video/*"
          maxFileSize={MAX_SIZE_MB * 1024 * 1024}
          multiple={true}
        />
      </div>

      {/* Fallback file input for manual selection */}
      <div style={{ marginTop: "1rem", marginBottom: "1rem" }}>
        <label style={{ 
          display: "inline-block", 
          padding: "0.5rem 1rem",
          backgroundColor: "#f3f4f6",
          border: "1px solid #d1d5db",
          borderRadius: "0.375rem",
          cursor: "pointer",
          fontSize: "0.9rem",
          color: "#374151"
        }}>
          Or click here to browse files
          <input
            ref={inputRef}
            type="file"
            accept=".wav,.mp3,.m4a,.mp4,.flac,.ogg,.webm,.aac,.mov,.avi"
            multiple
            onChange={handleFileChange}
            style={{ display: "none" }}
          />
        </label>
      </div>

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

      {/* Upload Progress Display */}
      {Object.keys(uploadProgress).length > 0 && (
        <div style={{ marginTop: "1.5rem" }}>
          <h3 style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>Upload Progress</h3>
          {Object.entries(uploadProgress).map(([fileName, progress]) => (
            <div key={fileName} style={{ marginBottom: "1rem" }}>
              <div style={{ 
                fontSize: "0.9rem", 
                marginBottom: "0.5rem",
                display: "flex",
                justifyContent: "space-between"
              }}>
                <span>{fileName}</span>
                <span>{(progress.loaded / (1024 * 1024)).toFixed(1)}MB / {(progress.total / (1024 * 1024)).toFixed(1)}MB</span>
              </div>
              <ProgressBar 
                progress={progress.percent}
                showPercentage={false}
                height="12px"
              />
              <div style={{ 
                fontSize: "0.8rem", 
                color: "#a1a1aa",
                marginTop: "0.25rem"
              }}>
                {progress.status}
              </div>
            </div>
          ))}
        </div>
      )}

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
