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
    """Valida DNI ecuatoriano de 10 dígitos.

    Args:
        value: Cadena con el DNI a validar (puede contener caracteres no numéricos).

    Returns:
        str: DNI validado conteniendo solo los 10 dígitos numéricos.

    Raises:
        ValidationException: Si el DNI es None, no tiene 10 dígitos, 
            la provincia es inválida, el formato es incorrecto, 
            o el dígito verificador no coincide.
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


def is_email_allowed(
    email: str, allowed_domains: Optional[Iterable[str]] = None
) -> bool:
    """Valida formato general del email y dominio permitido.

    Args:
        email: Dirección de correo electrónico a validar.
        allowed_domains: Lista opcional de dominios permitidos
        (ej: ['gmail.com', 'unl.edu.ec']).

    Returns:
        bool: True si el email tiene formato válido y pertenece a un dominio permitido 
            (si se especificó), False en caso contrario.
    """
    pattern = r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$"
    if not re.match(pattern, email):
        return False
    if allowed_domains:
        domain = email.split("@")[-1].lower()
        normalized = [d.lower() for d in allowed_domains]
        return domain in normalized
    return True


def hash_password(password: str) -> str:
    """Genera un hash seguro de la contraseña usando bcrypt.

    Args:
        password: Contraseña en texto plano a hashear.

    Returns:
        str: Hash de la contraseña.

    Raises:
        ValidationException: Si la contraseña está vacía o es None.
    """
    if not password:
        raise ValidationException("La contraseña es requerida")
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verifica si una contraseña en texto plano coincide con su hash.

    Args:
        password: Contraseña en texto plano a verificar.
        password_hash: Hash de la contraseña almacenado.

    Returns:
        bool: True si la contraseña coincide con el hash, False en caso contrario.
    """
    if not password or not password_hash:
        return False
    return _pwd_context.verify(password, password_hash)


def create_access_token(
    subject: str | int,
    expires_seconds: int | None = None,
    extra_claims: dict | None = None,
) -> str:
    """Genera un JWT firmado con expiración.

    Args:
        subject: Identificador del sujeto (generalmente ID de cuenta).
        expires_seconds: Tiempo de expiración en segundos. 
        Si es None, usa TOKEN_EXPIRES de configuración.
        extra_claims: Diccionario opcional con claims adicionales
        para incluir en el payload.

    Returns:
        str: Token JWT firmado.
    """

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
    """Genera un token para restablecimiento de contraseña.

    Args:
        account_id: ID de la cuenta para la cual se genera el token.
        email: Correo electrónico de la cuenta.
        expires_seconds: Tiempo de expiración en segundos 
        (por defecto 900 = 15 minutos).

    Returns:
        str: Token JWT con action='reset_password' para restablecimiento.
    """

    return create_access_token(
        subject=account_id,
        expires_seconds=expires_seconds,
        extra_claims={"action": "reset_password", "email": email},
    )


def decode_token(token: str) -> dict:
    """Decodifica y valida un JWT, retornando el payload decodificado.

    Args:
        token: Token JWT en formato de cadena a decodificar y validar.

    Returns:
        dict: Diccionario con el payload decodificado del JWT.

    Raises:
        UnauthorizedException: Si el token es inválido o ha expirado.
    """

    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError as exc:
        raise UnauthorizedException("Token inválido o expirado") from exc


def validate_reset_token(token: str) -> dict:
    """Valida que el token sea de tipo reset_password y retorna el payload.

    Args:
        token: Token JWT a validar.

    Returns:
        dict: Payload del token si es válido y tiene action='reset_password'.

    Raises:
        UnauthorizedException: Si el token es inválido, 
        expirado, o no tiene action='reset_password'.
    """

    payload = decode_token(token)
    if payload.get("action") != "reset_password":
        raise UnauthorizedException("Token de reset inválido")
    return payload


def get_current_account(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),  # noqa: B008
) -> Account:
    """Dependencia para obtener la cuenta autenticada desde el JWT.

    Args:
        token: JWT extraído del encabezado ``Authorization`` mediante
            el esquema ``OAuth2PasswordBearer``.
        db: Sesión de base de datos de SQLAlchemy usada para consultar
            la cuenta asociada al token.

    Returns:
        Account: Objeto de cuenta autenticada correspondiente al sujeto
        (``sub``) contenido en el token.

    Raises:
        HTTPException: Se lanza con estado HTTP 401 si el token es
        inválido (no contiene ``sub``) o si la cuenta asociada no existe
        o se encuentra inactiva.
    """
    payload = decode_token(token)
    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )

    account = AccountDAO().get_by_id(db, int(sub), only_active=True)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cuenta no encontrada o inactiva",
        )

    return account
