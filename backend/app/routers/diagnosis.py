"""Plant-disease diagnosis endpoints (image & video upload)."""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Diagnosis, User
from app.schemas import DiagnosisOut, DiagnosisResult
from app.services import vision_service

router = APIRouter(prefix="/api/diagnosis", tags=["diagnosis"])

MAX_BYTES = 25 * 1024 * 1024  # 25 MB


@router.post("", response_model=DiagnosisResult)
async def create_diagnosis(
    file: UploadFile = File(...),
    crop_hint: str | None = Form(None),
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 25MB)")

    content_type = (file.content_type or "").lower()
    media_type = "video" if content_type.startswith("video") else "image"

    result = vision_service.diagnose(data, media_type, crop_hint)

    record = Diagnosis(
        user_id=current.id,
        media_type=media_type,
        crop_hint=crop_hint,
        disease_name=result["disease_name"],
        confidence=result["confidence"],
        cause=result["cause"],
        immediate_solution=result["immediate_solution"],
        prevention_strategies=json.dumps(result["prevention_strategies"]),
        raw=result.get("evidence", {}),
    )
    db.add(record)
    db.commit()
    return DiagnosisResult(**result)


@router.get("/history", response_model=list[DiagnosisOut])
def history(
    current: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    records = (
        db.query(Diagnosis)
        .filter(Diagnosis.user_id == current.id)
        .order_by(Diagnosis.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        DiagnosisOut(
            id=r.id,
            media_type=r.media_type,
            crop_hint=r.crop_hint,
            disease_name=r.disease_name,
            cause=r.cause,
            immediate_solution=r.immediate_solution,
            prevention_strategies=r.prevention_list(),
            confidence=r.confidence,
            created_at=r.created_at,
        )
        for r in records
    ]
