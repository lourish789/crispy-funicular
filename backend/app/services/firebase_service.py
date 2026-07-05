"""Firebase Authentication integration (optional).

Verifies Firebase ID tokens server-side using the firebase-admin SDK. This lets
the frontend sign users in with Firebase (Google, email/password, etc.) and then
exchange the resulting ID token for an AgriTech session (our own JWT).

Everything is optional and lazily initialized:
  * if firebase-admin isn't installed, or no credentials are configured, the
    verifier reports itself disabled and the /api/auth/firebase endpoint returns
    a clear 503 instead of crashing.
"""
from __future__ import annotations

import json
import threading

from app.config import settings

try:
    import firebase_admin
    from firebase_admin import auth as fb_auth
    from firebase_admin import credentials as fb_credentials
except Exception:  # pragma: no cover - package optional
    firebase_admin = None  # type: ignore
    fb_auth = None  # type: ignore
    fb_credentials = None  # type: ignore

_app = None
_init_attempted = False
_lock = threading.Lock()


def _init() -> bool:
    """Initialize the firebase-admin app once. Returns True if usable."""
    global _app, _init_attempted
    if firebase_admin is None:
        return False
    if _app is not None:
        return True
    with _lock:
        if _app is not None:
            return True
        if _init_attempted:
            return _app is not None
        _init_attempted = True
        try:
            cred = _load_credentials()
            if cred is not None:
                _app = firebase_admin.initialize_app(cred)
            elif settings.firebase_project_id:
                # No service account, but a project id — rely on ADC / emulator.
                _app = firebase_admin.initialize_app(
                    options={"projectId": settings.firebase_project_id}
                )
            return _app is not None
        except Exception as exc:  # bad creds, etc.
            print(f"[AgriTech] Firebase init failed: {exc}")
            return False


def _load_credentials():
    if fb_credentials is None:
        return None
    if settings.firebase_credentials_json:
        try:
            data = json.loads(settings.firebase_credentials_json)
            return fb_credentials.Certificate(data)
        except Exception:
            return None
    if settings.firebase_credentials_file:
        try:
            return fb_credentials.Certificate(settings.firebase_credentials_file)
        except Exception:
            return None
    return None


def enabled() -> bool:
    return firebase_admin is not None and settings.firebase_enabled


def status() -> dict:
    return {
        "package_installed": firebase_admin is not None,
        "configured": settings.firebase_enabled,
        "ready": enabled(),
    }


def verify_id_token(id_token: str) -> dict | None:
    """Verify a Firebase ID token. Returns decoded claims or None on failure.

    Expected keys in the returned dict include: 'uid', 'email', 'name'.
    """
    if not _init() or fb_auth is None:
        return None
    try:
        decoded = fb_auth.verify_id_token(id_token)
        return {
            "uid": decoded.get("uid") or decoded.get("user_id"),
            "email": decoded.get("email"),
            "name": decoded.get("name") or (decoded.get("email") or "").split("@")[0],
            "email_verified": decoded.get("email_verified", False),
        }
    except Exception as exc:
        print(f"[AgriTech] Firebase token verification failed: {exc}")
        return None
