import { createContext, useState, useEffect } from "react";

export const AuthContext = createContext({ token: null, setToken: () => {} });

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("token"));

  useEffect(() => {
    if (token) {
      localStorage.setItem("token", token);
    } else {
      localStorage.removeItem("token");
    }
  }, [token]);

  return (
    <AuthContext.Provider value={{ token, setToken }}>
      {children}
    </AuthContext.Provider>
  );
}
