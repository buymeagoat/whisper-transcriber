import React from "react";

export function List({ style = {}, children, ...props }) {
  const listStyle = {
    listStyle: "none",
    paddingLeft: 0,
    ...style,
  };
  return (
    <ul style={listStyle} {...props}>
      {children}
    </ul>
  );
}

export function ListItem({ style = {}, children, ...props }) {
  const itemStyle = {
    marginBottom: "0.25rem",
    ...style,
  };
  return (
    <li style={itemStyle} {...props}>
      {children}
    </li>
  );
}

