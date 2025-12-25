"""Security helpers: DNI validation, email rules y JWT/password helpers."""

import re
from datetime import datetime, timedelta, timezone
from typing import Iterable, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.dao.account_dao import AccountDAO
from app.models.account import Account
from app.utils.exceptions import UnauthorizedException, ValidationException

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/accounts/login")


def validate_ec_dni(value: str) -> str:
    """Valida DNI (10 dígitoss)."""

    if value is None:
        raise ValidationException("DNI es requerido")

    digits = re.sub(r"\D", "", value)
    if len(digits) != 10:
        raise ValidationException("El DNI debe tener exactamente 10 digitos")

    province = int(digits[:2])
    if not ((1 <= province <= 24) or province == 30):
        raise ValidationException("Provincia del DNI invalida")

    third = int(digits[2])
    if third > 5:
        raise ValidationException("Formato de DNI invalido")

    coef = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    total = 0
    for i in range(9):
        prod = int(digits[i]) * coef[i]
        total += prod if prod < 10 else prod - 9

    check_digit = (10 - (total % 10)) % 10
    if check_digit != int(digits[9]):
        raise ValidationException("Dígito verificador del DNI inválido")

    return digits


def is_email_allowed(
    email: str, allowed_domains: Optional[Iterable[str]] = None
) -> bool:
    """Valida formato general y dominio permitido (si se especifica)."""
    pattern = r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$"
    if not re.match(pattern, email):
        return False
    if allowed_domains:
        domain = email.split("@")[-1].lower()
        normalized = [d.lower() for d in allowed_domains]
        return domain in normalized
    return True


def hash_password(password: str) -> str:
    if not password:
        raise ValidationException("La contraseña es requerida")
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    if not password or not password_hash:
        return False
    return _pwd_context.verify(password, password_hash)


def create_access_token(
    subject: str | int,
    expires_seconds: int | None = None,
    extra_claims: dict | None = None,
) -> str:
    """Genera un JWT firmado con expiración."""

    exp_seconds = expires_seconds or settings.TOKEN_EXPIRES
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=exp_seconds)).timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_reset_token(account_id: int, email: str, expires_seconds: int = 900) -> str:
    """Genera un token corto para restablecimiento de contraseña (por defecto 15 min)."""

    return create_access_token(
        subject=account_id,
        expires_seconds=expires_seconds,
        extra_claims={"action": "reset_password", "email": email},
    )


def decode_token(token: str) -> dict:
    """Decodifica y valida un JWT, retornando el payload."""

    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError as exc:
        raise UnauthorizedException("Token invalido o expirado") from exc


def validate_reset_token(token: str) -> dict:
    """Valida que el token sea de tipo reset_password y retorna el payload."""

    payload = decode_token(token)
    if payload.get("action") != "reset_password":
        raise UnauthorizedException("Token de reset invalido")
    return payload


def get_current_account(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),  # noqa: B008
) -> Account:
    """Dependencia para obtener la cuenta autenticada desde el JWT."""

    payload = decode_token(token)
    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido",
        )

    account = AccountDAO().get_by_id(db, int(sub), only_active=True)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cuenta no encontrada o inactiva",
        )

    return account
