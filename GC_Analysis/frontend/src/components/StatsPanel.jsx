import React from "react";

export default function StatsPanel({ stats }) {
  if (!stats) return null;
  return (
    <div style={{ marginTop: "1rem", color: "#a1a1aa" }}>
      <div>
        <strong>CPU Usage:</strong> {stats.cpu_percent}%
        &nbsp;|&nbsp;
        <strong>Memory:</strong> {stats.mem_used_mb}/{stats.mem_total_mb} MB
      </div>
      <div style={{ marginTop: "0.25rem" }}>
        <strong>Completed Jobs:</strong> {stats.completed_jobs}
        &nbsp;|&nbsp;
        <strong>Avg Time:</strong> {stats.avg_job_time}s
        &nbsp;|&nbsp;
        <strong>Queue:</strong> {stats.queue_length}
      </div>
    </div>
  );
}
