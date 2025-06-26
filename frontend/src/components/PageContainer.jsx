import React from "react";

export default function PageContainer({ style = {}, children }) {
  const containerStyle = {
    backgroundColor: "#18181b",
    color: "white",
    padding: "2rem",
    minHeight: "100vh",
    ...style,
  };
  return <div style={containerStyle}>{children}</div>;
}
