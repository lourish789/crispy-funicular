"""SQLAlchemy ORM models — the full AgriTech Suite schema."""
from __future__ import annotations

import datetime as dt
import json

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


# User roles
ROLE_FARMER = "farmer"  # producer / seller
ROLE_BUYER = "buyer"  # consumer / buyer
VALID_ROLES = {ROLE_FARMER, ROLE_BUYER}


def normalize_role(role: str | None) -> str:
    r = (role or "").strip().lower()
    if r in {"buyer", "consumer", "buy"}:
        return ROLE_BUYER
    return ROLE_FARMER  # default: producer/farmer


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)

    # Role: "farmer" (producer/seller) or "buyer" (consumer). Drives which
    # marketplace actions and feeds a user sees.
    role: Mapped[str] = mapped_column(String(20), default="farmer", index=True)
    # Set when the account was created/linked via Firebase auth.
    firebase_uid: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)

    # Farm profile / personalization metadata
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    farm_size_hectares: Mapped[float | None] = mapped_column(Float, nullable=True)
    primary_crops: Mapped[str | None] = mapped_column(Text, nullable=True)  # CSV
    livestock: Mapped[str | None] = mapped_column(Text, nullable=True)  # CSV
    farming_experience_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    soil_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    irrigation: Mapped[str | None] = mapped_column(String(120), nullable=True)
    goals: Mapped[str | None] = mapped_column(Text, nullable=True)

    diagnoses: Mapped[list[Diagnosis]] = relationship(back_populates="user")
    listings: Mapped[list[Listing]] = relationship(back_populates="seller")
    posts: Mapped[list[Post]] = relationship(back_populates="author")
    chat_messages: Mapped[list[ChatMessage]] = relationship(back_populates="user")

    def profile_summary(self) -> str:
        """Compact natural-language profile injected into the LLM context window."""
        parts = [f"Name: {self.full_name}"]
        if self.location:
            parts.append(f"Location: {self.location}")
        if self.country:
            parts.append(f"Country: {self.country}")
        if self.farm_size_hectares:
            parts.append(f"Farm size: {self.farm_size_hectares} ha")
        if self.primary_crops:
            parts.append(f"Primary crops: {self.primary_crops}")
        if self.livestock:
            parts.append(f"Livestock: {self.livestock}")
        if self.farming_experience_years is not None:
            parts.append(f"Experience: {self.farming_experience_years} years")
        if self.soil_type:
            parts.append(f"Soil: {self.soil_type}")
        if self.irrigation:
            parts.append(f"Irrigation: {self.irrigation}")
        if self.goals:
            parts.append(f"Goals: {self.goals}")
        return " | ".join(parts)


class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    media_type: Mapped[str] = mapped_column(String(20))  # image | video
    subject: Mapped[str] = mapped_column(String(20), default="plant")  # plant | animal
    crop_hint: Mapped[str | None] = mapped_column(String(120), nullable=True)
    disease_name: Mapped[str] = mapped_column(String(255))
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    cause: Mapped[str] = mapped_column(Text)
    immediate_solution: Mapped[str] = mapped_column(Text)
    prevention_strategies: Mapped[str] = mapped_column(Text)  # JSON array as text
    raw: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)

    user: Mapped[User] = relationship(back_populates="diagnoses")

    def prevention_list(self) -> list[str]:
        try:
            return json.loads(self.prevention_strategies)
        except (json.JSONDecodeError, TypeError):
            return [self.prevention_strategies] if self.prevention_strategies else []


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(80), index=True)  # produce/tools/...
    listing_type: Mapped[str] = mapped_column(String(20), default="sell")  # sell | buy
    price: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    unit: Mapped[str] = mapped_column(String(40), default="unit")
    quantity: Mapped[float] = mapped_column(Float, default=1)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)

    seller: Mapped[User] = relationship(back_populates="listings")


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    author_name: Mapped[str] = mapped_column(String(255), default="")
    author_role: Mapped[str] = mapped_column(String(20), default="farmer")
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    topic: Mapped[str] = mapped_column(String(80), index=True, default="general")
    likes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)

    author: Mapped[User] = relationship(back_populates="posts")
    comments: Mapped[list[Comment]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    author_name: Mapped[str] = mapped_column(String(255))
    author_role: Mapped[str] = mapped_column(String(20), default="farmer")
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)

    post: Mapped[Post] = relationship(back_populates="comments")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    role: Mapped[str] = mapped_column(String(20))  # user | assistant
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)

    user: Mapped[User] = relationship(back_populates="chat_messages")


class KnowledgeChunk(Base):
    """Vector store for RAG. Embeddings produced by Gemini, stored as JSON floats."""

    __tablename__ = "knowledge_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(120), default="agri-kb")
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list] = mapped_column(JSON)  # list[float]
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)
