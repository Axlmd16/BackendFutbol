import enum
import re
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums.rol import Role

# Constantes para validaciones
PHONE_REGEX = re.compile(r"^(\+593|0)?[2-9]\d{7,8}$")
EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9]([a-zA-Z0-9._-]{0,62}[a-zA-Z0-9])?@"
    r"[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.[a-zA-Z]{2,}$"
)
MAX_DIRECTION_LENGTH = 500
MAX_EMAIL_LENGTH = 254
VALID_TYPE_IDENTIFICATIONS = {"CEDULA", "PASSPORT", "RUC"}


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
    direction: Optional[str] = Field(default="S/N", max_length=MAX_DIRECTION_LENGTH)
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
        # Validar que solo contenga letras y espacios
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$", v):
            raise ValueError("El nombre solo puede contener letras y espacios")
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
        # Validar que solo contenga letras y espacios
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$", v):
            raise ValueError("El apellido solo puede contener letras y espacios")
        return v

    @field_validator("direction", mode="before")
    @classmethod
    def _validate_direction(cls, value: Any) -> str:
        if value is None:
            return "S/N"
        v = str(value).strip()
        if len(v) > MAX_DIRECTION_LENGTH:
            raise ValueError(
                f"La dirección no puede exceder {MAX_DIRECTION_LENGTH} caracteres"
            )
        return v if v else "S/N"

    @field_validator("phone", mode="before")
    @classmethod
    def _validate_phone(cls, value: Any) -> str:
        if value is None or str(value).strip() == "" or str(value).strip() == "S/N":
            return "S/N"
        v = str(value).strip()
        # Limpiar caracteres no numéricos excepto + al inicio
        cleaned = re.sub(r"[^\d+]", "", v)
        if cleaned.startswith("+"):
            cleaned = "+" + cleaned[1:].replace("+", "")
        # Validar formato de teléfono ecuatoriano
        if not PHONE_REGEX.match(cleaned):
            raise ValueError(
                "Formato de teléfono inválido. Use formato ecuatoriano: "
                "09XXXXXXXX, 07XXXXXXX o +593XXXXXXXXX"
            )
        return cleaned

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
        normalized = mapping.get(raw, str(value).strip().upper())

        if normalized not in VALID_TYPE_IDENTIFICATIONS:
            valid_types = ", ".join(VALID_TYPE_IDENTIFICATIONS)
            raise ValueError(f"Tipo de identificación inválido. Use: {valid_types}")
        return normalized

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

    email: str = Field(..., max_length=MAX_EMAIL_LENGTH)
    role: Role

    @field_validator("email", mode="before")
    @classmethod
    def _validate_email(cls, value: Any) -> str:
        if value is None:
            raise ValueError("El correo electrónico es requerido")
        v = str(value).strip().lower()
        if len(v) > MAX_EMAIL_LENGTH:
            raise ValueError(
                f"El correo electrónico no puede exceder {MAX_EMAIL_LENGTH} caracteres"
            )
        if not EMAIL_REGEX.match(v):
            raise ValueError(
                "El formato del correo electrónico es inválido. "
                "Use un formato válido como ejemplo@dominio.com"
            )
        return v


class UserFilter(BaseModel):
    """Encapsula los parámetros de búsqueda y paginación."""

    page: int = Field(1, ge=1, description="Número de página")
    limit: int = Field(10, ge=1, le=100, description="Registros por página (máx. 100)")
    search: Optional[str] = Field(
        None, max_length=100, description="Búsqueda por nombre o DNI"
    )
    role: Optional[str] = Field(
        None, description="Filtrar por rol (Administrator/Coach)"
    )
    is_active: Optional[bool] = Field(
        None, description="Filtrar por estado (True=activo, False=inactivo, None=todos)"
    )

    @field_validator("search", mode="before")
    @classmethod
    def _sanitize_search(cls, value: Any) -> Optional[str]:
        if value is None:
            return None
        v = str(value).strip()
        # Prevenir inyección SQL básica y caracteres peligrosos
        v = re.sub(r"[;'\"\-\-]", "", v)
        return v if v else None

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
        # Limpiar caracteres no numéricos
        digits = re.sub(r"\D", "", v)
        if len(digits) != 10:
            raise ValueError("El DNI debe tener exactamente 10 dígitos numéricos")
        # Validación básica de provincia (la validación completa se hace en security.py)
        province = int(digits[:2])
        if not ((1 <= province <= 24) or province == 30):
            raise ValueError("El DNI tiene un código de provincia inválido")
        return digits

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
        # Validar complejidad de contraseña
        if not re.search(r"[A-Z]", v):
            raise ValueError("La contraseña debe contener al menos una mayúscula")
        if not re.search(r"[a-z]", v):
            raise ValueError("La contraseña debe contener al menos una minúscula")
        if not re.search(r"\d", v):
            raise ValueError("La contraseña debe contener al menos un número")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\;'/`~]", v):
            raise ValueError(
                "La contraseña debe contener al menos un carácter especial"
            )
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
    external: str = Field(..., min_length=30, max_length=36)  # UUID tiene máx 36 chars
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
        # Validar complejidad de contraseña
        if not re.search(r"[A-Z]", v):
            raise ValueError("La contraseña debe contener al menos una mayúscula")
        if not re.search(r"[a-z]", v):
            raise ValueError("La contraseña debe contener al menos una minúscula")
        if not re.search(r"\d", v):
            raise ValueError("La contraseña debe contener al menos un número")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\;'/`~]", v):
            raise ValueError(
                "La contraseña debe contener al menos un carácter especial"
            )
        return v


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
