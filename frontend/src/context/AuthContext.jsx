import { createContext, useContext, useEffect, useState } from "react";
import { api } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem("packcheck_user");
    return stored ? JSON.parse(stored) : null;
  });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) localStorage.setItem("packcheck_user", JSON.stringify(user));
    else localStorage.removeItem("packcheck_user");
  }, [user]);

  async function login(username, password) {
    setLoading(true);
    setError(null);
    try {
      const data = await api.login(username, password);
      localStorage.setItem("packcheck_token", data.access_token);
      setUser({ username: data.username, role: data.role });
      return true;
    } catch (err) {
      const msg = err?.response?.data?.detail || "Login failed — check your username and password.";
      setError(msg);
      return false;
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    localStorage.removeItem("packcheck_token");
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, error, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
