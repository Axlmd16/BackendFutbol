"""Security helpers: DNI validation, email rules y JWT/password helpers."""

import re
from datetime import datetime, timedelta, timezone
from typing import Iterable, Optional

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.utils.exceptions import ValidationException

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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
