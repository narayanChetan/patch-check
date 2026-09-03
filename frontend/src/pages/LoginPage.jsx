import { useState } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const { user, login, error, loading } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  if (user) return <Navigate to="/scan" replace />;

  async function handleSubmit(e) {
    e.preventDefault();
    await login(username, password);
  }

  return (
    <div className="login-wrap">
      <div className="login-card">
        <h1>PackCheck</h1>
        <p className="sub">Legal Metrology Declaration Scanner — sign in to continue</p>
        <form onSubmit={handleSubmit}>
          <label className="field-label" htmlFor="username">Username</label>
          <input
            id="username" type="text" value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username" required
          />
          <div style={{ height: 12 }} />
          <label className="field-label" htmlFor="password">Password</label>
          <input
            id="password" type="password" value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password" required
          />
          {error && <p className="error-text">{error}</p>}
          <button className="btn btn-primary" type="submit" disabled={loading} style={{ width: "100%", marginTop: 18 }}>
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>
        <div className="demo-hint">
          <b>Demo accounts</b> (change before real deployment):<br />
          Inspector — <code>inspector / inspector123</code><br />
          Admin — <code>admin / admin123</code>
        </div>
      </div>
    </div>
  );
}
