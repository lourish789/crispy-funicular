import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import { api } from "../api.js";

const features = [
  { to: "/diagnosis", icon: "🔬", title: "Diagnose a Plant", desc: "Upload a photo or video to detect disease instantly." },
  { to: "/advisory", icon: "🧭", title: "Farm Advisory", desc: "Personalized recommendations to grow your business." },
  { to: "/news", icon: "📰", title: "Agri-News", desc: "Global & local agricultural headlines for your region." },
  { to: "/marketplace", icon: "🛒", title: "Marketplace", desc: "Buy and sell produce, tools, and inputs." },
  { to: "/community", icon: "💬", title: "Community", desc: "Share knowledge with fellow farmers." },
  { to: "/chat", icon: "🤖", title: "AI Expert", desc: "Chat with an assistant that knows your farm." },
];

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState({ diagnoses: 0, listings: 0 });

  useEffect(() => {
    Promise.all([api.diagnosisHistory(), api.myListings()])
      .then(([d, l]) => setStats({ diagnoses: d.length, listings: l.length }))
      .catch(() => {});
  }, []);

  const profileComplete = !!(user?.location && user?.primary_crops);

  return (
    <div>
      <div className="hero-banner">
        <span className="pill amber">🌤️ {user?.location || "Add your location in Profile"}</span>
        <h1>Welcome back, {user?.full_name?.split(" ")[0]} 👋</h1>
        <p style={{ maxWidth: 560, opacity: 0.94 }}>
          Your one-stop agricultural command center. Diagnose crops, get advisory,
          trade, and consult your AI expert — all in one place.
        </p>
      </div>

      {!profileComplete && (
        <div className="card" style={{ marginBottom: 24, borderLeft: "4px solid var(--amber)" }}>
          <div className="row spread">
            <div>
              <strong>Complete your farm profile</strong>
              <p className="muted" style={{ margin: 0 }}>
                Add your crops, location and farm size so the AI can personalize everything.
              </p>
            </div>
            <button className="btn primary" onClick={() => navigate("/profile")}>Complete profile</button>
          </div>
        </div>
      )}

      <div className="stat-tiles">
        <div className="stat"><div className="num">{stats.diagnoses}</div><div className="lbl">Diagnoses run</div></div>
        <div className="stat"><div className="num">{stats.listings}</div><div className="lbl">My listings</div></div>
        <div className="stat"><div className="num">{(user?.primary_crops || "").split(",").filter(Boolean).length}</div><div className="lbl">Crops tracked</div></div>
        <div className="stat"><div className="num">{user?.farm_size_hectares || "—"}</div><div className="lbl">Hectares</div></div>
      </div>

      <h2 style={{ fontSize: 20, marginBottom: 14 }}>Explore the suite</h2>
      <div className="grid cols-3">
        {features.map((f) => (
          <div key={f.to} className="card feature-card" onClick={() => navigate(f.to)}>
            <div className="feature-icon">{f.icon}</div>
            <h3 style={{ margin: "6px 0 0" }}>{f.title}</h3>
            <p className="muted" style={{ margin: 0 }}>{f.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
