import React from "react";
import { STATUS_LABELS } from "../statusLabels";

export default function StatusBadge({ status }) {
  const colors = {
    queued: "#f59e0b", // amber
    processing: "#3b82f6", // blue
    enriching: "#10b981", // green-teal
    completed: "#16a34a", // green
  };

  const bgColor = colors[status] || (status.startsWith("failed") ? "#dc2626" : "#6b7280");

  const style = {
    backgroundColor: bgColor,
    color: "#fff",
    padding: "0.15rem 0.5rem",
    borderRadius: "0.25rem",
    fontSize: "0.75rem",
    whiteSpace: "nowrap",
  };

  return <span style={style}>{STATUS_LABELS[status] || status}</span>;
}
