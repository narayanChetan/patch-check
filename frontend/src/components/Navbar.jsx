import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();
  return (
    <div className="topbar">
      <div className="brand">
        <svg width="34" height="34" viewBox="0 0 48 48" fill="none" aria-hidden="true">
          <circle cx="24" cy="24" r="21" stroke="#C9AD73" strokeWidth="2.5" />
          <circle cx="24" cy="24" r="15" stroke="#C9AD73" strokeWidth="1.2" strokeDasharray="2 3" />
          <path d="M16 25.5L21 30.5L32 18" stroke="#EFE8D6" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <div>
          <h1>PackCheck</h1>
          <p>Legal Metrology Declaration Scanner</p>
        </div>
      </div>
      <div className="user-chip">
        <span>{user?.username}</span>
        <span className="role-badge">{user?.role}</span>
        <button className="link-btn" onClick={logout}>Log out</button>
      </div>
      <nav className="tabs" style={{ width: "100%", marginBottom: 0 }}>
        <NavLink to="/scan" className={({ isActive }) => `tab-btn ${isActive ? "active" : ""}`}>
          Scan
        </NavLink>
        <NavLink to="/ledger" className={({ isActive }) => `tab-btn ${isActive ? "active" : ""}`}>
          Inspection Ledger
        </NavLink>
      </nav>
    </div>
  );
}
