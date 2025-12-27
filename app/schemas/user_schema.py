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

    @field_validator("type_identification", mode="before")
    @classmethod
    def _normalize_type_identification(cls, value: Any) -> str:
        if value is None:
            return "CEDULA"

        raw = str(value).strip().lower()
        mapping = {
            "dni": "CEDULA",
            "cedula": "CEDULA",
            "cédula": "CEDULA",
            "cedula_ec": "CEDULA",
            "passport": "PASSPORT",
            "pasaporte": "PASSPORT",
            "ruc": "RUC",
        }
        return mapping.get(raw, str(value).strip().upper())

    @field_validator("type_stament", mode="before")
    @classmethod
    def _normalize_type_stament(cls, value: Any) -> str:
        if value is None:
            return "EXTERNOS"
        raw = str(value).strip().lower()
        mapping = {
            "administrativos": "ADMINISTRATIVOS",
            "docentes": "DOCENTES",
            "estudiantes": "ESTUDIANTES",
            "trabajadores": "TRABAJADORES",
            "externos": "EXTERNOS",
        }
        return mapping.get(raw, str(value).strip().upper())


class AccountBase(BaseModel):
    """Campos base de cuenta de usuario."""

    email: EmailStr
    role: Role


class UserFilter(BaseModel):
    """Encapsula los parámetros de búsqueda y paginación."""

    page: int = Field(1, ge=1, description="Número de página")
    limit: int = Field(10, ge=1, le=100, description="Registros por página")
    search: Optional[str] = Field(None, description="Búsqueda por nombre o DNI")
    role: Optional[str] = Field(
        None, description="Filtrar por rol (Administrator/Coach)"
    )

    @property
    def skip(self) -> int:
        """Calcula automáticamente el offset para la BD."""
        return (self.page - 1) * self.limit


# ==========================================
# REQUEST SCHEMAS (Entradas)


class AdminCreateUserRequest(PersonBase, AccountBase):
    """Datos para crear un nuevo usuario (Admin/Coach)."""

    dni: str = Field(..., min_length=10, max_length=10, description="DNI (10 dígitos)")
    password: str = Field(..., min_length=8, max_length=64)

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


class UserDetailResponse(UserResponse):
    """Respuesta detallada de usuario (GET /id)."""

    first_name: str
    last_name: str
    direction: Optional[str]
    phone: Optional[str]
    type_identification: str
    type_stament: str
    created_at: datetime
    updated_at: Optional[datetime] = None


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
