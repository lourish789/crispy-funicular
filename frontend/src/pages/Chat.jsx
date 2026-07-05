import { useEffect, useRef, useState } from "react";
import { api, getToken } from "../api.js";

const SUGGESTIONS = [
  "How do I improve my maize yield this season?",
  "My tomato leaves have brown spots — what should I do?",
  "What crops should I diversify into?",
  "How can I reduce post-harvest losses?",
];

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const scrollRef = useRef();
  const session = "default";

  useEffect(() => {
    api.chatHistory(session)
      .then((h) => setMessages(h.map((m) => ({ role: m.role, content: m.content }))))
      .catch(() => {});
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  async function send(text) {
    const message = (text ?? input).trim();
    if (!message || streaming) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: message }, { role: "assistant", content: "" }]);
    setStreaming(true);

    try {
      const res = await fetch(`${api.base}/api/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify({ message, session_id: session }),
      });
      if (!res.ok || !res.body) throw new Error("Stream failed");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split("\n\n");
        buffer = events.pop() || "";
        for (const evt of events) {
          const line = evt.split("\n").find((l) => l.startsWith("data:"));
          if (!line) continue;
          const isToken = evt.includes("event: token");
          if (!isToken) continue;
          try {
            const data = JSON.parse(line.slice(5).trim());
            if (data.t) appendToLast(data.t);
          } catch { /* ignore partials */ }
        }
      }
    } catch {
      appendToLast("\n⚠️ The assistant is temporarily unavailable. Please try again.");
    } finally {
      setStreaming(false);
    }
  }

  function appendToLast(chunk) {
    setMessages((m) => {
      const copy = [...m];
      copy[copy.length - 1] = { role: "assistant", content: copy[copy.length - 1].content + chunk };
      return copy;
    });
  }

  return (
    <div className="chat-wrap">
      <div className="page-head">
        <h1>🤖 Agro — your AI farm expert</h1>
        <p>Context-aware, streaming responses personalized to your farm profile.</p>
      </div>

      <div className="chat-scroll" ref={scrollRef}>
        {messages.length === 0 ? (
          <div className="chat-empty">
            <div style={{ fontSize: 46 }}>🌱</div>
            <h3>Ask me anything about your farm</h3>
            <p className="muted">I know your crops, location and history.</p>
            <div className="suggest">
              {SUGGESTIONS.map((s) => <button key={s} onClick={() => send(s)}>{s}</button>)}
            </div>
          </div>
        ) : (
          messages.map((m, i) => (
            <div key={i} className={"bubble " + (m.role === "user" ? "user" : "bot")}>
              {m.content}
              {m.role === "assistant" && streaming && i === messages.length - 1 && !m.content && <span className="blink" />}
            </div>
          ))
        )}
      </div>

      <div className="chat-input">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="Type your question…"
          disabled={streaming}
        />
        <button className="btn primary" onClick={() => send()} disabled={streaming || !input.trim()}>
          {streaming ? <span className="spinner" /> : "Send"}
        </button>
      </div>
    </div>
  );
}
