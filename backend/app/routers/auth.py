"""Authentication & profile management."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, normalize_role
from app.schemas import (
    FirebaseLoginRequest,
    LoginRequest,
    ProfileUpdate,
    Token,
    UserCreate,
    UserOut,
)
from app.security import create_access_token, hash_password, verify_password
from app.services import firebase_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=normalize_role(payload.role),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.email)
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.post("/firebase", response_model=Token)
def firebase_login(payload: FirebaseLoginRequest, db: Session = Depends(get_db)):
    """Exchange a verified Firebase ID token for an AgriTech session.

    Creates the local account on first sign-in (linking firebase_uid + role).
    """
    if not firebase_service.enabled():
        raise HTTPException(
            status_code=503,
            detail="Firebase sign-in is not configured on the server.",
        )
    claims = firebase_service.verify_id_token(payload.id_token)
    if not claims or not claims.get("email"):
        raise HTTPException(status_code=401, detail="Invalid Firebase token")

    email = claims["email"].lower()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            full_name=claims.get("name") or email.split("@")[0],
            hashed_password="",  # no local password for federated accounts
            role=normalize_role(payload.role),
            firebase_uid=claims.get("uid"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    elif not user.firebase_uid:
        user.firebase_uid = claims.get("uid")
        db.commit()
        db.refresh(user)

    token = create_access_token(user.email)
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    token = create_access_token(user.email)
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)):
    return current


@router.put("/me", response_model=UserOut)
def update_profile(
    payload: ProfileUpdate,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "role":
            value = normalize_role(value)
        setattr(current, field, value)
    db.commit()
    db.refresh(current)
    return current
