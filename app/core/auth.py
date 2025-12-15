"""Utilities for JWT auth issuance and validation."""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, ExpiredSignatureError, jwt

from app.core.config import settings
from app.models.enums.rol import Role


def _extract_token(authorization: str | None) -> str:
    """Extrae el token de la cabecera de autorización."""
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization header")

    return parts[1]


def _create_token(*, subject: str, role: str, expires_delta: timedelta, token_type: str) -> str:
    """Crea un JWT parametrizable con tipo y expiración."""
    expire = datetime.utcnow() + expires_delta
    payload = {
        "sub": subject,
        "role": role,
        "type": token_type,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_access_token(*, subject: str, role: str) -> str:
    """Genera un access token de corta duración."""
    return _create_token(
        subject=subject,
        role=role,
        expires_delta=timedelta(seconds=settings.TOKEN_EXPIRES),
        token_type="access",
    )


def create_refresh_token(*, subject: str, role: str) -> str:
    """Genera un refresh token de mayor duración."""
    return _create_token(
        subject=subject,
        role=role,
        expires_delta=timedelta(seconds=settings.REFRESH_EXPIRES),
        token_type="refresh",
    )


def decode_and_validate_token(token: str, *, expected_type: Optional[str] = None) -> Dict[str, Any]:
    """Decodifica y valida el token JWT; opcionalmente verifica tipo."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if "sub" not in payload or "role" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    if expected_type and payload.get("type") != expected_type:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    return payload


def get_current_user(authorization: str | None = Header(default=None)) -> Dict[str, Any]:
    """Lee el usuario actual del token JWT."""
    token = _extract_token(authorization)
    payload = decode_and_validate_token(token, expected_type="access")
    return {
        "account_id": payload.get("sub"),
        "role": payload.get("role"),
    }


def require_admin(current=Depends(get_current_user)) -> Dict[str, Any]:
    """Solo permite administradores."""
    if current.get("role") != Role.ADMINISTRATOR.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return current


def require_admin_or_coach(current=Depends(get_current_user)) -> Dict[str, Any]:
    """Solo permite administradores o entrenadores."""
    if current.get("role") not in {Role.ADMINISTRATOR.value, Role.COACH.value}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin or coach role required")
    return current


def require_authenticated(current=Depends(get_current_user)) -> Dict[str, Any]:
    """Solo permite usuarios autenticados."""
    return current
