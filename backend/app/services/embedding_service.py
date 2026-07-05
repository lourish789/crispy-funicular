"""Google Gemini Embedding integration — used EXCLUSIVELY for vectorization / RAG.

Per project requirement: Gemini is used only for embeddings, never for generation.
"""
from __future__ import annotations

import hashlib
import math

from app.config import settings

try:
    import google.generativeai as genai
except Exception:  # pragma: no cover
    genai = None  # type: ignore

_configured = False


def _ensure_configured() -> bool:
    global _configured
    if not settings.gemini_enabled or genai is None:
        return False
    if not _configured:
        try:
            genai.configure(api_key=settings.gemini_api_key)
            _configured = True
        except Exception:
            return False
    return _configured


def embed_text(text: str, task_type: str = "retrieval_document") -> list[float]:
    """Return an embedding vector for `text`.

    Falls back to a deterministic local hashing embedding when Gemini is
    unavailable, so semantic search still functions (with reduced quality)
    and the app never crashes.
    """
    text = (text or "").strip()
    if not text:
        return [0.0] * 256
    if _ensure_configured():
        try:
            result = genai.embed_content(
                model=settings.gemini_embedding_model,
                content=text,
                task_type=task_type,
            )
            emb = result["embedding"]
            if isinstance(emb, dict):  # some SDK versions nest it
                emb = emb.get("values", [])
            if emb:
                return list(emb)
        except Exception:
            pass
    return _fallback_embedding(text)


def embed_query(text: str) -> list[float]:
    return embed_text(text, task_type="retrieval_query")


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    dot = sum(a[i] * b[i] for i in range(n))
    na = math.sqrt(sum(a[i] * a[i] for i in range(n)))
    nb = math.sqrt(sum(b[i] * b[i] for i in range(n)))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _fallback_embedding(text: str, dim: int = 256) -> list[float]:
    """Deterministic bag-of-hashed-tokens embedding for offline/degraded mode."""
    vec = [0.0] * dim
    for token in text.lower().split():
        h = int(hashlib.md5(token.encode()).hexdigest(), 16)
        vec[h % dim] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]
