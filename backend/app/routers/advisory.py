"""Personalized farm advisory endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import AdvisoryOut
from app.services import advisory_service

router = APIRouter(prefix="/api/advisory", tags=["advisory"])


@router.get("", response_model=AdvisoryOut)
def get_advisory(
    current: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return advisory_service.generate_advisory(db, current)
