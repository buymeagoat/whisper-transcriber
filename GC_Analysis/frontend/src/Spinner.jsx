import React from "react";

export default function Spinner({ size = "2rem" }) {
  const circleStyle = {
    width: size,
    height: size,
    border: "4px solid #e5e7eb",
    borderTopColor: "#3b82f6",
    borderRadius: "50%",
    animation: "spin 1s linear infinite",
  };

  return (
    <div style={{ display: "flex", justifyContent: "center", padding: "1rem" }}>
      <style>{"@keyframes spin { to { transform: rotate(360deg); } }"}</style>
      <div style={circleStyle} />
    </div>
  );
}
