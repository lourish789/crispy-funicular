"""Groq LLM integration (llama-3.1-8b-instant) with streaming + graceful fallback."""
from __future__ import annotations

import json
from collections.abc import Iterator

from app.config import settings

try:  # groq is optional at import time so the app boots without a key
    from groq import Groq
except Exception:  # pragma: no cover
    Groq = None  # type: ignore


def _client():
    if not settings.groq_enabled or Groq is None:
        return None
    try:
        return Groq(api_key=settings.groq_api_key)
    except Exception:
        return None


def chat_completion(messages: list[dict], temperature: float = 0.4) -> str:
    """Non-streaming completion. Returns text, or a graceful fallback string."""
    client = _client()
    if client is None:
        return _offline_reply(messages)
    try:
        resp = client.chat.completions.create(
            model=settings.groq_model,
            messages=messages,
            temperature=temperature,
            max_tokens=1024,
        )
        return resp.choices[0].message.content or ""
    except Exception as exc:  # network / rate-limit / auth failures
        return _offline_reply(messages, error=str(exc))


def stream_completion(
    messages: list[dict], temperature: float = 0.5
) -> Iterator[str]:
    """Yield text tokens as they arrive from Groq. Falls back to a chunked reply."""
    client = _client()
    if client is None:
        yield from _offline_stream(messages)
        return
    try:
        stream = client.chat.completions.create(
            model=settings.groq_model,
            messages=messages,
            temperature=temperature,
            max_tokens=1024,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    except Exception as exc:  # pragma: no cover
        yield from _offline_stream(messages, error=str(exc))


def json_completion(messages: list[dict], temperature: float = 0.2) -> dict:
    """Ask the model for JSON and parse it defensively."""
    client = _client()
    if client is None:
        return {}
    try:
        resp = client.chat.completions.create(
            model=settings.groq_model,
            messages=messages,
            temperature=temperature,
            max_tokens=1024,
            response_format={"type": "json_object"},
        )
        return json.loads(resp.choices[0].message.content or "{}")
    except Exception:
        return {}


def vision_completion(image_data_urls: list[str], prompt: str) -> dict:
    """Send image(s) to Groq's vision model and request structured JSON."""
    client = _client()
    if client is None:
        return {}
    content: list[dict] = [{"type": "text", "text": prompt}]
    for url in image_data_urls[:4]:  # cap frames sent to the vision model
        content.append({"type": "image_url", "image_url": {"url": url}})
    try:
        resp = client.chat.completions.create(
            model=settings.groq_vision_model,
            messages=[{"role": "user", "content": content}],
            temperature=0.2,
            max_tokens=1024,
        )
        text = resp.choices[0].message.content or "{}"
        return _extract_json(text)
    except Exception:
        return {}


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.split("\n", 1)[-1] if "\n" in text else text
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return {}
    return {}


# ---------- Offline / degraded-mode replies ----------
def _last_user(messages: list[dict]) -> str:
    for m in reversed(messages):
        if m.get("role") == "user":
            return m.get("content", "")
    return ""


def _offline_reply(messages: list[dict], error: str | None = None) -> str:
    q = _last_user(messages)
    note = (
        "The AI service is not configured yet (set GROQ_API_KEY). "
        if error is None
        else "The AI service is temporarily unavailable. "
    )
    return (
        f"{note}Here is general agronomic guidance for your question: "
        f'"{q[:180]}". Ensure balanced NPK nutrition, monitor soil moisture, '
        "scout weekly for pests and disease, rotate crops each season, and keep "
        "records of yields and costs so we can refine recommendations over time."
    )


def _offline_stream(messages: list[dict], error: str | None = None) -> Iterator[str]:
    for word in _offline_reply(messages, error).split(" "):
        yield word + " "
