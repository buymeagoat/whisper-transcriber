// frontend/src/pages/UploadPage.jsx

import { useState } from "react";

export default function UploadPage() {
  const [file, setFile] = useState(null);
  const [model, setModel] = useState("tiny");
  const [status, setStatus] = useState(null);

  const handleUpload = async () => {
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    formData.append("model", model);

    setStatus("Uploading and transcribing...");
    try {
      const res = await fetch("/jobs", { method: "POST", body: formData });
      const data = await res.json();
      if (res.ok) {
        setStatus(`✅ Job started: ${data.job_id}`);
      } else {
        setStatus(`❌ Error: ${data.error}`);
      }
    } catch (err) {
      setStatus(`❌ Network error`);
    }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold">Upload Audio File for Transcription</h2>

      <input type="file" onChange={(e) => setFile(e.target.files[0])} />

      <div>
        <label className="block mb-1">Select Model</label>
        <select
          className="text-black p-1"
          value={model}
          onChange={(e) => setModel(e.target.value)}
        >
          <option value="tiny">tiny</option>
          <option value="base">base</option>
          <option value="small">small</option>
          <option value="medium">medium</option>
          <option value="large">large</option>
        </select>
      </div>

      <button
        onClick={handleUpload}
        className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded"
      >
        Transcribe
      </button>

      {status && <p>{status}</p>}
    </div>
  );
}
