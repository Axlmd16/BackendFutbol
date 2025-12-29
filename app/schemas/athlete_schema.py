"""Esquemas Pydantic para atletas (inscripciÃ³n/creaciÃ³n/ediciÃ³n/bÃºsqueda)."""

from __future__ import annotations

import enum
from datetime import date
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

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

    dni: str = Field(..., min_length=10, max_length=10, description="DNI (10 dÃ­gitos)")

    # Datos especÃ­ficos del atleta
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



class AthleteUpdateDTO(BaseModel):
    """Datos para actualizar un atleta incluyendo datos del MS de personas."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    height: Optional[float] = Field(default=None, ge=0)
    weight: Optional[float] = Field(default=None, ge=0)
    direction: Optional[str] = Field(default=None, description="Dirección")
    phone: Optional[str] = Field(default=None, description="Teléfono")

class AthleteFilter(BaseModel):
    """Filtros para bÃºsqueda/paginaciÃ³n de atletas."""

    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=100)
    search: Optional[str] = Field(None, description="BÃºsqueda por nombre o DNI")
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


class AthleteResponse(BaseSchema):
    """Respuesta básica de atleta para listados."""

    id: int
    full_name: str
    dni: str
    type_athlete: str
    sex: str
    is_active: bool
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
