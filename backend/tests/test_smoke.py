"""End-to-end smoke tests exercising every endpoint via FastAPI TestClient.

Runs fully offline (no API keys) — services degrade gracefully, so these tests
validate the full request/response contract of the platform.
"""
import io
import os
import tempfile

os.environ.setdefault("DATABASE_URL", f"sqlite:///{tempfile.gettempdir()}/agritech_test.db")

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

# fresh DB per run
_db = os.environ["DATABASE_URL"].replace("sqlite:///", "")
if os.path.exists(_db):
    os.remove(_db)

from app.database import SessionLocal, init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.services import rag_service  # noqa: E402

# Ensure schema + RAG seed exist (lifespan does this in production).
init_db()
_seed_db = SessionLocal()
try:
    rag_service.seed_knowledge_base(_seed_db)
finally:
    _seed_db.close()

client = TestClient(app)


def _auth_headers(email="farmer@example.com"):
    r = client.post(
        "/api/auth/register",
        json={"email": email, "full_name": "Test Farmer", "password": "secret123"},
    )
    if r.status_code == 400:  # already registered
        r = client.post("/api/auth/login", json={"email": email, "password": "secret123"})
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, token


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_auth_and_profile():
    headers, _ = _auth_headers()
    r = client.put(
        "/api/auth/me",
        headers=headers,
        json={
            "location": "Ibadan, Nigeria",
            "country": "Nigeria",
            "farm_size_hectares": 1.5,
            "primary_crops": "maize,tomato",
            "farming_experience_years": 2,
        },
    )
    assert r.status_code == 200
    assert r.json()["location"] == "Ibadan, Nigeria"


def test_diagnosis_image():
    headers, _ = _auth_headers()
    # synthetic leaf image with brown lesions
    arr = np.zeros((120, 120, 3), dtype=np.uint8)
    arr[..., 1] = 160  # green
    arr[30:60, 30:60] = [120, 80, 40]  # brown patch
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    r = client.post(
        "/api/diagnosis",
        headers=headers,
        files={"file": ("leaf.jpg", buf, "image/jpeg")},
        data={"crop_hint": "tomato"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "disease_name" in body
    assert isinstance(body["prevention_strategies"], list)
    # history
    h = client.get("/api/diagnosis/history", headers=headers)
    assert h.status_code == 200 and len(h.json()) >= 1


def test_advisory():
    headers, _ = _auth_headers()
    r = client.get("/api/advisory", headers=headers)
    assert r.status_code == 200
    body = r.json()
    for key in ("expand", "optimize", "improve", "give_up", "metrics", "summary"):
        assert key in body


def test_news():
    headers, _ = _auth_headers()
    r = client.get("/api/news", headers=headers)
    assert r.status_code == 200
    assert isinstance(r.json()["articles"], list)
    assert len(r.json()["articles"]) >= 1


def test_marketplace():
    headers, _ = _auth_headers()
    r = client.post(
        "/api/marketplace/listings",
        headers=headers,
        json={
            "title": "Fresh Tomatoes",
            "description": "50kg crates of ripe tomatoes",
            "category": "produce",
            "price": 20,
            "unit": "crate",
            "quantity": 50,
        },
    )
    assert r.status_code == 201, r.text
    lid = r.json()["id"]
    assert client.get("/api/marketplace/listings").status_code == 200
    assert client.get(f"/api/marketplace/listings/{lid}").status_code == 200
    assert client.get("/api/marketplace/my-listings", headers=headers).status_code == 200


def test_community():
    headers, _ = _auth_headers()
    r = client.post(
        "/api/community/posts",
        headers=headers,
        json={"title": "Best maize variety?", "body": "What do you recommend?", "topic": "crops"},
    )
    assert r.status_code == 201, r.text
    pid = r.json()["id"]
    c = client.post(
        f"/api/community/posts/{pid}/comments",
        headers=headers,
        json={"body": "Try TME 419"},
    )
    assert c.status_code == 201
    assert len(c.json()["comments"]) == 1
    like = client.post(f"/api/community/posts/{pid}/like", headers=headers)
    assert like.json()["likes"] == 1
    assert client.get("/api/community/posts").status_code == 200


def test_chat_stream():
    headers, token = _auth_headers()
    # POST streaming
    with client.stream(
        "POST",
        "/api/chat/stream",
        headers=headers,
        json={"message": "How do I improve my maize yield?", "session_id": "s1"},
    ) as resp:
        assert resp.status_code == 200
        text = "".join(chunk for chunk in resp.iter_text())
    assert "event: start" in text
    assert "event: done" in text
    # GET SSE with token query param
    r = client.get(
        "/api/chat/stream",
        params={"message": "Tell me about crop rotation", "token": token, "session_id": "s1"},
    )
    assert r.status_code == 200
    # history persisted
    h = client.get("/api/chat/history", headers=headers, params={"session_id": "s1"})
    assert h.status_code == 200 and len(h.json()) >= 2
