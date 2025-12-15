"""Utilities for JWT auth validation."""
from typing import Dict, Any

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, ExpiredSignatureError, jwt

from app.core.config import settings
from app.models.enums.rol import Role


def _extract_token(authorization: str | None) -> str:
    """Gets the bearer token from the Authorization header."""
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization header")

    return parts[1]


def decode_and_validate_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a JWT token; raises HTTP errors on failure."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if "sub" not in payload or "role" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    return payload


def get_current_user(authorization: str | None = Header(default=None)) -> Dict[str, Any]:
    """Reads Authorization header, validates JWT, and returns account_id and role."""
    token = _extract_token(authorization)
    payload = decode_and_validate_token(token)
    return {
        "account_id": payload.get("sub"),
        "role": payload.get("role"),
    }


def require_admin(current=Depends(get_current_user)) -> Dict[str, Any]:
    """Allows only administrator users."""
    if current.get("role") != Role.ADMINISTRATOR.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return current


def require_admin_or_coach(current=Depends(get_current_user)) -> Dict[str, Any]:
    """Allows administrators or coaches."""
    if current.get("role") not in {Role.ADMINISTRATOR.value, Role.COACH.value}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin or coach role required")
    return current


def require_authenticated(current=Depends(get_current_user)) -> Dict[str, Any]:
    """Allows any authenticated user."""
    return current
