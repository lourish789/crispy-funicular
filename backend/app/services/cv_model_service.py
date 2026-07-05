"""Open-source local computer-vision disease classifiers.

Runs Hugging Face `image-classification` pipelines entirely on-device (no API
key required) to detect diseases in **plants** and **animals**:

  * plant  -> linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification
             (MobileNetV2, 38 PlantVillage classes)
  * animal -> SrimathiE21ALR044/Cattle_Skin_Disease  (ViT, cattle skin disease)

Both are configurable via env (PLANT_DISEASE_MODEL / ANIMAL_DISEASE_MODEL).
Everything is lazy-loaded and fully optional: if `torch`/`transformers` are not
installed or a model cannot be fetched, the service reports itself unavailable
and the caller falls back to the vision-LLM / heuristic pipeline.
"""
from __future__ import annotations

import threading

from PIL import Image

from app.config import settings

_pipelines: dict[str, object] = {}
_failed: set[str] = set()
_lock = threading.Lock()


def _normalize_subject(subject: str | None) -> str:
    return "animal" if (subject or "").lower().startswith("anim") else "plant"


def _model_id(subject: str) -> str:
    return (
        settings.animal_disease_model
        if subject == "animal"
        else settings.plant_disease_model
    )


def _get_pipeline(subject: str):
    """Lazily build (and cache) the image-classification pipeline for a subject."""
    if not settings.cv_local_enabled:
        return None
    if subject in _pipelines:
        return _pipelines[subject]
    if subject in _failed:
        return None
    with _lock:
        if subject in _pipelines:
            return _pipelines[subject]
        try:
            from transformers import pipeline  # heavy import, done lazily

            device = 0 if settings.cv_use_gpu else -1
            pl = pipeline(
                "image-classification", model=_model_id(subject), device=device
            )
            _pipelines[subject] = pl
            print(f"[AgriTech] Loaded open-source CV model for {subject}: {_model_id(subject)}")
            return pl
        except Exception as exc:  # torch/transformers missing or download failed
            _failed.add(subject)
            print(f"[AgriTech] CV model for {subject} unavailable ({exc}); using fallback.")
            return None


def available(subject: str = "plant") -> bool:
    return _get_pipeline(_normalize_subject(subject)) is not None


def deps_installed() -> bool:
    """Cheap check (no model download) for whether local CV can run at all."""
    if not settings.cv_local_enabled:
        return False
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401

        return True
    except Exception:
        return False


def status() -> dict:
    return {
        "enabled": settings.cv_local_enabled,
        "deps_installed": deps_installed(),
        "plant_model": settings.plant_disease_model,
        "animal_model": settings.animal_disease_model,
        "loaded": sorted(_pipelines.keys()),
    }


def prettify(label: str) -> str:
    """Turn a raw class label into a human-readable disease name.

    e.g. 'Tomato___Late_blight' -> 'Tomato — Late blight'.
    """
    label = str(label).strip()
    label = label.replace("___", " — ").replace("__", " — ").replace("_", " ")
    label = label.replace(" - ", " — ")
    return " ".join(w.capitalize() if w.islower() else w for w in label.split())


def is_healthy(label: str) -> bool:
    l = str(label).lower()
    return "healthy" in l or "normal" in l or l.endswith("healthy")


def classify(images: list[Image.Image], subject: str = "plant", top_k: int = 5) -> dict | None:
    """Classify one or more frames; aggregate the highest score per label.

    Returns None when the model is unavailable so callers can fall back.
    """
    subject = _normalize_subject(subject)
    pl = _get_pipeline(subject)
    if pl is None or not images:
        return None

    scores: dict[str, float] = {}
    for img in images[:4]:  # cap frames for latency
        try:
            preds = pl(img.convert("RGB"))
        except Exception:
            continue
        for p in preds:
            label = p.get("label", "")
            score = float(p.get("score", 0.0))
            scores[label] = max(scores.get(label, 0.0), score)

    if not scores:
        return None

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:top_k]
    top_label, top_score = ranked[0]
    return {
        "label": top_label,
        "pretty": prettify(top_label),
        "healthy": is_healthy(top_label),
        "confidence": round(float(top_score), 3),
        "subject": subject,
        "model": _model_id(subject),
        "top_k": [
            {"label": prettify(l), "raw": l, "score": round(float(s), 3)}
            for l, s in ranked
        ],
    }
