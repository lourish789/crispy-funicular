# 🌱 AgriTech Suite

A comprehensive, one-stop agricultural platform that puts AI in every farmer's
pocket. Diagnose plant disease from a photo or video, get a personalized farm
growth strategy, read hyper-local agri-news, trade in a B2B/B2C marketplace,
connect with a community of farmers, and consult a **context-aware, streaming AI
expert** that knows your farm.

![status](https://img.shields.io/badge/build-passing-brightgreen) ![python](https://img.shields.io/badge/python-3.10%2B-blue) ![react](https://img.shields.io/badge/react-18-61dafb)

---

## ✨ Features

| # | Feature | What it does |
|---|---------|--------------|
| 1 | **🔬 AI Plant & Animal Disease Diagnosis** | Upload an **image or video** of a **plant or animal**; frames are sampled with OpenCV and an **open-source local computer-vision model** classifies the disease on-device (no API key). The detected label is then enriched by the LLM into structured JSON: `disease_name`, `cause`, `immediate_solution`, `prevention_strategies`, confidence, and the detector/model used. |
| 2 | **🧭 Personalized Farm Advisory** | A data-driven engine blends your profile + historical activity (diagnoses, listings) with an LLM to tell you how to **expand**, **optimize**, **improve**, and what to **give up** on. |
| 3 | **📰 Real-Time Agri-News** | Fetches global + hyper-localized agricultural news for your location, with efficient **TTL caching**. |
| 4 | **🛒 Agribusiness Marketplace** | B2B/B2C listings for produce, tools, fertilizers, seeds, livestock & machinery — search, filter, buy/sell. |
| 5 | **💬 Community Hub** | Topic-based forum: posts, comments, likes, knowledge sharing. |
| 6 | **🤖 Context-Aware Streaming Chatbot** | Groq `llama-3.1-8b-instant` with **end-to-end token streaming (SSE)**, RAG over a knowledge base embedded with **Google Gemini embeddings**, and full injection of the user's profile + conversation history. |

### AI architecture

- **Disease detection (primary):** open-source **Hugging Face `image-classification`** models running locally — no API key:
  - Plant/crop → `linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification` (MobileNetV2, 38 PlantVillage classes)
  - Animal/livestock → `SrimathiE21ALR044/Cattle_Skin_Disease` (ViT)
  - both configurable via `PLANT_DISEASE_MODEL` / `ANIMAL_DISEASE_MODEL`.
- **Diagnosis enrichment:** the detected label is expanded into cause / solution / prevention by the LLM, with an offline keyword knowledge base fallback.
- **LLM / text generation:** Groq `llama-3.1-8b-instant` (low latency).
- **Vision fallback:** Groq multimodal model, then a color-analysis heuristic.
- **Embeddings / RAG:** Google Gemini Embedding API **exclusively** for vectorization and semantic search.
- **Graceful degradation:** every stage has a deterministic offline fallback, so the platform never crashes when a key is missing, a model isn't downloaded, or an API fails.

**Detection order:** open-source local CV model → Groq vision → text reasoning over color metrics → rule-based heuristic.

To enable the local CV models:

```bash
cd backend
pip install -r requirements-cv.txt   # torch + transformers (~200MB+); model downloads on first use
```

Without them, diagnosis still works via the vision-LLM / heuristic fallback.

---

## 🗂️ Project structure

```
crispy-funicular/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── main.py             # app factory, CORS, lifespan (DB init + RAG seed)
│   │   ├── config.py           # env-driven settings
│   │   ├── database.py         # SQLAlchemy engine/session
│   │   ├── models.py           # ORM schema (users, diagnoses, listings, posts, chat, vectors)
│   │   ├── schemas.py          # Pydantic contracts
│   │   ├── security.py         # JWT + bcrypt
│   │   ├── dependencies.py     # auth dependency
│   │   ├── routers/            # auth, diagnosis, advisory, news, marketplace, community, chat
│   │   └── services/           # llm, embeddings, rag, vision, advisory, news, chat
│   ├── tests/test_smoke.py     # end-to-end tests for every endpoint
│   ├── requirements.txt
│   └── .env.example
└── frontend/                   # React + Vite SPA
    ├── src/
    │   ├── pages/              # Login, Dashboard, Diagnosis, Advisory, News, Marketplace, Community, Chat, Profile
    │   ├── components/Navbar.jsx
    │   ├── api.js  auth.jsx  App.jsx  styles.css
    └── package.json
```

---

## 🚀 Quick start

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate    |    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then add your API keys (optional — runs in fallback mode without them)
uvicorn app.main:app --reload
```

API runs at **http://localhost:8000** — interactive docs at **/docs**.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

App runs at **http://localhost:5173** (the Vite dev server proxies `/api` to the backend).

### 3. Configure keys (optional but recommended)

Edit `backend/.env`:

```env
GROQ_API_KEY=...        # https://console.groq.com   (chat + vision)
GEMINI_API_KEY=...      # https://aistudio.google.com (embeddings / RAG)
NEWS_API_KEY=...        # https://newsapi.org         (live news)
SECRET_KEY=<long-random-string>
```

Without keys, the app runs fully in **graceful-fallback mode** (heuristic diagnosis, local embeddings, demo news) so you can explore every feature immediately.

---

## 🔌 API reference (selected)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/register` · `/api/auth/login` | Auth, returns JWT |
| `PUT`  | `/api/auth/me` | Update farm profile |
| `POST` | `/api/diagnosis` | Multipart image/video → structured diagnosis |
| `GET`  | `/api/advisory` | Personalized recommendations |
| `GET`  | `/api/news?location=` | Cached global + local agri-news |
| `GET/POST` | `/api/marketplace/listings` | Browse / create listings |
| `GET/POST` | `/api/community/posts` | Forum posts, comments, likes |
| `POST` | `/api/chat/stream` | **SSE** streaming chat (fetch + Bearer) |
| `GET`  | `/api/chat/stream?token=&message=` | **SSE** for browser `EventSource` |
| `GET`  | `/api/health` | Service status |

---

## 🧪 Testing

```bash
cd backend
pytest -q      # 8 end-to-end tests covering every feature, all offline
```

---

## 🛡️ Resilience

- Every external AI/news call is wrapped with try/except and a deterministic fallback.
- File uploads are size-capped (25 MB) and content-type aware (image vs. video).
- JWT auth on all user-scoped routes; SSE `GET` accepts a token query param because `EventSource` cannot send headers.

---

Built with FastAPI · SQLAlchemy · React · Vite · Groq · Google Gemini.
