"""Computer-vision plant-disease diagnosis.

Pipeline:
  1. Accept an uploaded image or video (bytes).
  2. For video, sample representative frames with OpenCV.
  3. Run lightweight leaf/color analysis to build visual evidence.
  4. Ask the Groq vision model to diagnose; if unavailable, fall back to a
     heuristic diagnosis derived from the color analysis so callers always get
     a well-formed structured result.
"""
from __future__ import annotations

import base64
import io
import json
import tempfile
from dataclasses import dataclass

import numpy as np
from PIL import Image

from app.services import cv_model_service, llm_service

DIAGNOSIS_PROMPT = (
    "You are an expert plant pathologist. Analyse the plant image(s) and diagnose "
    "the most likely disease or disorder. Respond ONLY with a JSON object with keys: "
    '"disease_name" (string), "cause" (string), "immediate_solution" (string), '
    '"prevention_strategies" (array of short strings), "confidence" (0-1 float). '
    "If the plant looks healthy, say so in disease_name."
)


@dataclass
class VisualEvidence:
    green_ratio: float
    brown_ratio: float
    yellow_ratio: float
    dark_spot_ratio: float
    brightness: float
    frames_analyzed: int


def _image_to_data_url(img: Image.Image) -> str:
    img = img.convert("RGB")
    img.thumbnail((768, 768))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/jpeg;base64,{b64}"


def _analyze_colors(images: list[Image.Image]) -> VisualEvidence:
    greens = browns = yellows = darks = brights = 0.0
    for img in images:
        arr = np.asarray(img.convert("RGB").resize((160, 160)), dtype=np.float32)
        r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
        total = arr.shape[0] * arr.shape[1]
        green = np.sum((g > r + 15) & (g > b + 10)) / total
        brown = np.sum((r > 80) & (r < 180) & (g > 40) & (g < 130) & (b < 90)) / total
        yellow = np.sum((r > 150) & (g > 150) & (b < 110)) / total
        dark = np.sum((r < 60) & (g < 60) & (b < 60)) / total
        bright = float(arr.mean()) / 255.0
        greens += green
        browns += brown
        yellows += yellow
        darks += dark
        brights += bright
    n = max(len(images), 1)
    return VisualEvidence(
        green_ratio=round(greens / n, 3),
        brown_ratio=round(browns / n, 3),
        yellow_ratio=round(yellows / n, 3),
        dark_spot_ratio=round(darks / n, 3),
        brightness=round(brights / n, 3),
        frames_analyzed=len(images),
    )


def extract_frames_from_video(data: bytes, max_frames: int = 4) -> list[Image.Image]:
    """Sample up to `max_frames` evenly spaced frames from a video byte stream."""
    try:
        import cv2  # imported lazily so image-only deployments stay light
    except Exception:
        return []
    frames: list[Image.Image] = []
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    cap = cv2.VideoCapture(tmp_path)
    try:
        count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        if count <= 0:
            # stream without a known length: read sequentially
            ok, frame = cap.read()
            while ok and len(frames) < max_frames:
                frames.append(_cv_to_pil(frame))
                for _ in range(15):
                    ok, frame = cap.read()
            return frames
        indices = np.linspace(0, count - 1, num=min(max_frames, count), dtype=int)
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
            ok, frame = cap.read()
            if ok:
                frames.append(_cv_to_pil(frame))
    finally:
        cap.release()
    return frames


def _cv_to_pil(frame) -> Image.Image:
    import cv2

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


def diagnose(
    data: bytes,
    media_type: str,
    crop_hint: str | None = None,
    subject: str = "plant",
) -> dict:
    """Main entry point. Returns a dict matching schemas.DiagnosisResult.

    Detection order:
      1. Open-source local CV model (plant or animal) — primary, no key needed.
      2. Groq vision model — secondary.
      3. Text reasoning over color metrics — tertiary.
      4. Rule-based heuristic — always available.
    """
    if media_type == "video":
        images = extract_frames_from_video(data)
        if not images:  # decoding failed — degrade gracefully
            return _healthy_or_unknown(None)
    else:
        try:
            images = [Image.open(io.BytesIO(data))]
        except Exception:
            return _healthy_or_unknown(None)

    evidence = _analyze_colors(images)

    # ---- 1. Open-source local computer-vision classifier ----
    cv = cv_model_service.classify(images, subject)
    if cv:
        return _build_from_cv(cv, subject, crop_hint, evidence)

    # ---- 2/3. Groq vision, then text reasoning ----
    data_urls = [_image_to_data_url(img) for img in images]

    prompt = DIAGNOSIS_PROMPT
    if crop_hint:
        prompt += f" The farmer says the crop is: {crop_hint}."
    prompt += (
        f" Visual analysis of the sample: green={evidence.green_ratio}, "
        f"brown/necrotic={evidence.brown_ratio}, yellowing={evidence.yellow_ratio}, "
        f"dark_lesions={evidence.dark_spot_ratio}, brightness={evidence.brightness}, "
        f"frames_analyzed={evidence.frames_analyzed}."
    )

    result = llm_service.vision_completion(data_urls, prompt)
    if not result:
        # Vision model unavailable: try a text reasoning pass over the evidence
        result = llm_service.json_completion(
            [
                {"role": "system", "content": DIAGNOSIS_PROMPT},
                {
                    "role": "user",
                    "content": prompt + " No image is available; reason from the metrics.",
                },
            ]
        )
    if not result:
        return _heuristic_diagnosis(evidence)

    return _normalize(result, evidence)


def _normalize(
    result: dict, evidence: VisualEvidence, detector: str = "groq-vision"
) -> dict:
    prevention = result.get("prevention_strategies") or []
    if isinstance(prevention, str):
        prevention = [prevention]
    conf = result.get("confidence", 0.6)
    try:
        conf = float(conf)
    except (TypeError, ValueError):
        conf = 0.6
    return {
        "disease_name": str(result.get("disease_name") or "Undetermined condition"),
        "cause": str(result.get("cause") or "Cause could not be determined from the sample."),
        "immediate_solution": str(
            result.get("immediate_solution")
            or "Isolate affected plants and consult a local extension officer."
        ),
        "prevention_strategies": [str(p) for p in prevention][:6]
        or ["Practice crop rotation", "Use certified seed", "Scout weekly"],
        "confidence": max(0.0, min(1.0, conf)),
        "detector": detector,
        "evidence": evidence.__dict__,
    }


# ---------- Open-source CV model result -> structured advice ----------
def _build_from_cv(
    cv: dict, subject: str, crop_hint: str | None, evidence: VisualEvidence
) -> dict:
    """Turn a CV classification into a full structured diagnosis.

    The label + confidence come from the open-source model; the agronomic /
    veterinary advice is enriched by the LLM, with a keyword-based local
    fallback so the endpoint stays useful fully offline.
    """
    ev = dict(evidence.__dict__)
    ev["cv_model"] = cv.get("model")
    ev["cv_top_k"] = cv.get("top_k")
    ev["detector"] = "open-source-cv"

    if cv["healthy"]:
        return {
            "disease_name": f"Healthy / No disease detected ({cv['pretty']})",
            "cause": "The model classified the sample as healthy tissue.",
            "immediate_solution": "No treatment needed — continue good husbandry "
            "and monitor regularly.",
            "prevention_strategies": [
                "Routine scouting / health checks",
                "Balanced nutrition",
                "Good sanitation and biosecurity",
            ],
            "confidence": cv["confidence"],
            "detector": "open-source-cv",
            "model": cv.get("model"),
            "evidence": ev,
        }

    advice = _advice_for_label(cv["pretty"], subject, crop_hint)
    return {
        "disease_name": cv["pretty"],
        "cause": advice["cause"],
        "immediate_solution": advice["immediate_solution"],
        "prevention_strategies": advice["prevention_strategies"],
        "confidence": cv["confidence"],
        "detector": "open-source-cv",
        "model": cv.get("model"),
        "evidence": ev,
    }


# Keyword -> advice map for offline enrichment of detected labels.
_ADVICE_KB: list[tuple[tuple[str, ...], dict]] = [
    (
        ("blight", "phytophthora"),
        {
            "cause": "A fungal/oomycete pathogen (blight) spreading in humid, wet conditions.",
            "immediate_solution": "Remove and destroy affected foliage, apply a copper-"
            "based or systemic fungicide, and stop overhead watering.",
            "prevention_strategies": ["Use resistant varieties", "Rotate crops",
                "Improve spacing/air-flow", "Avoid wetting leaves"],
        },
    ),
    (
        ("rust",),
        {
            "cause": "A rust fungus producing orange/brown pustules on leaves.",
            "immediate_solution": "Remove infected leaves and apply an appropriate fungicide "
            "(e.g. triazole) early.",
            "prevention_strategies": ["Plant resistant cultivars", "Avoid overhead irrigation",
                "Remove crop debris", "Ensure good airflow"],
        },
    ),
    (
        ("mildew",),
        {
            "cause": "Powdery/downy mildew fungus favored by humidity and poor airflow.",
            "immediate_solution": "Apply sulphur or potassium-bicarbonate spray and prune for "
            "airflow.",
            "prevention_strategies": ["Space plants well", "Water at the base",
                "Use resistant varieties", "Remove infected tissue"],
        },
    ),
    (
        ("spot", "septoria", "bacterial"),
        {
            "cause": "Leaf-spot complex (fungal or bacterial) causing necrotic lesions.",
            "immediate_solution": "Prune affected leaves, avoid overhead watering, and apply a "
            "copper-based bactericide/fungicide.",
            "prevention_strategies": ["Crop rotation", "Certified clean seed",
                "Field sanitation", "Drip irrigation"],
        },
    ),
    (
        ("mosaic", "virus", "curl", "yellow leaf curl"),
        {
            "cause": "A viral infection, usually spread by insect vectors (whitefly/aphids).",
            "immediate_solution": "Rogue out infected plants and control the insect vector; "
            "there is no chemical cure for the virus itself.",
            "prevention_strategies": ["Use virus-free certified planting material",
                "Control whitefly/aphids", "Use reflective mulch", "Resistant varieties"],
        },
    ),
    (
        ("lumpy", "pox", "dermat", "skin", "mange", "ringworm", "foot"),
        {
            "cause": "A contagious skin/viral condition in livestock spread by contact or "
            "biting insects.",
            "immediate_solution": "Isolate the affected animal immediately, treat lesions and "
            "prevent secondary infection, and consult a veterinarian for vaccination/treatment.",
            "prevention_strategies": ["Vaccinate the herd", "Vector (fly/tick) control",
                "Quarantine new animals", "Strict biosecurity and hygiene"],
        },
    ),
    (
        ("rot", "anthracnose", "mold", "scab"),
        {
            "cause": "A fungal rot/anthracnose thriving on wet, damaged, or overripe tissue.",
            "immediate_solution": "Remove and destroy affected material, improve drainage, and "
            "apply a suitable fungicide.",
            "prevention_strategies": ["Avoid waterlogging", "Handle produce gently",
                "Sanitation", "Timely harvest"],
        },
    ),
]


def _advice_for_label(label: str, subject: str, crop_hint: str | None) -> dict:
    """LLM-enriched advice for a detected disease label, with offline fallback."""
    kind = "animal/livestock" if subject == "animal" else "plant/crop"
    prompt = (
        f"An open-source computer-vision model detected the condition '{label}' on a "
        f"{kind}{f' (specifically {crop_hint})' if crop_hint else ''}. "
        "As an expert plant pathologist / veterinarian, respond ONLY as JSON with keys "
        '"cause" (string), "immediate_solution" (string), and "prevention_strategies" '
        "(array of 3-5 short strings)."
    )
    ai = llm_service.json_completion(
        [
            {"role": "system", "content": "You return only valid JSON."},
            {"role": "user", "content": prompt},
        ]
    )
    if ai and ai.get("cause") and ai.get("immediate_solution"):
        prev = ai.get("prevention_strategies") or []
        if isinstance(prev, str):
            prev = [prev]
        return {
            "cause": str(ai["cause"]),
            "immediate_solution": str(ai["immediate_solution"]),
            "prevention_strategies": [str(p) for p in prev][:6]
            or ["Scout regularly", "Practice sanitation", "Use resistant stock"],
        }

    # Offline keyword-based enrichment
    low = label.lower()
    for keys, advice in _ADVICE_KB:
        if any(k in low for k in keys):
            return advice
    return {
        "cause": f"The model identified '{label}'. Exact cause needs field confirmation.",
        "immediate_solution": "Isolate affected specimens and consult a local extension "
        "officer or veterinarian with this result.",
        "prevention_strategies": [
            "Routine scouting / health checks",
            "Good sanitation & biosecurity",
            "Balanced nutrition",
            "Use certified/healthy stock",
        ],
    }


def _heuristic_diagnosis(evidence: VisualEvidence) -> dict:
    """Rule-based fallback so the endpoint is always useful without any AI key."""
    if evidence.green_ratio > 0.45 and evidence.brown_ratio < 0.08:
        return _healthy_or_unknown(evidence)
    if evidence.yellow_ratio > 0.20:
        return _normalize(
            detector="heuristic",
            evidence=evidence,
            result={
                "disease_name": "Nutrient deficiency (likely nitrogen) / early chlorosis",
                "cause": "Widespread yellowing of foliage typically signals nitrogen "
                "deficiency, waterlogging, or root stress.",
                "immediate_solution": "Apply a balanced nitrogen-rich fertilizer, improve "
                "drainage, and check for root rot.",
                "prevention_strategies": [
                    "Soil-test before each season",
                    "Split-apply nitrogen",
                    "Add organic matter/compost",
                    "Avoid waterlogging",
                ],
                "confidence": 0.5,
            },
        )
    if evidence.brown_ratio > 0.15 or evidence.dark_spot_ratio > 0.06:
        return _normalize(
            detector="heuristic",
            evidence=evidence,
            result={
                "disease_name": "Fungal leaf blight / leaf-spot complex",
                "cause": "Necrotic brown lesions and dark spots are consistent with "
                "fungal pathogens (e.g. blight, anthracnose) favored by humid conditions.",
                "immediate_solution": "Remove and destroy affected leaves, apply an "
                "appropriate fungicide, and avoid overhead irrigation.",
                "prevention_strategies": [
                    "Use resistant varieties",
                    "Rotate crops",
                    "Improve air circulation/spacing",
                    "Keep foliage dry",
                ],
                "confidence": 0.5,
            },
        )
    return _healthy_or_unknown(evidence)


def _healthy_or_unknown(evidence: VisualEvidence | None) -> dict:
    ev = evidence.__dict__ if evidence else {}
    healthy = bool(evidence and evidence.green_ratio > 0.4)
    return {
        "disease_name": "Healthy / No disease detected" if healthy else "Inconclusive",
        "cause": "The sample shows predominantly healthy tissue."
        if healthy
        else "The image could not be analysed with confidence.",
        "immediate_solution": "Continue good agronomic practice and monitor weekly."
        if healthy
        else "Re-upload a clear, well-lit close-up of the affected area.",
        "prevention_strategies": [
            "Regular scouting",
            "Balanced fertilization",
            "Crop rotation",
        ],
        "confidence": 0.55 if healthy else 0.2,
        "detector": "heuristic",
        "evidence": ev,
    }
