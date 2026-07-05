"""Context-aware streaming chatbot endpoints (Server-Sent Events)."""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import ChatMessage, User
from app.schemas import ChatMessageOut, ChatRequest
from app.security import decode_token
from app.services import chat_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _sse(event: str, data: dict | str) -> str:
    payload = data if isinstance(data, str) else json.dumps(data)
    return f"event: {event}\ndata: {payload}\n\n"


def _stream(db: Session, user: User, session_id: str, message: str):
    yield _sse("start", {"session_id": session_id})
    try:
        for token in chat_service.stream_reply(db, user, session_id, message):
            yield _sse("token", {"t": token})
    except Exception as exc:  # never break the stream contract
        yield _sse("error", {"message": str(exc)})
    yield _sse("done", {"session_id": session_id})


@router.post("/stream")
def chat_stream_post(
    payload: ChatRequest,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Streaming chat for fetch()-based clients that can send an auth header."""
    return StreamingResponse(
        _stream(db, current, payload.session_id, payload.message),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/stream")
def chat_stream_get(
    message: str = Query(...),
    session_id: str = Query("default"),
    token: str = Query(..., description="JWT — EventSource cannot send headers"),
    db: Session = Depends(get_db),
):
    """SSE endpoint for browser EventSource (auth passed as query param)."""
    email = decode_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Unknown user")
    return StreamingResponse(
        _stream(db, user, session_id, message),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/history", response_model=list[ChatMessageOut])
def history(
    session_id: str = "default",
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current.id, ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(200)
        .all()
    )
