"""Utilidades de seguridad: hashing, contraseñas y sanitización."""

import html
import re
import secrets
import string
from typing import Iterable, List, Optional
from passlib.context import CryptContext
from app.utils.exceptions import ValidationException

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Caracteres seguros para contraseñas temporales
_PASSWORD_ALPHABET = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"  # limitado para evitar caracteres raros en emails

def hash_password(plain_password: str) -> str:
    """Hashea una contraseña en bcrypt."""
    return pwd_context.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña en texto plano contra un hash."""
    return pwd_context.verify(plain_password, hashed_password)

def generate_secure_password(length: int = 14) -> str:
    """Genera una contraseña aleatoria fuerte."""
    length = max(12, min(length, 48))  # forzar longitud mínima/máxima
    return "".join(secrets.choice(_PASSWORD_ALPHABET) for _ in range(length))

def sanitize_text(value: Optional[str], max_length: Optional[int] = None) -> str:
    """Aplica sanitización básica (strip, escape html, remueve scripts y controles)."""
    if value is None:
        return ""
    cleaned = value.strip()
    cleaned = re.sub(r"<[^>]*>", "", cleaned)  # elimina tags HTML simples
    cleaned = html.escape(cleaned, quote=True)
    cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", cleaned)  # caracteres de control
    if max_length:
        cleaned = cleaned[:max_length]
    return cleaned

def sanitize_email(value: str) -> str:
    """Normaliza email a lowercase y aplica sanitización ligera."""
    return sanitize_text(value, max_length=150).lower()

def validate_ec_dni(value: str) -> str:
    """Valida y normaliza DNI ecuatoriano (10 dígitos, último es dígito verificador).
    """

    if value is None:
        raise ValidationException("DNI es requerido")

    digits = re.sub(r"\D", "", value)
    if len(digits) != 10:
        raise ValidationException("El DNI debe tener exactamente 10 dígitos")

    province = int(digits[:2])
    if not ((1 <= province <= 24) or province == 30):
        raise ValidationException("Provincia del DNI inválida")

    third = int(digits[2])
    if third > 5:
        raise ValidationException("Formato de DNI inválido para persona natural")

    coef = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    total = 0
    for i in range(9):
        prod = int(digits[i]) * coef[i]
        total += prod if prod < 10 else prod - 9

    check_digit = (10 - (total % 10)) % 10
    if check_digit != int(digits[9]):
        raise ValidationException("Dígito verificador del DNI inválido")

    return digits

def is_email_allowed(email: str, allowed_domains: Optional[Iterable[str]] = None) -> bool:
    """Valida formato general y dominio permitido (si se especifica)."""
    pattern = r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$"
    if not re.match(pattern, email):
        return False
    if allowed_domains:
        domain = email.split("@")[-1].lower()
        normalized = [d.lower() for d in allowed_domains]
        return domain in normalized
    return True

def normalize_role(role_value: str) -> str:
    """Normaliza el rol a minúsculas para mapearlo fácilmente."""
    return sanitize_text(role_value).lower()
