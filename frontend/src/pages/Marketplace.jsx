import { useEffect, useState } from "react";
import { useAuth } from "../auth.jsx";
import { api } from "../api.js";

const CATEGORIES = ["all", "produce", "tools", "fertilizers", "seeds", "livestock", "machinery"];
const CAT_IMG = {
  produce: "https://images.unsplash.com/photo-1518977676601-b53f82aba655?auto=format&fit=crop&w=600&q=60",
  tools: "https://images.unsplash.com/photo-1416879595882-3373a0480b5b?auto=format&fit=crop&w=600&q=60",
  fertilizers: "https://images.unsplash.com/photo-1592982537447-7440770cbfc9?auto=format&fit=crop&w=600&q=60",
  seeds: "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?auto=format&fit=crop&w=600&q=60",
  livestock: "https://images.unsplash.com/photo-1500595046743-cd271d694d30?auto=format&fit=crop&w=600&q=60",
  machinery: "https://images.unsplash.com/photo-1605000797499-95a51c5269ae?auto=format&fit=crop&w=600&q=60",
};
const DEFAULT_IMG = "https://images.unsplash.com/photo-1607921090707-c2f6c3f2d1c5?auto=format&fit=crop&w=600&q=60";

export default function Marketplace() {
  const { user } = useAuth();
  const isFarmer = user?.role !== "buyer";
  const [listings, setListings] = useState([]);
  const [feed, setFeed] = useState([]);
  const [cat, setCat] = useState("all");
  const [search, setSearch] = useState("");
  const [showModal, setShowModal] = useState(false);

  function load() {
    const parts = [];
    if (cat !== "all") parts.push(`category=${cat}`);
    if (search) parts.push(`search=${encodeURIComponent(search)}`);
    api.listings(parts.length ? `?${parts.join("&")}` : "").then(setListings).catch(() => {});
    api.marketFeed().then(setFeed).catch(() => {});
  }
  useEffect(load, [cat]);

  return (
    <div>
      <div className="page-head row spread">
        <div>
          <h1>🛒 Agribusiness Marketplace</h1>
          <p>{isFarmer
            ? "Sell your produce & inputs, and see what buyers are looking for."
            : "Discover produce & inputs for sale, and post what you're looking to buy."}</p>
        </div>
        <button className="btn primary" onClick={() => setShowModal(true)}>
          {isFarmer ? "+ Sell something" : "+ Post a request"}
        </button>
      </div>

      {feed.length > 0 && (
        <div style={{ marginBottom: 26 }}>
          <h2 style={{ fontSize: 18, marginBottom: 12 }}>
            {isFarmer ? "🔔 Buyers looking for produce" : "🌱 Fresh from farmers"}
          </h2>
          <div className="grid cols-3">
            {feed.slice(0, 3).map((l) => (
              <div key={l.id} className="card listing-card">
                <div className="row spread">
                  <span className={"pill" + (l.listing_type === "buy" ? " amber" : "")}>
                    {l.listing_type === "buy" ? "Wanted" : l.category}
                  </span>
                </div>
                <h3 style={{ margin: "8px 0 4px" }}>{l.title}</h3>
                <p className="muted" style={{ fontSize: 13.5, margin: "0 0 8px" }}>{l.description.slice(0, 90)}</p>
                <div className="row spread">
                  <span className="listing-price">{l.currency} {l.price}<span className="muted" style={{ fontSize: 13, fontWeight: 400 }}>/{l.unit}</span></span>
                  <span className="muted" style={{ fontSize: 12 }}>📍 {l.location || "—"}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="row" style={{ marginBottom: 14 }}>
        <input placeholder="Search listings…" value={search} onChange={(e) => setSearch(e.target.value)} onKeyDown={(e) => e.key === "Enter" && load()} style={{ maxWidth: 320 }} />
        <button className="btn outline" onClick={load}>Search</button>
      </div>

      <div className="tag-row">
        {CATEGORIES.map((c) => (
          <div key={c} className={"tag" + (cat === c ? " active" : "")} onClick={() => setCat(c)}>{c}</div>
        ))}
      </div>

      {listings.length === 0 ? (
        <div className="card" style={{ textAlign: "center", padding: 40 }}>
          <div style={{ fontSize: 40 }}>🧺</div>
          <p className="muted">No listings yet. Be the first to post!</p>
        </div>
      ) : (
        <div className="grid cols-3">
          {listings.map((l) => (
            <div key={l.id} className="card listing-card">
              <img src={l.image_url || CAT_IMG[l.category] || DEFAULT_IMG} alt="" onError={(e) => (e.target.src = DEFAULT_IMG)} />
              <div className="row spread">
                <span className={"pill" + (l.listing_type === "buy" ? " amber" : "")}>{l.listing_type === "buy" ? "Wanted" : l.category}</span>
                {l.seller_id === user?.id && (
                  <a className="muted" style={{ cursor: "pointer", fontSize: 13 }} onClick={() => api.deleteListing(l.id).then(load)}>Delete</a>
                )}
              </div>
              <h3 style={{ margin: "8px 0 4px" }}>{l.title}</h3>
              <p className="muted" style={{ fontSize: 13.5, margin: "0 0 8px" }}>{l.description.slice(0, 90)}</p>
              <div className="row spread">
                <span className="listing-price">{l.currency} {l.price}<span className="muted" style={{ fontSize: 13, fontWeight: 400 }}>/{l.unit}</span></span>
                <span className="muted" style={{ fontSize: 12 }}>📍 {l.location || "—"}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {showModal && <ListingModal isFarmer={isFarmer} onClose={() => setShowModal(false)} onCreated={() => { setShowModal(false); load(); }} />}
    </div>
  );
}

function ListingModal({ isFarmer, onClose, onCreated }) {
  const [form, setForm] = useState({
    title: "", description: "", category: "produce",
    price: "", currency: "USD", unit: "kg", quantity: 1, location: "", image_url: "",
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api.createListing({ ...form, price: parseFloat(form.price), quantity: parseFloat(form.quantity) || 1 });
      onCreated();
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={submit}>
        <h2 style={{ fontSize: 22 }}>{isFarmer ? "Sell a product" : "Post a buy request"}</h2>
        <p className="muted" style={{ marginTop: 0, fontSize: 13 }}>
          {isFarmer
            ? "Listed as a sell offer visible to buyers."
            : "Listed as a wanted request visible to farmers."}
        </p>
        {error && <div className="error-box">{error}</div>}
        <div className="field"><label>Title</label><input value={form.title} onChange={set("title")} required placeholder={isFarmer ? "Fresh organic tomatoes" : "Looking for 500kg maize"} /></div>
        <div className="field"><label>Description</label><textarea rows={3} value={form.description} onChange={set("description")} required /></div>
        <div className="row">
          <div className="field" style={{ flex: 1 }}><label>Category</label>
            <select value={form.category} onChange={set("category")}>
              {CATEGORIES.filter((c) => c !== "all").map((c) => <option key={c}>{c}</option>)}
            </select>
          </div>
        </div>
        <div className="row">
          <div className="field" style={{ flex: 1 }}><label>Price</label><input type="number" step="0.01" value={form.price} onChange={set("price")} required /></div>
          <div className="field" style={{ width: 90 }}><label>Currency</label><input value={form.currency} onChange={set("currency")} /></div>
          <div className="field" style={{ width: 90 }}><label>Unit</label><input value={form.unit} onChange={set("unit")} /></div>
        </div>
        <div className="field"><label>Image URL (optional)</label><input value={form.image_url} onChange={set("image_url")} placeholder="https://…" /></div>
        <div className="row spread" style={{ marginTop: 8 }}>
          <button type="button" className="btn outline" onClick={onClose}>Cancel</button>
          <button className="btn primary" disabled={busy}>{busy ? "Posting…" : "Post listing"}</button>
        </div>
      </form>
    </div>
  );
}
