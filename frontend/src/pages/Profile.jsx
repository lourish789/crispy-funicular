import { useState } from "react";
import { useAuth } from "../auth.jsx";
import { api } from "../api.js";

export default function Profile() {
  const { user, setUser } = useAuth();
  const [form, setForm] = useState({
    full_name: user?.full_name || "",
    location: user?.location || "",
    country: user?.country || "",
    farm_size_hectares: user?.farm_size_hectares || "",
    primary_crops: user?.primary_crops || "",
    livestock: user?.livestock || "",
    farming_experience_years: user?.farming_experience_years || "",
    soil_type: user?.soil_type || "",
    irrigation: user?.irrigation || "",
    goals: user?.goals || "",
  });
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function save(e) {
    e.preventDefault();
    setBusy(true);
    setSaved(false);
    const payload = {
      ...form,
      farm_size_hectares: form.farm_size_hectares ? parseFloat(form.farm_size_hectares) : null,
      farming_experience_years: form.farming_experience_years ? parseInt(form.farming_experience_years) : null,
    };
    try {
      const updated = await api.updateProfile(payload);
      setUser(updated);
      setSaved(true);
    } finally { setBusy(false); }
  }

  return (
    <div style={{ maxWidth: 720 }}>
      <div className="page-head">
        <h1>👤 Farm Profile</h1>
        <p>This context personalizes your advisory, news, and AI assistant.</p>
      </div>

      <form className="card" onSubmit={save}>
        {saved && <div className="error-box" style={{ background: "#e7f6ec", color: "var(--green-700)" }}>✔ Profile saved.</div>}
        <div className="grid cols-2">
          <div className="field"><label>Full name</label><input value={form.full_name} onChange={set("full_name")} /></div>
          <div className="field"><label>Location (city/state)</label><input value={form.location} onChange={set("location")} placeholder="Ibadan, Oyo" /></div>
          <div className="field"><label>Country</label><input value={form.country} onChange={set("country")} placeholder="Nigeria" /></div>
          <div className="field"><label>Farm size (hectares)</label><input type="number" step="0.1" value={form.farm_size_hectares} onChange={set("farm_size_hectares")} /></div>
          <div className="field"><label>Primary crops (comma-separated)</label><input value={form.primary_crops} onChange={set("primary_crops")} placeholder="maize, tomato, cassava" /></div>
          <div className="field"><label>Livestock (comma-separated)</label><input value={form.livestock} onChange={set("livestock")} placeholder="poultry, goats" /></div>
          <div className="field"><label>Experience (years)</label><input type="number" value={form.farming_experience_years} onChange={set("farming_experience_years")} /></div>
          <div className="field"><label>Soil type</label><input value={form.soil_type} onChange={set("soil_type")} placeholder="loamy" /></div>
          <div className="field"><label>Irrigation</label><input value={form.irrigation} onChange={set("irrigation")} placeholder="drip / rain-fed" /></div>
        </div>
        <div className="field"><label>Goals</label><textarea rows={3} value={form.goals} onChange={set("goals")} placeholder="What do you want to achieve this year?" /></div>
        <button className="btn primary" disabled={busy}>{busy ? "Saving…" : "Save profile"}</button>
      </form>
    </div>
  );
}
