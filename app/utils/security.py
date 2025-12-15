"""Security helpers: DNI validation, email rules, and JWT authentication."""

import re
from typing import Iterable, Optional
from pydantic import BaseModel
from app.utils.exceptions import ValidationException


class CurrentUser(BaseModel):
    """
    Modelo de usuario autenticado extraído del token JWT.
    
    Se utiliza para inyección de dependencias en endpoints protegidos.
    """
    id: int
    email: str
    role: str
    external_id: Optional[str] = None
    is_active: bool = True


def validate_ec_dni(value: str) -> str:
    """Valida DNI (10 dígitoss).
    """

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

