import { useEffect, useState } from "react";
import { api } from "../api.js";

const sections = [
  { key: "expand", icon: "🚀", title: "How to expand", color: "var(--green-600)" },
  { key: "optimize", icon: "⚙️", title: "Optimize operations", color: "#2f80c2" },
  { key: "improve", icon: "📈", title: "Things to improve", color: "var(--amber)" },
  { key: "give_up", icon: "✂️", title: "Consider dropping", color: "#c2542f" },
];

export default function Advisory() {
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");

  function load() {
    setBusy(true);
    setError("");
    api.advisory().then(setData).catch((e) => setError(e.message)).finally(() => setBusy(false));
  }
  useEffect(load, []);

  return (
    <div>
      <div className="page-head row spread">
        <div>
          <h1>🧭 Farm Advisory Engine</h1>
          <p>Data-driven recommendations built from your profile and activity.</p>
        </div>
        <button className="btn outline" onClick={load} disabled={busy}>{busy ? "…" : "↻ Refresh"}</button>
      </div>

      {error && <div className="error-box">{error}</div>}
      {busy && !data && <div className="card">Generating your personalized advisory…</div>}

      {data && (
        <>
          <div className="card" style={{ marginBottom: 20, background: "linear-gradient(120deg,var(--green-50),#fff)" }}>
            <span className="pill">Executive summary</span>
            <p style={{ fontSize: 16, marginBottom: 0 }}>{data.summary}</p>
          </div>

          <div className="stat-tiles">
            <div className="stat"><div className="num">{data.metrics.crops_count}</div><div className="lbl">Crops</div></div>
            <div className="stat"><div className="num">{data.metrics.disease_incidents}</div><div className="lbl">Disease incidents</div></div>
            <div className="stat"><div className="num">{data.metrics.active_listings}</div><div className="lbl">Active listings</div></div>
            <div className="stat"><div className="num">{data.metrics.experience_years}y</div><div className="lbl">Experience</div></div>
          </div>

          <div className="grid cols-2">
            {sections.map((s) => (
              <div key={s.key} className="card">
                <h3 style={{ color: s.color }}>{s.icon} {s.title}</h3>
                <ul className="clean">
                  {(data[s.key] || []).map((item, i) => <li key={i}>{item}</li>)}
                  {(data[s.key] || []).length === 0 && <li className="muted">Nothing flagged here — well done!</li>}
                </ul>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
