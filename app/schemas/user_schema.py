from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums.rol import Role

# ==========================================
# BASES (Reutilizables)


class PersonBase(BaseModel):
    """Campos comunes de información personal."""

    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    direction: Optional[str] = Field(default="S/N")
    phone: Optional[str] = Field(default="S/N")
    type_identification: str = Field(default="CEDULA")
    type_stament: str = Field(default="EXTERNOS")

    model_config = ConfigDict(validate_assignment=True, from_attributes=True)


class AccountBase(BaseModel):
    """Campos base de cuenta de usuario."""

    email: EmailStr
    role: Role


# ==========================================
# REQUEST SCHEMAS (Entradas)


class AdminCreateUserRequest(PersonBase, AccountBase):
    """Datos para crear un nuevo usuario (Admin/Coach)."""

    dni: str = Field(..., min_length=10, max_length=10, description="DNI (10 dígitos)")
    password: str = Field(..., min_length=8, max_length=64)

    # Validar el rol
    @field_validator("role", mode="before")
    @classmethod
    def _parse_role(cls, value: Any) -> Role:
        if isinstance(value, Role):
            if value == Role.INTERN:
                raise ValueError("Rol inválido. Use Administrator o Coach")
            return value

        if value is None:
            raise ValueError("Rol es requerido")

        raw = str(value).strip().lower()
        mapping = {
            "administrador": Role.ADMINISTRATOR,
            "administrator": Role.ADMINISTRATOR,
            "admin": Role.ADMINISTRATOR,
            "entrenador": Role.COACH,
            "coach": Role.COACH,
        }

        if raw not in mapping:
            raise ValueError("Rol inválido. Use Administrator o Coach")

        return mapping[raw]


class AdminUpdateUserRequest(PersonBase):
    """Datos para actualizar un usuario existente."""

    id: int = Field(..., gt=0, description="ID del usuario a actualizar")


class CreatePersonInMSRequest(PersonBase):
    """DTO para microservicio de usuarios."""

    dni: str = Field(..., min_length=10, max_length=10)


class CreateLocalUserAccountRequest(AccountBase):
    """DTO interno para crear cuenta local."""

    full_name: str = Field(..., min_length=2, max_length=200)
    external: str = Field(..., min_length=30, max_length=50)
    dni: str = Field(..., min_length=10, max_length=10)
    password: str = Field(..., min_length=8, max_length=64)


# ==========================================
# RESPONSE SCHEMAS (Salidas)


class UserResponseBase(BaseModel):
    """Base para todas las respuestas de usuario."""

    id: int
    full_name: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class UserResponse(UserResponseBase):
    """Respuesta estándar de usuario (GET /all, GET /id)."""

    dni: str
    email: EmailStr
    external: str
    is_active: bool


class AdminCreateUserResponse(UserResponseBase):
    """Respuesta tras crear un usuario."""

    email: EmailStr
    account_id: int
    external: str


class AdminUpdateUserResponse(UserResponseBase):
    """Respuesta tras actualizar un usuario."""

    email: EmailStr
    updated_at: datetime
    is_active: bool
