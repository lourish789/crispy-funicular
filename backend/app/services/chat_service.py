"""Context-aware chatbot orchestration: persona + profile + history + RAG."""
from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy.orm import Session

from app.models import ChatMessage, User
from app.services import llm_service, rag_service

SYSTEM_PERSONA = (
    "You are Agro, a highly knowledgeable and empathetic agricultural expert and "
    "advisor. You speak warmly and practically, like a trusted extension officer who "
    "understands smallholder realities. Give specific, actionable, locally-relevant "
    "guidance. Be encouraging, cite agronomic reasoning, and keep answers focused. "
    "When you use the provided knowledge context, integrate it naturally."
)


def build_messages(db: Session, user: User, session_id: str, message: str) -> list[dict]:
    """Assemble the full context window: persona + profile + RAG + history + query."""
    context_snippets = rag_service.retrieve(db, message, top_k=4)
    context_block = (
        "\n".join(f"- {s}" for s in context_snippets)
        if context_snippets
        else "(no specific knowledge retrieved)"
    )

    system = (
        f"{SYSTEM_PERSONA}\n\n"
        f"FARMER PROFILE (speak specifically to this):\n{user.profile_summary()}\n\n"
        f"RELEVANT AGRONOMIC KNOWLEDGE:\n{context_block}"
    )

    messages: list[dict] = [{"role": "system", "content": system}]

    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user.id, ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(10)
        .all()
    )
    for m in reversed(history):
        messages.append({"role": m.role, "content": m.content})

    messages.append({"role": "user", "content": message})
    return messages


def persist(db: Session, user: User, session_id: str, role: str, content: str) -> None:
    db.add(
        ChatMessage(
            user_id=user.id, session_id=session_id, role=role, content=content
        )
    )
    db.commit()


def stream_reply(
    db: Session, user: User, session_id: str, message: str
) -> Iterator[str]:
    """Persist the user's message, stream the assistant reply, persist the full reply."""
    persist(db, user, session_id, "user", message)
    messages = build_messages(db, user, session_id, message)

    collected: list[str] = []
    for token in llm_service.stream_completion(messages):
        collected.append(token)
        yield token

    full = "".join(collected).strip()
    if full:
        persist(db, user, session_id, "assistant", full)
