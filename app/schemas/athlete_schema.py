"""Esquemas Pydantic para atletas (inscripciÃ³n/creaciÃ³n/ediciÃ³n/bÃºsqueda)."""

from __future__ import annotations

import enum
from datetime import date
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums.sex import Sex
from app.schemas.base_schema import BaseSchema
from app.schemas.constants import DATE_FORMAT_DESCRIPTION
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

    dni: str = Field(..., min_length=10, max_length=10, description="DNI (10 di­gitos)")

    # Datos especÃ­ficos del atleta
    birth_date: Optional[date] = Field(
        default=None,
        description=f"Fecha de nacimiento ({DATE_FORMAT_DESCRIPTION})",
        examples=["2000-01-31"],
    )
    sex: SexInput = Field(default=SexInput.MALE, description="Sexo")
    weight: Optional[float] = Field(default=None, ge=0, le=300)
    height: Optional[float] = Field(
        default=None,
        ge=0.5,
        le=2.5,  # Máximo 2.50 metros
        description="Altura en metros (no puede ser negativa)",
    )

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

    birth_date: Optional[date] = Field(
        default=None, description=DATE_FORMAT_DESCRIPTION
    )
    sex: Optional[SexInput] = None
    type_athlete: Optional[TypeStament] = None
    weight: Optional[float] = Field(default=None, ge=0)
    height: Optional[float] = Field(
        default=None,
        ge=0,
        description="Altura en metros (no puede ser negativa)",
    )


class AthleteUpdateDTO(BaseModel):
    """Datos para actualizar un atleta incluyendo datos del MS de personas."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    # Datos personales
    first_name: Optional[str] = Field(default=None, min_length=2)
    last_name: Optional[str] = Field(default=None, min_length=2)
    birth_date: Optional[date] = Field(
        default=None, description=DATE_FORMAT_DESCRIPTION
    )
    sex: Optional[SexInput] = None
    type_identification: Optional[str] = None
    dni: Optional[str] = None
    type_stament: Optional[str] = None
    # Datos de contacto (se sincronizan con MS de personas)
    direction: Optional[str] = Field(default=None, description="Dirección")
    phone: Optional[str] = Field(default=None, description="Teléfono")
    # Datos físicos
    height: Optional[float] = Field(
        default=None,
        ge=0,
        description="Altura en metros (no puede ser negativa)",
    )

    weight: Optional[float] = Field(default=None, ge=0)


class AthleteFilter(BaseModel):
    """Filtros para busqueda/paginación de atletas."""

    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=100)
    search: Optional[str] = Field(None, description="Búsqueda por nombre o DNI")
    type_athlete: Optional[TypeStament] = None
    sex: Optional[SexInput] = None
    is_active: Optional[bool] = Field(
        default=None, description="Filtrar por estado activo (None = todos)"
    )
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    @model_validator(mode="after")
    def _validate_date_range(self) -> "AthleteFilter":
        if self.start_date and self.end_date and self.start_date > self.end_date:
            # Esto es lo que genera el error 422 para el usuario
            raise ValueError(
                "Rango de fechas inválido: la fecha de inicio es posterior a la de fin"
            )
        return self

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

    athlete_id: int = Field(..., gt=0, description="ID del atleta (debe ser positivo)")
    matches_played: int = 0
    goals: int = 0
    assists: int = 0
    yellow_cards: int = 0
    red_cards: int = 0

    model_config = ConfigDict(from_attributes=True)


class AthleteResponse(BaseSchema):
    """Respuesta básica de atleta para listados."""

    id: int
    full_name: str
    dni: str
    type_athlete: str
    sex: str
    is_active: bool
    has_account: bool = False  # True si ya tiene cuenta en el sistema (pasante)
    height: Optional[float] = None
    weight: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AthleteDetailResponse(BaseSchema):
    """Respuesta detallada de atleta con datos del MS de personas."""

    id: int
    external_person_id: str
    full_name: str
    dni: str
    type_athlete: str
    date_of_birth: Optional[date] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    sex: str
    is_active: bool
    created_at: str
    updated_at: Optional[str] = None
    # Campos del MS de personas (sin duplicados)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    direction: Optional[str] = None
    phone: Optional[str] = None
    type_identification: Optional[str] = None
    type_stament: Optional[str] = None
    photo: Optional[str] = None
    # Campos del representante (para menores de edad)
    representative_id: Optional[int] = None
    representative_name: Optional[str] = None
    representative_dni: Optional[str] = None
    representative_phone: Optional[str] = None
    representative_email: Optional[str] = None
    representative_relationship: Optional[str] = None


class AthleteUpdateResponse(BaseSchema):
    """Respuesta tras actualizar un atleta."""

    id: int
    full_name: str
    height: Optional[float] = None
    weight: Optional[float] = None
    updated_at: Optional[str] = None


class AthleteInscriptionResponseDTO(BaseSchema):
    """Respuesta al registrar un deportista UNL."""

    athlete_id: int
    statistic_id: int
    full_name: str
    dni: str


# ==========================================
# SCHEMAS PARA MENORES DE EDAD


class RepresentativeDataDTO(BaseModel):
    """Datos del representante para inscripción de menor."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    dni: str = Field(..., min_length=10, max_length=10, description="DNI (10 dígitos)")
    phone: Optional[str] = Field(default="S/N", description="Teléfono de contacto")
    email: Optional[str] = Field(default=None, description="Email (opcional)")
    direction: Optional[str] = Field(default="S/N", description="Dirección")
    type_identification: str = Field(default="CEDULA")
    # type_stament siempre será EXTERNOS para representantes de menores
    relationship_type: str = Field(
        ..., description="Tipo de relación: FATHER, MOTHER, LEGAL_GUARDIAN"
    )

    @field_validator("dni", mode="before")
    @classmethod
    def _normalize_and_validate_dni(cls, value: Any) -> str:
        try:
            return validate_ec_dni(str(value))
        except ValidationException as exc:
            raise ValueError(exc.message) from exc


class MinorAthleteDataDTO(BaseModel):
    """Datos del atleta menor para inscripción."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    dni: str = Field(..., min_length=10, max_length=10, description="DNI (10 dígitos)")
    birth_date: date = Field(..., description="Fecha de nacimiento (YYYY-MM-DD)")
    sex: SexInput = Field(default=SexInput.MALE, description="Sexo")
    height: Optional[float] = Field(
        default=None,
        description="Altura en metros (mínimo 1.0 m, máximo 1.90 m)",
    )
    weight: Optional[float] = Field(
        default=None, description="Peso en kg (mínimo 15 kg, máximo 90 kg)"
    )
    direction: Optional[str] = Field(default="S/N", description="Dirección")
    phone: Optional[str] = Field(default="S/N", description="Teléfono")
    type_identification: str = Field(default="CEDULA")

    # type_stament siempre será EXTERNOS para menores de edad

    @field_validator("dni", mode="before")
    @classmethod
    def _normalize_and_validate_dni(cls, value: Any) -> str:
        try:
            return validate_ec_dni(str(value))
        except ValidationException as exc:
            raise ValueError(exc.message) from exc

    @field_validator("birth_date", mode="after")
    @classmethod
    def _validate_minor_age(cls, value: date) -> date:
        """Valida que el atleta sea menor de edad (entre 5 y 17 años)."""
        from datetime import date as date_type

        today = date_type.today()

        if value > today:
            raise ValueError("La fecha de nacimiento no puede ser en el futuro")

        age = (
            today.year
            - value.year
            - ((today.month, today.day) < (value.month, value.day))
        )

        if age >= 18:
            raise ValueError(
                f"El deportista debe ser menor de 18 años. Edad calculada: {age} años"
            )

        if age < 5:
            raise ValueError(
                f"El deportista debe tener al menos 5 años. Edad calculada: {age} años"
            )

        return value

    @field_validator("height")
    @classmethod
    def _validate_minor_height(cls, value: Optional[float]) -> Optional[float]:
        """Valida que la altura esté dentro de los límites para menores."""
        if value is None:
            return value

        if value < 1.0:
            raise ValueError(
                f"La altura mínima para atletas menores es 1.0 metro. "
                f"Altura ingresada: {value} m"
            )

        if value > 1.90:
            raise ValueError(
                f"La altura máxima para atletas menores es 1.90 metros. "
                f"Altura ingresada: {value} m"
            )

        return value

    @field_validator("weight")
    @classmethod
    def _validate_minor_weight(cls, value: Optional[float]) -> Optional[float]:
        """Valida que el peso esté dentro de los límites para menores."""
        if value is None:
            return value

        if value < 15:
            raise ValueError(
                f"El peso mínimo para atletas menores es 15 kg. "
                f"Peso ingresado: {value} kg"
            )

        if value > 90:
            raise ValueError(
                f"El peso máximo para atletas menores es 90 kg. "
                f"Peso ingresado: {value} kg"
            )

        return value

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
            "female": SexInput.FEMALE,
            "f": SexInput.FEMALE,
            "femenino": SexInput.FEMALE,
            "other": SexInput.OTHER,
            "otro": SexInput.OTHER,
        }
        if raw not in mapping:
            raise ValueError("El sexo debe ser MALE, FEMALE u OTHER")
        return mapping[raw]


class MinorAthleteInscriptionDTO(BaseModel):
    """Datos para inscribir un deportista menor de edad con su representante."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    representative: RepresentativeDataDTO
    athlete: MinorAthleteDataDTO


class MinorAthleteInscriptionResponseDTO(BaseSchema):
    """Respuesta al registrar un deportista menor con su representante."""

    representative_id: int
    representative_full_name: str
    representative_dni: str
    representative_is_new: bool  # True si se creó nuevo, False si ya existía
    athlete_id: int
    athlete_full_name: str
    athlete_dni: str
    statistic_id: int
