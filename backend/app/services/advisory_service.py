"""Personalized farm advisory & recommendation engine.

Blends deterministic analysis of the user's profile + historical activity
(diagnoses, listings) with an LLM-generated narrative. Always returns a
structured recommendation even when the LLM is offline.
"""
from __future__ import annotations

import datetime as dt
import json

from sqlalchemy.orm import Session

from app.models import Diagnosis, Listing, User
from app.services import llm_service


def _collect_metrics(db: Session, user: User) -> dict:
    diagnoses = (
        db.query(Diagnosis)
        .filter(Diagnosis.user_id == user.id)
        .order_by(Diagnosis.created_at.desc())
        .all()
    )
    listings = db.query(Listing).filter(Listing.seller_id == user.id).all()
    disease_hits = [d for d in diagnoses if "healthy" not in d.disease_name.lower()]
    crops = [c.strip() for c in (user.primary_crops or "").split(",") if c.strip()]
    return {
        "crops_count": len(crops),
        "crops": crops,
        "farm_size_hectares": user.farm_size_hectares or 0,
        "experience_years": user.farming_experience_years or 0,
        "total_diagnoses": len(diagnoses),
        "disease_incidents": len(disease_hits),
        "recent_diseases": [d.disease_name for d in disease_hits[:5]],
        "active_listings": len([x for x in listings if x.status == "active"]),
        "diversification_index": round(len(set(crops)) / max(len(crops), 1), 2)
        if crops
        else 0,
    }


def _rule_based(metrics: dict, user: User) -> dict:
    expand, optimize, improve, give_up = [], [], [], []

    if metrics["farm_size_hectares"] and metrics["farm_size_hectares"] < 2:
        expand.append(
            "Your farm is small — consider intercropping and vertical/high-density "
            "planting to raise output per hectare before acquiring more land."
        )
    if metrics["crops_count"] <= 1:
        expand.append(
            "You rely on a single crop. Add 1-2 complementary high-value crops "
            "(e.g. vegetables, legumes) to diversify income and spread risk."
        )
    else:
        optimize.append(
            "Maintain your crop diversity but focus inputs on your top-margin crops."
        )

    if metrics["active_listings"] == 0:
        expand.append(
            "You have no marketplace listings. List surplus produce or inputs to open "
            "a direct B2B/B2C sales channel."
        )
    else:
        optimize.append(
            "You are actively selling — bundle produce and join a cooperative to "
            "improve bargaining power and reduce logistics costs."
        )

    if metrics["disease_incidents"] >= 2:
        improve.append(
            "Recurring disease detections suggest weak preventive practices. Adopt a "
            "strict IPM schedule: weekly scouting, resistant varieties, sanitation."
        )
    if metrics["experience_years"] < 3:
        improve.append(
            "As a newer farmer, invest in record-keeping (inputs, yields, costs) so "
            "decisions become data-driven."
        )

    optimize.append(
        "Adopt drip irrigation and mulching to cut water use 30-50% and reduce "
        "fungal disease pressure."
    )
    give_up.append(
        "Phase out chronically low-yield or disease-prone plots/varieties and "
        "redirect that land and capital to your best-performing enterprise."
    )
    if metrics["crops_count"] > 5:
        give_up.append(
            "Growing too many unrelated crops fragments your attention — drop the "
            "bottom performers by margin per hectare."
        )

    summary = (
        f"Advisory for {user.full_name}: with "
        f"{metrics['farm_size_hectares'] or 'an unspecified'} ha and "
        f"{metrics['crops_count']} crop(s), the priority is to diversify income, "
        f"tighten disease prevention, and formalise your market channels."
    )
    return {
        "summary": summary,
        "expand": expand,
        "optimize": optimize,
        "improve": improve,
        "give_up": give_up,
    }


def generate_advisory(db: Session, user: User) -> dict:
    metrics = _collect_metrics(db, user)
    base = _rule_based(metrics, user)

    prompt = (
        "You are a senior agribusiness consultant. Using this farmer profile and "
        "activity metrics, produce concise, actionable advice. Respond ONLY as JSON "
        'with keys "summary" (string) and "expand", "optimize", "improve", "give_up" '
        "(each an array of 2-4 short imperative strings).\n\n"
        f"PROFILE: {user.profile_summary()}\n"
        f"METRICS: {json.dumps(metrics)}"
    )
    ai = llm_service.json_completion(
        [
            {"role": "system", "content": "You return only valid JSON."},
            {"role": "user", "content": prompt},
        ]
    )

    def _merge(key: str) -> list[str]:
        vals = ai.get(key) if isinstance(ai.get(key), list) else []
        combined = [str(v) for v in vals] + base[key]
        # de-dup while preserving order
        seen, out = set(), []
        for v in combined:
            if v not in seen:
                seen.add(v)
                out.append(v)
        return out[:5]

    return {
        "generated_at": dt.datetime.now(dt.timezone.utc),
        "summary": str(ai.get("summary") or base["summary"]),
        "expand": _merge("expand"),
        "optimize": _merge("optimize"),
        "improve": _merge("improve"),
        "give_up": _merge("give_up"),
        "metrics": metrics,
    }
