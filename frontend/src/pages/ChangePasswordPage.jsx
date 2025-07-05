import { useState, useContext } from "react";
import { useApi } from "../api";
import { AuthContext } from "../context/AuthContext";
import { ROUTES } from "../routes";

export default function ChangePasswordPage() {
  const api = useApi();
  const { logout } = useContext(AuthContext);
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/change-password", { password });
      window.location.href = ROUTES.UPLOAD;
    } catch (err) {
      setError(err.message || "Failed to change password");
    }
  };

  const handleLogout = () => {
    logout();
    window.location.href = ROUTES.LOGIN;
  };

  return (
    <div className="page-content" style={{ maxWidth: "400px", margin: "0 auto" }}>
      <h2>Change Password</h2>
      <form onSubmit={handleSubmit} style={{ marginTop: "1rem" }}>
        <div style={{ marginBottom: "0.5rem" }}>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="New Password"
            style={{ padding: "0.5rem", width: "100%" }}
          />
        </div>
        <button type="submit" style={{ padding: "0.5rem 1rem" }}>
          Save Password
        </button>
      </form>
      <button onClick={handleLogout} style={{ marginTop: "1rem" }}>
        Cancel
      </button>
      {error && <p style={{ color: "red" }}>{error}</p>}
    </div>
  );
}
