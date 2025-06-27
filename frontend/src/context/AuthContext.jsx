import { createContext, useState, useEffect } from "react";

function getRole(token) {
  if (!token) return null;
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.role;
  } catch {
    return null;
  }
}

export const AuthContext = createContext({
  token: null,
  login: () => {},
  logout: () => {},
  isAuthenticated: false,
});

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("token"));
  const [role, setRole] = useState(() => getRole(localStorage.getItem("token")));

  const login = (newToken) => {
    setToken(newToken);
    setRole(getRole(newToken));
  };

  const logout = () => {
    setToken(null);
    setRole(null);
  };

  useEffect(() => {
    if (token) {
      localStorage.setItem("token", token);
      setRole(getRole(token));
    } else {
      localStorage.removeItem("token");
      setRole(null);
    }
  }, [token]);

  return (
    <AuthContext.Provider
      value={{ token, role, login, logout, isAuthenticated: Boolean(token) }}
    >
      {children}
    </AuthContext.Provider>
  );
}
