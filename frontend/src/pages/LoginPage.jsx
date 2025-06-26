import { useState, useContext } from "react";
import { ROUTES } from "../routes";
import { AuthContext } from "../context/AuthContext";
import { useApi } from "../api";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const { login } = useContext(AuthContext);
  const api = useApi();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      const body = new URLSearchParams({ username, password });
      const data = await api.post(
        "/token",
        body,
        { headers: { "Content-Type": "application/x-www-form-urlencoded" } }
      );
      login(data.access_token);
      window.location.href = ROUTES.UPLOAD;
    } catch {
      setError("Network error");
    }
  };

  return (
    <div style={{ padding: "2rem" }}>
      <h2>Login</h2>
      <form onSubmit={handleSubmit} style={{ marginTop: "1rem" }}>
        <div style={{ marginBottom: "0.5rem" }}>
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Username"
            style={{ padding: "0.5rem", width: "200px" }}
          />
        </div>
        <div style={{ marginBottom: "0.5rem" }}>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            style={{ padding: "0.5rem", width: "200px" }}
          />
        </div>
        <button type="submit" style={{ padding: "0.5rem 1rem" }}>Login</button>
      </form>
      {error && <p style={{ color: "red" }}>{error}</p>}
    </div>
  );
}
