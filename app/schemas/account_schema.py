import re

from pydantic import BaseModel, EmailStr, Field, field_validator


class LoginRequest(BaseModel):
    """Datos solicitados para iniciar sesión.

    Reglas de validación:
    - `email` debe tener un formato de correo válido.
    - `password` debe tener entre 8 y 64 caracteres.

    Nota: No se valida la complejidad en login para no bloquear
    contraseñas antiguas y evitar filtrar políticas a atacantes.
    """

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=64)


class LoginResponse(BaseModel):
    """Datos respuesta al iniciar sesión.

    Attributes:
        access_token: Token JWT generado tras autenticación correcta.
        token_type: Esquema de autenticación, típicamente "bearer".
        expires_in: Tiempo de vida del token (segundos) desde su emisión.
    """

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class PasswordResetRequest(BaseModel):
    """Datos para solicitar restablecimiento de contraseña.

    Reglas:
    - `email` debe ser un correo válido.
    """

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Datos para confirmar restablecimiento de contraseña.

    Attributes:
        token: Token de restablecimiento recibido por correo.
        new_password: Nueva contraseña (8-64 caracteres).
    """

    token: str
    new_password: str = Field(..., min_length=8, max_length=64)

    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Valida la complejidad de la contraseña."""
        if not re.search(r'[A-Z]', v):
            raise ValueError('La contraseña debe contener al menos una letra mayúscula')
        if not re.search(r'[a-z]', v):
            raise ValueError('La contraseña debe contener al menos una letra minúscula')
        if not re.search(r'[0-9]', v):
            raise ValueError('La contraseña debe contener al menos un número')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('La contraseña debe contener al menos un carácter especial (!@#$%^&*(),.?":{}|<>)')  # noqa: E501
        return v