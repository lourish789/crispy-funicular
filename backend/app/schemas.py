"""Pydantic request/response schemas."""
from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------- Auth & Users ----------
class UserBase(BaseModel):
    email: EmailStr
    full_name: str


class UserCreate(UserBase):
    password: str = Field(min_length=6)


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    location: str | None = None
    country: str | None = None
    farm_size_hectares: float | None = None
    primary_crops: str | None = None
    livestock: str | None = None
    farming_experience_years: int | None = None
    soil_type: str | None = None
    irrigation: str | None = None
    goals: str | None = None


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    location: str | None = None
    country: str | None = None
    farm_size_hectares: float | None = None
    primary_crops: str | None = None
    livestock: str | None = None
    farming_experience_years: int | None = None
    soil_type: str | None = None
    irrigation: str | None = None
    goals: str | None = None
    created_at: dt.datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ---------- Diagnosis ----------
class DiagnosisResult(BaseModel):
    disease_name: str
    cause: str
    immediate_solution: str
    prevention_strategies: list[str]
    confidence: float = 0.0
    detector: str | None = None  # open-source-cv | groq-vision | heuristic
    model: str | None = None


class DiagnosisOut(DiagnosisResult):
    model_config = ConfigDict(from_attributes=True)
    id: int
    media_type: str
    subject: str = "plant"
    crop_hint: str | None = None
    created_at: dt.datetime


# ---------- Advisory ----------
class AdvisoryOut(BaseModel):
    generated_at: dt.datetime
    summary: str
    expand: list[str]
    optimize: list[str]
    improve: list[str]
    give_up: list[str]
    metrics: dict


# ---------- News ----------
class NewsArticle(BaseModel):
    title: str
    description: str | None = None
    url: str | None = None
    source: str | None = None
    published_at: str | None = None
    image_url: str | None = None
    scope: str = "global"  # global | local


class NewsResponse(BaseModel):
    location: str | None = None
    cached: bool = False
    articles: list[NewsArticle]


# ---------- Marketplace ----------
class ListingCreate(BaseModel):
    title: str
    description: str
    category: str
    listing_type: str = "sell"
    price: float
    currency: str = "USD"
    unit: str = "unit"
    quantity: float = 1
    location: str | None = None
    image_url: str | None = None


class ListingOut(ListingCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    seller_id: int
    status: str
    created_at: dt.datetime


# ---------- Community ----------
class PostCreate(BaseModel):
    title: str
    body: str
    topic: str = "general"


class CommentCreate(BaseModel):
    body: str


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    author_name: str
    body: str
    created_at: dt.datetime


class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    body: str
    topic: str
    likes: int
    author_id: int
    created_at: dt.datetime
    comments: list[CommentOut] = []


# ---------- Chat ----------
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    role: str
    content: str
    created_at: dt.datetime
