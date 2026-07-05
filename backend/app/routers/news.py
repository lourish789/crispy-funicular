"""Agri-news aggregator endpoint (cached)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import NewsArticle, NewsResponse
from app.services import news_service

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("", response_model=NewsResponse)
def get_news(
    location: str | None = None,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # default to the farmer's saved location when none is supplied
    loc = location or current.location or current.country
    articles, cached = news_service.get_news(loc)
    return NewsResponse(
        location=loc,
        cached=cached,
        articles=[NewsArticle(**a) for a in articles],
    )
