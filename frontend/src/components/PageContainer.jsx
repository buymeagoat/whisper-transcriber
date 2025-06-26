import React from "react";

export default function PageContainer({ style = {}, children }) {
  const containerStyle = {
    backgroundColor: "#18181b",
    color: "white",
    minHeight: "100vh",
    ...style,
  };
  return (
    <div className="page-content" style={containerStyle}>
      {children}
    </div>
  );
}
