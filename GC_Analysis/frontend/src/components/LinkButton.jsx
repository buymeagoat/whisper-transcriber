import React from "react";

export default function LinkButton({ color = "#2563eb", style = {}, children, ...props }) {
  const baseStyle = {
    backgroundColor: color,
    color: "white",
    border: "none",
    borderRadius: "0.25rem",
    padding: "0.5rem 0.75rem",
    cursor: "pointer",
    fontSize: "0.85rem",
    textDecoration: "none",
    display: "inline-block",
    boxShadow: "0 1px 2px rgba(0,0,0,0.2)",
    ...style,
  };
  return (
    <a style={baseStyle} {...props}>
      {children}
    </a>
  );
}

