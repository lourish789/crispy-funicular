import { useEffect, useRef, useState } from "react";
import { api } from "../api.js";

export default function Diagnosis() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState("");
  const [subject, setSubject] = useState("plant");
  const [cropHint, setCropHint] = useState("");
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState([]);
  const inputRef = useRef();

  useEffect(() => { api.diagnosisHistory().then(setHistory).catch(() => {}); }, [result]);

  function pick(f) {
    if (!f) return;
    setFile(f);
    setResult(null);
    setError("");
    setPreview(f.type.startsWith("image") ? URL.createObjectURL(f) : "");
  }

  async function submit() {
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      const form = new FormData();
      form.append("file", file);
      form.append("subject", subject);
      if (cropHint) form.append("crop_hint", cropHint);
      const res = await api.diagnose(form);
      setResult(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="page-head">
        <h1>🔬 Plant & Animal Disease Diagnosis</h1>
        <p>Upload an image or a short video. An open-source computer-vision model detects the disease locally, then our AI expands it into a treatment plan.</p>
      </div>

      <div className="grid cols-2">
        <div className="card">
          <label>What are you diagnosing?</label>
          <div className="tag-row" style={{ marginBottom: 18 }}>
            <div className={"tag" + (subject === "plant" ? " active" : "")} onClick={() => setSubject("plant")}>🌿 Plant / Crop</div>
            <div className={"tag" + (subject === "animal" ? " active" : "")} onClick={() => setSubject("animal")}>🐄 Animal / Livestock</div>
          </div>
          <div
            className="dropzone"
            onClick={() => inputRef.current.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => { e.preventDefault(); pick(e.dataTransfer.files[0]); }}
          >
            <div style={{ fontSize: 40 }}>📷</div>
            <strong>Click or drop an image / video</strong>
            <p className="muted" style={{ margin: "6px 0 0" }}>JPG, PNG, MP4 · up to 25MB</p>
            <input ref={inputRef} type="file" accept="image/*,video/*" hidden onChange={(e) => pick(e.target.files[0])} />
          </div>
          {preview && <img className="preview-img" src={preview} alt="preview" />}
          {file && !preview && <p className="muted">🎬 {file.name} (video ready for frame sampling)</p>}

          <div className="field" style={{ marginTop: 16 }}>
            <label>{subject === "animal" ? "Animal (optional)" : "Crop (optional — improves accuracy)"}</label>
            <input value={cropHint} onChange={(e) => setCropHint(e.target.value)} placeholder={subject === "animal" ? "e.g. cattle, goat, poultry" : "e.g. tomato, maize, cassava"} />
          </div>
          {error && <div className="error-box">{error}</div>}
          <button className="btn primary" style={{ width: "100%" }} disabled={!file || busy} onClick={submit}>
            {busy ? <><span className="spinner" /> Analysing…</> : "Diagnose now"}
          </button>
        </div>

        <div className="card diag-result">
          {!result ? (
            <div style={{ textAlign: "center", padding: "30px 0", color: "var(--muted)" }}>
              <div style={{ fontSize: 40 }}>🌿</div>
              <p>Your diagnosis will appear here.</p>
            </div>
          ) : (
            <div>
              <div className="row" style={{ gap: 8 }}>
                <span className="pill">Diagnosis</span>
                {result.detector === "open-source-cv" && (
                  <span className="pill amber">🧠 Open-source CV</span>
                )}
              </div>
              <h2 style={{ marginTop: 10 }}>{result.disease_name}</h2>
              {result.model && (
                <p className="muted" style={{ fontSize: 12, margin: "-6px 0 4px" }}>model: {result.model}</p>
              )}
              <div className="row" style={{ margin: "6px 0 14px" }}>
                <div style={{ flex: 1 }}>
                  <div className="confidence-bar"><div className="confidence-fill" style={{ width: `${Math.round(result.confidence * 100)}%` }} /></div>
                </div>
                <span className="muted" style={{ fontSize: 13 }}>{Math.round(result.confidence * 100)}% confidence</span>
              </div>
              <h3>🧪 Cause</h3>
              <p className="muted">{result.cause}</p>
              <h3>💊 Immediate solution</h3>
              <p className="muted">{result.immediate_solution}</p>
              <h3>🛡️ Prevention strategies</h3>
              <ul className="clean">
                {result.prevention_strategies.map((s, i) => <li key={i}>{s}</li>)}
              </ul>
            </div>
          )}
        </div>
      </div>

      {history.length > 0 && (
        <>
          <h2 style={{ fontSize: 20, margin: "28px 0 14px" }}>Recent diagnoses</h2>
          <div className="grid cols-3">
            {history.slice(0, 6).map((h) => (
              <div key={h.id} className="card">
                <span className="pill">{h.media_type}</span>
                <h3 style={{ margin: "8px 0 4px" }}>{h.disease_name}</h3>
                <p className="muted" style={{ fontSize: 13, margin: 0 }}>{new Date(h.created_at).toLocaleString()}</p>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
