import { useEffect, useState } from "react";

export default function AdminLogsPage() {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    fetch("/logs")
      .then(res => res.json())
      .then(data => setLogs(data))
      .catch(() => setLogs([]));
  }, []);

  const handleView = (path) => {
    window.open(`/logs/view?path=${encodeURIComponent(path)}`, '_blank');
  };

  const handleDownload = (path) => {
    window.open(`/logs/download?path=${encodeURIComponent(path)}`, '_blank');
  };

  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">Admin Logs</h2>
      <div className="space-y-4">
        {logs.map(log => (
          <div key={log} className="border p-4 rounded shadow-sm">
            <div className="font-mono text-sm break-all">{log}</div>
            <div className="mt-2 space-x-2">
              <button onClick={() => handleView(log)} className="px-2 py-1 bg-blue-600 text-white rounded">View</button>
              <button onClick={() => handleDownload(log)} className="px-2 py-1 bg-green-600 text-white rounded">Download</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
