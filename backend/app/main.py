"""AgriTech Suite — FastAPI application entry point."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import SessionLocal, init_db
from app.routers import (
    advisory,
    auth,
    chat,
    community,
    diagnosis,
    marketplace,
    news,
)
from app.services import rag_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        created = rag_service.seed_knowledge_base(db)
        if created:
            print(f"[AgriTech] Seeded {created} knowledge chunks for RAG.")
    finally:
        db.close()
    yield


app = FastAPI(
    title="AgriTech Suite API",
    description="One-stop agricultural platform: diagnosis, advisory, news, "
    "marketplace, community, and a context-aware AI assistant.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth, diagnosis, advisory, news, marketplace, community, chat):
    app.include_router(r.router)


@app.get("/")
def root():
    return {"name": "AgriTech Suite API", "status": "ok", "version": "1.0.0"}


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "llm": "groq:configured" if settings.groq_enabled else "offline-fallback",
        "embeddings": "gemini:configured"
        if settings.gemini_enabled
        else "local-fallback",
        "news": "configured" if settings.news_api_key else "demo",
    }
