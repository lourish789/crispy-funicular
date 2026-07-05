"""Retrieval-Augmented Generation: knowledge base seeding + semantic retrieval."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import KnowledgeChunk
from app.services.embedding_service import cosine_similarity, embed_query, embed_text

SEED_KNOWLEDGE = [
    "Crop rotation with legumes (beans, cowpea, groundnut) fixes atmospheric nitrogen "
    "and reduces fertilizer costs while breaking pest and disease cycles.",
    "Maize needs 120-150 kg N per hectare split into basal and top-dress applications; "
    "yellowing lower leaves usually indicate nitrogen deficiency.",
    "Tomato late blight (Phytophthora infestans) spreads in cool, wet weather; use "
    "copper-based fungicides and resistant varieties, and avoid overhead irrigation.",
    "Integrated Pest Management (IPM) combines scouting, biological controls, resistant "
    "varieties, and targeted pesticide use only when thresholds are exceeded.",
    "Drip irrigation improves water-use efficiency by 30-50% versus flood irrigation and "
    "reduces fungal disease by keeping foliage dry.",
    "Soil pH between 6.0 and 7.0 is ideal for most crops; apply lime to raise pH and "
    "elemental sulphur or organic matter to lower it.",
    "Post-harvest losses in Sub-Saharan Africa reach 30-40%; hermetic storage bags and "
    "solar drying dramatically cut spoilage and boost market value.",
    "Cassava mosaic disease is transmitted by whiteflies; plant certified disease-free "
    "cuttings and use tolerant varieties like TME 419.",
    "Poultry require 21% protein starter feed for the first weeks; sudden mortality with "
    "greenish diarrhea can indicate Newcastle disease — vaccinate on schedule.",
    "Diversifying into high-value crops (peppers, herbs, horticulture) and value-added "
    "processing raises margins compared with staple grains alone.",
    "Mulching conserves soil moisture, suppresses weeds, and moderates soil temperature, "
    "reducing irrigation needs during dry spells.",
    "Access to aggregated markets and cooperatives improves bargaining power and lets "
    "smallholders sell in bulk at better prices.",
]


def seed_knowledge_base(db: Session) -> int:
    """Populate the vector store once. Returns number of chunks created."""
    existing = db.query(KnowledgeChunk).count()
    if existing:
        return 0
    created = 0
    for text in SEED_KNOWLEDGE:
        chunk = KnowledgeChunk(source="agri-kb", content=text, embedding=embed_text(text))
        db.add(chunk)
        created += 1
    db.commit()
    return created


def add_document(db: Session, content: str, source: str = "user") -> KnowledgeChunk:
    chunk = KnowledgeChunk(source=source, content=content, embedding=embed_text(content))
    db.add(chunk)
    db.commit()
    db.refresh(chunk)
    return chunk


def retrieve(db: Session, query: str, top_k: int = 4) -> list[str]:
    """Return the most semantically relevant knowledge snippets for `query`."""
    q_emb = embed_query(query)
    chunks = db.query(KnowledgeChunk).all()
    scored = [
        (cosine_similarity(q_emb, c.embedding or []), c.content) for c in chunks
    ]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [content for score, content in scored[:top_k] if score > 0.01]
