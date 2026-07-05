import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";

const links = [
  { to: "/", label: "Dashboard", icon: "🏠" },
  { to: "/diagnosis", label: "Diagnose", icon: "🔬" },
  { to: "/advisory", label: "Advisory", icon: "🧭" },
  { to: "/news", label: "News", icon: "📰" },
  { to: "/marketplace", label: "Market", icon: "🛒" },
  { to: "/community", label: "Community", icon: "💬" },
  { to: "/chat", label: "AI Expert", icon: "🤖" },
];

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-logo">🌱</span>
        <div>
          <div className="brand-name">AgriTech Suite</div>
          <div className="brand-sub">grow smarter</div>
        </div>
      </div>
      <nav className="nav-links">
        {links.map((l) => (
          <NavLink
            key={l.to}
            to={l.to}
            end={l.to === "/"}
            className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}
          >
            <span className="nav-icon">{l.icon}</span>
            <span>{l.label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-foot">
        <NavLink to="/profile" className="profile-chip">
          <span className="avatar">{(user?.full_name || "U")[0].toUpperCase()}</span>
          <div className="profile-meta">
            <div className="profile-name">{user?.full_name}</div>
            <div className="profile-loc">{user?.location || "Set your farm"}</div>
          </div>
        </NavLink>
        <button
          className="btn ghost small"
          onClick={() => {
            logout();
            navigate("/login");
          }}
        >
          Log out
        </button>
      </div>
    </aside>
  );
}
