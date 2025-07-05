import React, { useContext } from "react";
import { Link } from "react-router-dom";
import { ROUTES } from "../routes";
import { AuthContext } from "../context/AuthContext";
import ToastContainer from "./ToastContainer";

export default function Layout({ children }) {
  const { logout, isAuthenticated, role } = useContext(AuthContext);

  const handleLogout = () => {
    logout();
    window.location.href = ROUTES.LOGIN;
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        minHeight: "100vh",
        backgroundColor: "#18181b",
        color: "white",
      }}
    >
      <ToastContainer />
      <header className="app-header">
        <h1 style={{ margin: 0 }}>Whisper Transcriber</h1>
      </header>
      <div style={{ display: "flex", flex: 1 }}>
        <aside className="side-nav">
          <nav style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
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
          <a href="/download-app" style={linkStyle}>
            Download Desktop App
          </a>
          {role === "admin" && (
            <Link to={ROUTES.SETTINGS} style={linkStyle}>
              Settings
            </Link>
          )}
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
        </aside>
        <main className="page-content" style={{ flex: 1 }}>
          {children}
        </main>
      </div>
    </div>
  );
}

const linkStyle = {
  color: "white",
  textDecoration: "none",
  fontWeight: "500",
  padding: "0.25rem 0.5rem",
};
