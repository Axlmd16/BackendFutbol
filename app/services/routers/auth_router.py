from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.dao.account_dao import AccountDAO
from app.dao.user_dao import UserDAO
from app.models.enums.rol import Role
from app.schemas.auth_schema import (
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    ResetPasswordRequest,
    UserPayload,
)
from app.utils.security import verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])

account_dao = AccountDAO()
user_dao = UserDAO()


def _map_role_for_frontend(role: Role) -> str:
    # Frontend usa strings en español para RoleRoute.
    mapping = {
        Role.ADMINISTRATOR: "admin",
        Role.COACH: "entrenador",
        Role.INTERN: "pasante",
    }
    return mapping.get(role, role.value)


def _create_access_token(*, user_id: int, email: str, role: Role) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(seconds=int(settings.TOKEN_EXPIRES))

    claims = {
        "sub": str(user_id),
        "email": email,
        "role": role.value,
        "exp": exp,
        "iat": now,
    }

    return jwt.encode(
        claims,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def _decode_bearer_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        ) from e


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Login (temporal) con cuenta local",
    description="Autenticación temporal usando accounts locales (email + password).",
)
def login(
    payload: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> LoginResponse:
    account = account_dao.get_by_field(
        db,
        "email",
        payload.email.lower(),
        only_active=True,
    )
    if not account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    if not verify_password(payload.password, account.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    user = account.user or user_dao.get_by_id(db, account.user_id, only_active=False)
    if not user:
        raise HTTPException(status_code=500, detail="Cuenta sin usuario asociado")

    token = _create_access_token(
        user_id=user.id,
        email=account.email,
        role=account.role,
    )

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=UserPayload(
            id=user.id,
            full_name=user.full_name,
            dni=user.dni,
            email=account.email,
            role=_map_role_for_frontend(account.role),
        ),
    )


@router.get(
    "/me",
    response_model=UserPayload,
    status_code=status.HTTP_200_OK,
    summary="Usuario actual",
)
def me(
    db: Annotated[Session, Depends(get_db)],
    authorization: Annotated[Optional[str], Header()] = None,
) -> UserPayload:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token requerido",
        )

    token = authorization.split(" ", 1)[1].strip()
    claims = _decode_bearer_token(token)

    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )

    user = user_dao.get_by_id(db, int(user_id), only_active=False)
    if not user or not user.account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )

    return UserPayload(
        id=user.id,
        full_name=user.full_name,
        dni=user.dni,
        email=user.account.email,
        role=_map_role_for_frontend(user.account.role),
    )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout (noop)",
)
def logout() -> dict:
    # No hay blacklist de tokens por ahora.
    return {"ok": True}


@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    summary="Forgot password (mock)",
)
def forgot_password(_: ForgotPasswordRequest) -> dict:
    # Mock: no enviamos correo aún.
    return {"ok": True}


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Reset password (mock)",
)
def reset_password(_: ResetPasswordRequest) -> dict:
    # Mock: no cambiamos contraseña aún.
    return {"ok": True}


@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    summary="Refresh token (mock)",
)
def refresh_token() -> dict:
    return {"ok": True}
