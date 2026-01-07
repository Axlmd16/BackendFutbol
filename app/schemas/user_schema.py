import enum
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums.rol import Role


class TypeStament(str, enum.Enum):
    """Valores permitidos para type_stament."""

    DOCENTES = "DOCENTES"
    ESTUDIANTES = "ESTUDIANTES"
    ADMINISTRATIVOS = "ADMINISTRATIVOS"
    TRABAJADORES = "TRABAJADORES"
    EXTERNOS = "EXTERNOS"


class PersonBase(BaseModel):
    """Campos comunes de información personal."""

    first_name: str = Field(...)
    last_name: str = Field(...)
    direction: Optional[str] = Field(default="S/N")
    phone: Optional[str] = Field(default="S/N")
    type_identification: str = Field(default="CEDULA")
    type_stament: TypeStament = Field(default=TypeStament.EXTERNOS)
    model_config = ConfigDict(validate_assignment=True, from_attributes=True)

    @field_validator("first_name", mode="before")
    @classmethod
    def _validate_first_name(cls, value: Any) -> str:
        if value is None:
            raise ValueError("El nombre es requerido")
        v = str(value).strip()
        if len(v) < 2:
            raise ValueError("El nombre debe tener al menos 2 caracteres")
        if len(v) > 100:
            raise ValueError("El nombre no puede exceder 100 caracteres")
        return v

    @field_validator("last_name", mode="before")
    @classmethod
    def _validate_last_name(cls, value: Any) -> str:
        if value is None:
            raise ValueError("El apellido es requerido")
        v = str(value).strip()
        if len(v) < 2:
            raise ValueError("El apellido debe tener al menos 2 caracteres")
        if len(v) > 100:
            raise ValueError("El apellido no puede exceder 100 caracteres")
        return v

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
    def _normalize_type_stament(cls, value: Any) -> TypeStament:
        if value is None:
            return TypeStament.EXTERNOS

        if isinstance(value, TypeStament):
            return value

        raw = str(value).strip().lower()
        mapping = {
            "administrativos": "ADMINISTRATIVOS",
            "docente": "DOCENTES",
            "docentes": "DOCENTES",
            "estudiantes": "ESTUDIANTES",
            "trabajadores": "TRABAJADORES",
            "externo": "EXTERNOS",
            "externos": "EXTERNOS",
        }

        normalized = mapping.get(raw, str(value).strip().upper())
        try:
            return TypeStament(normalized)
        except ValueError as exc:
            raise ValueError(
                "type_stament inválido. Use: DOCENTES, ESTUDIANTES, "
                "ADMINISTRATIVOS, TRABAJADORES, EXTERNOS"
            ) from exc


class AccountBase(BaseModel):
    """Campos base de cuenta de usuario."""

    email: str = Field(...)
    role: Role

    @field_validator("email", mode="before")
    @classmethod
    def _validate_email(cls, value: Any) -> str:
        if value is None:
            raise ValueError("El correo electrónico es requerido")
        import re

        v = str(value).strip().lower()
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_regex, v):
            raise ValueError("El formato del correo electrónico es inválido")
        return v


class UserFilter(BaseModel):
    """Encapsula los parámetros de búsqueda y paginación."""

    page: int = Field(1, ge=1, description="Número de página")
    limit: int = Field(10, ge=1, le=1000, description="Registros por página")
    search: Optional[str] = Field(None, description="Búsqueda por nombre o DNI")
    role: Optional[str] = Field(
        None, description="Filtrar por rol (Administrator/Coach)"
    )
    is_active: Optional[bool] = Field(
        None, description="Filtrar por estado (True=activo, False=inactivo, None=todos)"
    )

    @property
    def skip(self) -> int:
        """Calcula automáticamente el offset para la BD."""
        return (self.page - 1) * self.limit


# REQUEST SCHEMAS (Entradas)


class AdminCreateUserRequest(PersonBase, AccountBase):
    """Datos para crear un nuevo usuario (Admin/Coach)."""

    dni: str = Field(...)
    password: str = Field(...)

    @field_validator("dni", mode="before")
    @classmethod
    def _validate_dni(cls, value: Any) -> str:
        if value is None:
            raise ValueError("El DNI es requerido")
        v = str(value).strip()
        if len(v) != 10:
            raise ValueError("El DNI debe tener exactamente 10 dígitos")
        return v

    @field_validator("password", mode="before")
    @classmethod
    def _validate_password(cls, value: Any) -> str:
        if value is None:
            raise ValueError("La contraseña es requerida")
        v = str(value)
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        if len(v) > 64:
            raise ValueError("La contraseña no puede exceder 64 caracteres")
        return v

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


# ==========================================
# INTERN SCHEMAS (Pasantes)


class PromoteAthleteRequest(BaseModel):
    """Datos para promover un atleta a pasante."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=64)


class InternFilter(BaseModel):
    """Filtros para listar pasantes."""

    page: int = Field(1, ge=1, description="Número de página")
    limit: int = Field(10, ge=1, le=100, description="Registros por página")
    search: Optional[str] = Field(None, description="Búsqueda por nombre o DNI")

    @property
    def skip(self) -> int:
        """Calcula automáticamente el offset para la BD."""
        return (self.page - 1) * self.limit


class InternResponse(BaseModel):
    """Respuesta de un pasante."""

    id: int
    user_id: int
    full_name: str
    dni: str
    email: EmailStr
    athlete_id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PromoteAthleteResponse(BaseModel):
    """Respuesta tras promover un atleta a pasante."""

    id: int
    user_id: int
    full_name: str
    email: EmailStr
    role: str
