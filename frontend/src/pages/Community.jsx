import { useEffect, useState } from "react";
import { api } from "../api.js";

const TOPICS = ["all", "general", "crops", "livestock", "pests", "market", "weather", "finance"];

export default function Community() {
  const [posts, setPosts] = useState([]);
  const [topic, setTopic] = useState("all");
  const [showModal, setShowModal] = useState(false);

  function load() {
    api.posts(topic === "all" ? "" : topic).then(setPosts).catch(() => {});
  }
  useEffect(load, [topic]);

  return (
    <div>
      <div className="page-head row spread">
        <div>
          <h1>💬 Community Hub</h1>
          <p>Share knowledge, ask questions, and connect with fellow farmers.</p>
        </div>
        <button className="btn primary" onClick={() => setShowModal(true)}>+ New post</button>
      </div>

      <div className="tag-row">
        {TOPICS.map((t) => <div key={t} className={"tag" + (topic === t ? " active" : "")} onClick={() => setTopic(t)}>{t}</div>)}
      </div>

      {posts.length === 0 ? (
        <div className="card" style={{ textAlign: "center", padding: 40 }}>
          <div style={{ fontSize: 40 }}>🌾</div>
          <p className="muted">No posts in this topic yet. Start the conversation!</p>
        </div>
      ) : (
        posts.map((p) => <PostCard key={p.id} post={p} onChange={load} />)
      )}

      {showModal && <PostModal onClose={() => setShowModal(false)} onCreated={() => { setShowModal(false); load(); }} />}
    </div>
  );
}

function PostCard({ post, onChange }) {
  const [comment, setComment] = useState("");
  const [open, setOpen] = useState(false);

  async function addComment() {
    if (!comment.trim()) return;
    await api.comment(post.id, { body: comment });
    setComment("");
    onChange();
  }

  return (
    <div className="card post">
      <div className="row spread">
        <div className="row" style={{ gap: 8 }}>
          <span className="pill">{post.topic}</span>
          {post.author_name && (
            <span className="muted" style={{ fontSize: 12.5 }}>
              by <strong>{post.author_name}</strong>{" "}
              <span className={"role-badge " + (post.author_role || "farmer")}>
                {post.author_role === "buyer" ? "🛍️ Buyer" : "🌾 Farmer"}
              </span>
            </span>
          )}
        </div>
        <span className="muted" style={{ fontSize: 12 }}>{new Date(post.created_at).toLocaleDateString()}</span>
      </div>
      <div className="post-title" style={{ marginTop: 8 }}>{post.title}</div>
      <p className="muted">{post.body}</p>
      <div className="row" style={{ gap: 18 }}>
        <a className="muted" style={{ cursor: "pointer" }} onClick={() => api.like(post.id).then(onChange)}>❤️ {post.likes}</a>
        <a className="muted" style={{ cursor: "pointer" }} onClick={() => setOpen(!open)}>💬 {post.comments?.length || 0} comments</a>
      </div>
      {open && (
        <div style={{ marginTop: 12 }}>
          {post.comments?.map((c) => (
            <div key={c.id} className="comment">
              <strong>{c.author_name}</strong>{" "}
              <span className={"role-badge " + (c.author_role || "farmer")}>
                {c.author_role === "buyer" ? "🛍️" : "🌾"}
              </span> · {c.body}
            </div>
          ))}
          <div className="row" style={{ marginTop: 10 }}>
            <input value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Write a comment…" onKeyDown={(e) => e.key === "Enter" && addComment()} />
            <button className="btn primary small" onClick={addComment}>Send</button>
          </div>
        </div>
      )}
    </div>
  );
}

function PostModal({ onClose, onCreated }) {
  const [form, setForm] = useState({ title: "", body: "", topic: "general" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try { await api.createPost(form); onCreated(); }
    catch (err) { setError(err.message); } finally { setBusy(false); }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <form className="modal" onClick={(e) => e.stopPropagation()} onSubmit={submit}>
        <h2 style={{ fontSize: 22 }}>Create a post</h2>
        {error && <div className="error-box">{error}</div>}
        <div className="field"><label>Title</label><input value={form.title} onChange={set("title")} required /></div>
        <div className="field"><label>Topic</label>
          <select value={form.topic} onChange={set("topic")}>{TOPICS.filter((t) => t !== "all").map((t) => <option key={t}>{t}</option>)}</select>
        </div>
        <div className="field"><label>Body</label><textarea rows={4} value={form.body} onChange={set("body")} required /></div>
        <div className="row spread">
          <button type="button" className="btn outline" onClick={onClose}>Cancel</button>
          <button className="btn primary" disabled={busy}>{busy ? "Posting…" : "Publish"}</button>
        </div>
      </form>
    </div>
  );
}
