import { useState } from "react";
import { useAuth } from "../auth.jsx";
import { firebaseConfigured } from "../firebase.js";

const ROLES = [
  { key: "farmer", icon: "🌾", title: "I'm a Farmer", sub: "Producer / seller" },
  { key: "buyer", icon: "🛍️", title: "I'm a Buyer", sub: "Consumer / buyer" },
];

export default function Login() {
  const { login, register, firebaseLogin } = useAuth();
  const [mode, setMode] = useState("login");
  const [role, setRole] = useState("farmer");
  const [form, setForm] = useState({ full_name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "login") await login(form.email, form.password);
      else await register(form.full_name, form.email, form.password, role);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function google() {
    setError("");
    setBusy(true);
    try {
      await firebaseLogin(role);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-wrap">
      <div className="auth-hero">
        <span className="pill amber" style={{ width: "fit-content" }}>🌍 One-stop AgriTech platform</span>
        <h1>Grow smarter with AI on your side.</h1>
        <p style={{ opacity: 0.9, maxWidth: 440 }}>
          Diagnose plant & animal disease from a photo, get personalized farm advisory,
          trade in the marketplace, read hyper-local agri-news, and chat with an
          expert AI assistant that knows your farm.
        </p>
        <ul>
          <li><span className="dot">🔬</span> AI plant & animal disease diagnosis</li>
          <li><span className="dot">🧭</span> Personalized farm growth advisory</li>
          <li><span className="dot">🛒</span> Marketplace connecting farmers & buyers</li>
          <li><span className="dot">🤖</span> Context-aware streaming AI expert</li>
        </ul>
      </div>

      <div className="auth-form">
        <form className="auth-card card" onSubmit={submit}>
          <h2 style={{ fontSize: 24 }}>{mode === "login" ? "Welcome back 👋" : "Create your account"}</h2>
          <p className="muted" style={{ marginTop: 0 }}>
            {mode === "login" ? "Log in to your dashboard." : "Join as a farmer or a buyer."}
          </p>
          {error && <div className="error-box">{error}</div>}

          {mode === "register" && (
            <div className="field">
              <label>I am joining as a…</label>
              <div className="role-picker">
                {ROLES.map((r) => (
                  <div
                    key={r.key}
                    className={"role-option" + (role === r.key ? " active" : "")}
                    onClick={() => setRole(r.key)}
                  >
                    <span className="role-emoji">{r.icon}</span>
                    <div>
                      <div className="role-title">{r.title}</div>
                      <div className="role-sub">{r.sub}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {mode === "register" && (
            <div className="field">
              <label>Full name</label>
              <input value={form.full_name} onChange={set("full_name")} required placeholder="Ada Farmer" />
            </div>
          )}
          <div className="field">
            <label>Email</label>
            <input type="email" value={form.email} onChange={set("email")} required placeholder="you@farm.com" />
          </div>
          <div className="field">
            <label>Password</label>
            <input type="password" value={form.password} onChange={set("password")} required minLength={6} placeholder="••••••••" />
          </div>
          <button className="btn primary" style={{ width: "100%" }} disabled={busy}>
            {busy ? <span className="spinner" /> : mode === "login" ? "Log in" : "Sign up"}
          </button>

          {firebaseConfigured && (
            <>
              <div className="divider"><span>or</span></div>
              <button type="button" className="btn google" onClick={google} disabled={busy}>
                <span style={{ fontWeight: 800 }}>G</span> Continue with Google
              </button>
              {mode === "register" && (
                <p className="muted" style={{ fontSize: 12, textAlign: "center", margin: "8px 0 0" }}>
                  You'll join as <strong>{role === "farmer" ? "a Farmer" : "a Buyer"}</strong>.
                </p>
              )}
            </>
          )}

          <p className="muted" style={{ textAlign: "center", marginTop: 16, fontSize: 13.5 }}>
            {mode === "login" ? "New here?" : "Already have an account?"}{" "}
            <a
              style={{ color: "var(--green-700)", fontWeight: 700, cursor: "pointer" }}
              onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}
            >
              {mode === "login" ? "Create an account" : "Log in"}
            </a>
          </p>
        </form>
      </div>
    </div>
  );
}
