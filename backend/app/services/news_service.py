"""Real-time agri-news aggregator with TTL caching and graceful fallback."""
from __future__ import annotations

import httpx
from cachetools import TTLCache

from app.config import settings

# key -> list[dict]; shared process cache
_cache: TTLCache = TTLCache(maxsize=128, ttl=settings.news_cache_ttl_seconds)

GLOBAL_QUERY = "agriculture OR farming OR crops OR agribusiness"


def _fetch_newsapi(query: str, page_size: int = 10) -> list[dict]:
    if not settings.news_api_key:
        return []
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": page_size,
        "apiKey": settings.news_api_key,
    }
    try:
        resp = httpx.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("articles", [])
    except Exception:
        return []


def _map_article(raw: dict, scope: str) -> dict:
    source = raw.get("source") or {}
    return {
        "title": raw.get("title") or "Untitled",
        "description": raw.get("description"),
        "url": raw.get("url"),
        "source": source.get("name") if isinstance(source, dict) else str(source),
        "published_at": raw.get("publishedAt"),
        "image_url": raw.get("urlToImage"),
        "scope": scope,
    }


def get_news(location: str | None = None) -> tuple[list[dict], bool]:
    """Return (articles, cached). Combines global + location-scoped agri news."""
    cache_key = f"news::{(location or 'global').lower()}"
    if cache_key in _cache:
        return _cache[cache_key], True

    articles: list[dict] = []
    for raw in _fetch_newsapi(GLOBAL_QUERY, page_size=8):
        articles.append(_map_article(raw, "global"))

    if location:
        local_q = f"({location}) AND (agriculture OR farming OR weather OR harvest)"
        for raw in _fetch_newsapi(local_q, page_size=8):
            articles.append(_map_article(raw, "local"))

    if not articles:
        articles = _fallback_articles(location)

    _cache[cache_key] = articles
    return articles, False


def _fallback_articles(location: str | None) -> list[dict]:
    loc = location or "your region"
    return [
        {
            "title": "Set NEWS_API_KEY to see live agricultural headlines",
            "description": "The news aggregator is running in demo mode. Add a "
            "NewsAPI.org key to fetch real-time global and localized agri-news.",
            "url": "https://newsapi.org",
            "source": "AgriTech Suite",
            "published_at": None,
            "image_url": None,
            "scope": "global",
        },
        {
            "title": f"Seasonal advisory for {loc}",
            "description": "Monitor local weather forecasts, plan planting around the "
            "rains, and check soil moisture before irrigating.",
            "url": None,
            "source": "AgriTech Suite",
            "published_at": None,
            "image_url": None,
            "scope": "local",
        },
    ]
