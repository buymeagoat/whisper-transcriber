import React, { useContext } from "react";
import { Link } from "react-router-dom";
import { ROUTES } from "../routes";
import { AuthContext } from "../context/AuthContext";

export default function Layout({ children }) {
  const { logout, isAuthenticated } = useContext(AuthContext);

  const handleLogout = () => {
    logout();
    window.location.href = ROUTES.LOGIN;
  };

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#18181b", color: "white" }}>
      <nav
        style={{
          backgroundColor: "#27272a",
          padding: "1rem",
          display: "flex",
          gap: "1rem",
          borderBottom: "1px solid #3f3f46",
          flexWrap: "wrap",
        }}
      >
        <Link to={ROUTES.UPLOAD} style={linkStyle}>
          Upload
        </Link>
        <Link to={ROUTES.ACTIVE} style={linkStyle}>
          Active Jobs
        </Link>
        <Link to={ROUTES.COMPLETED} style={linkStyle}>
          Completed Jobs
        </Link>
        <Link to={ROUTES.FAILED} style={linkStyle}>
          Failed Jobs
        </Link>
        <Link to={ROUTES.ADMIN} style={linkStyle}>
          Admin
        </Link>
        {isAuthenticated ? (
          <button onClick={handleLogout} style={linkStyle}>
            Logout
          </button>
        ) : (
          <Link to={ROUTES.LOGIN} style={linkStyle}>
            Login
          </Link>
        )}
      </nav>
      <main className="page-content">{children}</main>
    </div>
  );
}

const linkStyle = {
  color: "white",
  textDecoration: "none",
  fontWeight: "500",
  padding: "0.25rem 0.5rem",
};
