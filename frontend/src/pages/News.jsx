import { useEffect, useState } from "react";
import { useAuth } from "../auth.jsx";
import { api } from "../api.js";

const FALLBACK_IMG =
  "https://images.unsplash.com/photo-1560493676-04071c5f467b?auto=format&fit=crop&w=600&q=60";

export default function News() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [loc, setLoc] = useState(user?.location || "");
  const [busy, setBusy] = useState(true);

  function load(location) {
    setBusy(true);
    api.news(location).then(setData).catch(() => {}).finally(() => setBusy(false));
  }
  useEffect(() => load(loc), []);

  const filtered = (scope) => (data?.articles || []).filter((a) => scope === "all" || a.scope === scope);

  return (
    <div>
      <div className="page-head">
        <h1>📰 Agri-News</h1>
        <p>Real-time global and hyper-local agricultural news{data?.cached ? " · served from cache" : ""}.</p>
      </div>

      <div className="row" style={{ marginBottom: 20 }}>
        <input placeholder="Filter by location (e.g. Nigeria)" value={loc} onChange={(e) => setLoc(e.target.value)} style={{ maxWidth: 320 }} />
        <button className="btn primary" onClick={() => load(loc)} disabled={busy}>{busy ? "…" : "Update"}</button>
      </div>

      {busy && !data && <div className="card">Fetching the latest headlines…</div>}

      {data && ["local", "global"].map((scope) => {
        const items = filtered(scope);
        if (!items.length) return null;
        return (
          <div key={scope} style={{ marginBottom: 28 }}>
            <h2 style={{ fontSize: 20, marginBottom: 14 }}>
              {scope === "local" ? `📍 Local — ${data.location || "your region"}` : "🌍 Global"}
            </h2>
            <div className="grid cols-3">
              {items.map((a, i) => (
                <a key={i} className="card news-card" href={a.url || "#"} target="_blank" rel="noreferrer">
                  <img src={a.image_url || FALLBACK_IMG} alt="" onError={(e) => (e.target.src = FALLBACK_IMG)} />
                  <span className={"pill" + (scope === "local" ? " amber" : "")}>{a.source || "News"}</span>
                  <h3 style={{ fontSize: 16, margin: "8px 0 4px" }}>{a.title}</h3>
                  <p className="muted" style={{ fontSize: 13.5, margin: 0 }}>
                    {(a.description || "").slice(0, 120)}{a.description && a.description.length > 120 ? "…" : ""}
                  </p>
                </a>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
