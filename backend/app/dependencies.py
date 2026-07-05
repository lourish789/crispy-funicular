"""Shared FastAPI dependencies (current-user resolution)."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_error
    email = decode_token(token)
    if not email:
        raise credentials_error
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise credentials_error
    return user


def require_roles(*roles: str):
    """Dependency factory: allow only users whose role is in `roles`."""

    def _dep(current: User = Depends(get_current_user)) -> User:
        if roles and current.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action is only available to: {', '.join(roles)}. "
                f"Your role is '{current.role}'.",
            )
        return current

    return _dep
