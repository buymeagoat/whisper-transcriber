import React from "react";

export function Table({ style = {}, children, ...props }) {
  const baseStyle = {
    width: "100%",
    borderCollapse: "collapse",
    fontSize: "0.875rem",
    ...style,
  };
  return (
    <table style={baseStyle} {...props}>
      {children}
    </table>
  );
}

export function Th({ style = {}, children, ...props }) {
  const thStyle = {
    padding: "1rem 1.5rem",
    textAlign: "left",
    color: "#d4d4d8",
    borderBottom: "1px solid #3f3f46",
    ...style,
  };
  return (
    <th style={thStyle} {...props}>
      {children}
    </th>
  );
}

export function Td({ style = {}, children, ...props }) {
  const tdStyle = {
    padding: "0.75rem 1.5rem",
    borderBottom: "1px solid #3f3f46",
    ...style,
  };
  return (
    <td style={tdStyle} {...props}>
      {children}
    </td>
  );
}
