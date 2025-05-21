import { useState } from 'react';

export default function App() {
  const [file, setFile] = useState(null);
  const [model, setModel] = useState('tiny');
  const [status, setStatus] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setStatus('❌ Please select a file first.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('model', model);

    setStatus('⏳ Uploading and transcribing…');

    try {
      const res = await fetch('/jobs', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      if (res.ok) {
        setStatus(`✅ Done! Output: ${data.output_txt}`);
      } else {
        setStatus(`❌ Error: ${data.error}`);
      }
    } catch (err) {
      setStatus(`❌ Failed: ${err.message}`);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-900 text-white p-6">
      <div className="max-w-xl mx-auto space-y-6">
        <h1 className="text-3xl font-bold">🎙️ Whisper Transcriber</h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block mb-1 text-sm font-medium">Select model:</label>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full p-2 rounded bg-zinc-800 border border-zinc-600"
            >
              <option value="tiny">tiny</option>
              <option value="base">base</option>
              <option value="small">small</option>
              <option value="medium">medium</option>
              <option value="large">large</option>
            </select>
            <p className="text-xs text-zinc-400 mt-1">All models available offline</p>
          </div>

          <div>
            <label className="block mb-1 text-sm font-medium">Upload audio file:</label>
            <input
              type="file"
              accept=".mp3,.m4a,.wav"
              onChange={(e) => setFile(e.target.files[0])}
              className="w-full p-2 rounded bg-zinc-800 border border-zinc-600"
            />
          </div>

          <button
            type="submit"
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded shadow"
          >
            Start Transcription
          </button>
        </form>

        {status && (
          <div className="p-3 mt-4 bg-zinc-800 rounded border border-zinc-700">
            {status}
          </div>
        )}
      </div>
    </div>
  );
}
