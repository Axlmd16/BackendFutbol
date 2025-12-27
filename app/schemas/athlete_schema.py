"""Esquemas Pydantic para atletas (inscripción/creación/edición/búsqueda)."""

from __future__ import annotations

import enum
from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums.sex import Sex
from app.schemas.base_schema import BaseSchema
from app.schemas.user_schema import PersonBase, TypeStament
from app.utils.exceptions import ValidationException
from app.utils.security import validate_ec_dni


class SexInput(str, enum.Enum):
    """Valores permitidos en request (mejor UX en docs que Sex='Male')."""

    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class AthleteInscriptionDTO(PersonBase):
    """Datos para alta de deportista UNL."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    dni: str = Field(..., min_length=10, max_length=10, description="DNI (10 dígitos)")

    # Datos específicos del atleta
    birth_date: Optional[date] = Field(
        default=None,
        description="Fecha de nacimiento (YYYY-MM-DD)",
        examples=["2000-01-31"],
    )
    sex: SexInput = Field(default=SexInput.MALE, description="Sexo")
    weight: Optional[float] = Field(default=None, ge=0)
    height: Optional[float] = Field(default=None, ge=0)

    @field_validator("dni", mode="before")
    @classmethod
    def _normalize_and_validate_dni(cls, value: Any) -> str:
        try:
            return validate_ec_dni(str(value))
        except ValidationException as exc:
            raise ValueError(exc.message) from exc

    @field_validator("sex", mode="before")
    @classmethod
    def _normalize_sex(cls, value: Any) -> SexInput:
        if value is None or value == "":
            return SexInput.MALE
        if isinstance(value, SexInput):
            return value
        raw = str(value).strip().lower()
        mapping = {
            "male": SexInput.MALE,
            "m": SexInput.MALE,
            "masculino": SexInput.MALE,
            "hombre": SexInput.MALE,
            "female": SexInput.FEMALE,
            "f": SexInput.FEMALE,
            "femenino": SexInput.FEMALE,
            "mujer": SexInput.FEMALE,
            "other": SexInput.OTHER,
            "otro": SexInput.OTHER,
        }
        if raw not in mapping:
            raise ValueError("El sexo debe ser MALE, FEMALE u OTHER")
        return mapping[raw]


class AthleteUpdateRequest(BaseModel):
    """Datos para editar un atleta (solo campos del atleta)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    birth_date: Optional[date] = Field(default=None, description="YYYY-MM-DD")
    sex: Optional[SexInput] = None
    type_athlete: Optional[TypeStament] = None
    weight: Optional[float] = Field(default=None, ge=0)
    height: Optional[float] = Field(default=None, ge=0)


class AthleteFilter(BaseModel):
    """Filtros para búsqueda/paginación de atletas."""

    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=100)
    search: Optional[str] = Field(None, description="Búsqueda por nombre o DNI")
    type_athlete: Optional[TypeStament] = None
    sex: Optional[SexInput] = None

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.limit


class AthleteCreateDB(BaseModel):
    """Schema interno: payload ya listo para AthleteDAO.create()."""

    external_person_id: str
    full_name: str
    dni: str
    type_athlete: str
    date_of_birth: Optional[date] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    sex: Sex

    model_config = ConfigDict(from_attributes=True)


class StatisticCreateDB(BaseModel):
    """Schema interno: payload listo para StatisticDAO.create()."""

    athlete_id: int
    matches_played: int = 0
    goals: int = 0
    assists: int = 0
    yellow_cards: int = 0
    red_cards: int = 0

    model_config = ConfigDict(from_attributes=True)


class AthleteInscriptionResponseDTO(BaseSchema):
    """Respuesta al registrar un deportista UNL."""

    athlete_id: int
    statistic_id: int
    full_name: str
    dni: str


# ==========================================
# SCHEMAS PARA REGISTRO DE MENORES
# ==========================================


class RepresentativeCreateSchema(BaseModel):
    """
    Datos del representante legal para registro de menor.

    Validaciones implementadas:
    - DNI ecuatoriano válido (10 dígitos con verificador)
    - Email con formato válido
    - Teléfono en formato internacional
    - Nombres y apellidos sin caracteres especiales peligrosos
    """

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    first_name: str = Field(
        ..., min_length=2, max_length=100, description="Nombres del representante"
    )
    last_name: str = Field(
        ..., min_length=2, max_length=100, description="Apellidos del representante"
    )
    dni: str = Field(
        ..., min_length=10, max_length=10, description="DNI ecuatoriano (10 dígitos)"
    )
    email: EmailStr = Field(..., description="Email del representante")
    phone: str = Field(
        ...,
        min_length=10,
        max_length=15,
        description="Teléfono (formato: +593991234567)",
    )
    address: str = Field(
        ...,
        min_length=5,
        max_length=255,
        description="Dirección completa del representante",
    )
    relationship_type: str = Field(
        ...,
        description=(
            "Tipo de relación (PADRE/MADRE, TUTOR LEGAL, ABUELO/A, TIO/A, etc.)"
        ),
    )

    @field_validator("dni", mode="before")
    @classmethod
    def _validate_dni(cls, value: Any) -> str:
        try:
            return validate_ec_dni(str(value))
        except ValidationException as exc:
            raise ValueError(exc.message) from exc

    @field_validator("phone", mode="before")
    @classmethod
    def _validate_phone(cls, value: Any) -> str:
        phone = str(value).strip()
        # Eliminar espacios y guiones
        phone_clean = phone.replace(" ", "").replace("-", "")

        # Validar formato internacional básico
        if not phone_clean.startswith("+"):
            raise ValueError(
                "El teléfono debe estar en formato internacional "
                "(ej: +593991234567)"
            )

        if len(phone_clean) < 10 or len(phone_clean) > 15:
            raise ValueError(
                "El teléfono debe tener entre 10 y 15 dígitos "
                "(incluyendo código de país)"
            )

        return phone

    @field_validator("relationship_type", mode="before")
    @classmethod
    def _normalize_relationship(cls, value: Any) -> str:
        relationship = str(value).strip().upper()

        valid_types = [
            "PADRE/MADRE",
            "TUTOR LEGAL",
            "ABUELO/A",
            "TIO/A",
            "HERMANO/A MAYOR",
            "OTRO",
        ]

        if relationship not in valid_types:
            raise ValueError(
                f"Tipo de relación inválido. "
                f"Debe ser uno de: {', '.join(valid_types)}"
            )

        return relationship


class MinorAthleteCreateSchema(BaseModel):
    """
    Schema para registrar deportista menor de edad.

    Validaciones de seguridad (OWASP Top 10):
    - A03:2021 Injection: Validación estricta de DNI, email, teléfono
    - A04:2021 Insecure Design: Requerimiento de autorización parental
    - A07:2021 Identification and Authentication Failures: Unicidad de DNI
    """

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    # Datos del menor
    first_name: str = Field(
        ..., min_length=2, max_length=100, description="Nombres del menor"
    )
    last_name: str = Field(
        ..., min_length=2, max_length=100, description="Apellidos del menor"
    )
    dni: str = Field(
        ..., min_length=10, max_length=10, description="DNI ecuatoriano del menor"
    )
    birth_date: date = Field(
        ..., description="Fecha de nacimiento (formato: YYYY-MM-DD)"
    )
    sex: SexInput = Field(
        default=SexInput.MALE,
        description="Sexo del menor (MALE, FEMALE, OTHER)",
    )

    # Autorización parental (OBLIGATORIA)
    parental_authorization: bool = Field(
        ...,
        description=(
            "Confirmación explícita de autorización parental. "
            "Debe ser true para procesar el registro."
        ),
    )

    # Datos del representante legal
    representative: RepresentativeCreateSchema = Field(
        ..., description="Información completa del representante legal"
    )

    @field_validator("dni", mode="before")
    @classmethod
    def _validate_minor_dni(cls, value: Any) -> str:
        try:
            return validate_ec_dni(str(value))
        except ValidationException as exc:
            raise ValueError(exc.message) from exc

    @field_validator("sex", mode="before")
    @classmethod
    def _normalize_sex(cls, value: Any) -> SexInput:
        if value is None or value == "":
            return SexInput.MALE
        if isinstance(value, SexInput):
            return value
        raw = str(value).strip().lower()
        mapping = {
            "male": SexInput.MALE,
            "m": SexInput.MALE,
            "masculino": SexInput.MALE,
            "hombre": SexInput.MALE,
            "female": SexInput.FEMALE,
            "f": SexInput.FEMALE,
            "femenino": SexInput.FEMALE,
            "mujer": SexInput.FEMALE,
            "other": SexInput.OTHER,
            "otro": SexInput.OTHER,
        }
        if raw not in mapping:
            raise ValueError("El sexo debe ser MALE, FEMALE u OTHER")
        return mapping[raw]

    @field_validator("birth_date", mode="after")
    @classmethod
    def _validate_age(cls, value: date) -> date:
        from datetime import datetime

        today = datetime.now().date()
        age = (
            today.year
            - value.year
            - ((today.month, today.day) < (value.month, value.day))
        )

        if age >= 18:
            raise ValueError(
                "El deportista debe ser menor de 18 años para este "
                "tipo de registro. Use el endpoint de registro estándar."
            )

        if age < 5:
            raise ValueError(
                "El deportista debe tener al menos 5 años para registrarse "
                "en la escuela de fútbol."
            )

        return value

    @field_validator("parental_authorization", mode="after")
    @classmethod
    def _validate_authorization(cls, value: bool) -> bool:
        if not value:
            raise ValueError(
                "Se requiere autorización parental explícita "
                "(parental_authorization=true) para registrar menores de edad."
            )
        return value


class RepresentativeResponseSchema(BaseSchema):
    """Schema de respuesta para representante creado/vinculado."""

    id: int
    first_name: str
    last_name: str
    dni: str
    email: str
    phone: str
    address: str
    relationship_type: str
    external_person_id: str
    created_at: datetime
    is_active: bool


class MinorAthleteResponseSchema(BaseSchema):
    """Schema de respuesta para menor registrado."""

    id: int
    first_name: str
    last_name: str
    dni: str
    birth_date: date
    sex: str
    type_athlete: str
    representative_id: int
    external_person_id: str
    created_at: datetime
    is_active: bool


class MinorAthleteRegistrationResponse(BaseModel):
    """
    Respuesta completa del registro de menor.

    Incluye datos del menor y del representante para confirmación.
    """

    athlete: MinorAthleteResponseSchema
    representative: RepresentativeResponseSchema

    model_config = ConfigDict(from_attributes=True)
