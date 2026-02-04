"""Esquemas Pydantic para representantes de deportistas menores de edad."""

from __future__ import annotations

import enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.base_schema import BaseSchema
from app.schemas.constants import PHONE_FORMAT_ERROR_EC, PHONE_PATTERN_EC
from app.schemas.user_schema import PersonBase
from app.utils.exceptions import ValidationException
from app.utils.security import validate_ec_dni


class RelationshipType(str, enum.Enum):
    """Tipo de relación entre representante y atleta menor."""

    FATHER = "FATHER"
    MOTHER = "MOTHER"
    LEGAL_GUARDIAN = "LEGAL_GUARDIAN"


# ==========================================
# REQUEST SCHEMAS (Entradas)


class RepresentativeInscriptionDTO(PersonBase):
    """Datos para registrar un representante."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    dni: str = Field(..., min_length=10, max_length=10, description="DNI (10 dígitos)")
    email: Optional[EmailStr] = Field(
        default=None, description="Email de contacto (opcional)"
    )
    relationship_type: RelationshipType = Field(
        ..., description="Tipo de relación con el atleta"
    )

    @field_validator("dni", mode="before")
    @classmethod
    def _normalize_and_validate_dni(cls, value: Any) -> str:
        try:
            return validate_ec_dni(str(value))
        except ValidationException as exc:
            raise ValueError(exc.message) from exc

    @field_validator("relationship_type", mode="before")
    @classmethod
    def _normalize_relationship(cls, value: Any) -> RelationshipType:
        if value is None:
            raise ValueError("El tipo de relación es requerido")
        if isinstance(value, RelationshipType):
            return value
        raw = str(value).strip().upper().replace(" ", "_")
        mapping = {
            "FATHER": RelationshipType.FATHER,
            "PADRE": RelationshipType.FATHER,
            "MOTHER": RelationshipType.MOTHER,
            "MADRE": RelationshipType.MOTHER,
            "LEGAL_GUARDIAN": RelationshipType.LEGAL_GUARDIAN,
            "TUTOR": RelationshipType.LEGAL_GUARDIAN,
            "TUTOR_LEGAL": RelationshipType.LEGAL_GUARDIAN,
        }
        if raw not in mapping:
            raise ValueError(
                "Tipo de relación inválido. Use: FATHER, MOTHER o LEGAL_GUARDIAN"
            )
        return mapping[raw]


class RepresentativeUpdateDTO(BaseModel):
    """Datos para actualizar un representante."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    first_name: Optional[str] = Field(default=None, min_length=2)
    last_name: Optional[str] = Field(default=None, min_length=2)
    phone: Optional[str] = Field(default=None, description="Teléfono")
    email: Optional[EmailStr] = Field(default=None, description="Email")
    direction: Optional[str] = Field(
        default=None, max_length=200, description="Dirección"
    )
    relationship_type: Optional[RelationshipType] = None

    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone(cls, value: Any) -> Optional[str]:
        """Valida formato de teléfono ecuatoriano (10 dígitos)."""
        if value is None or value == "S/N":
            return value
        v = str(value).strip()
        if v and not PHONE_PATTERN_EC.match(v):
            raise ValueError(PHONE_FORMAT_ERROR_EC)
        return v


class RepresentativeFilter(BaseModel):
    """Filtros para búsqueda/paginación de representantes."""

    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=100)
    search: Optional[str] = Field(None, description="Búsqueda por nombre o DNI")

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.limit


# ==========================================
# INTERNAL SCHEMAS (Para DAO)


class RepresentativeCreateDB(BaseModel):
    """Schema interno: payload listo para RepresentativeDAO.create()."""

    external_person_id: str
    full_name: str
    dni: str
    phone: Optional[str] = None
    email: Optional[str] = None
    relationship_type: Any  # Acepta el enum Relationship

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


# ==========================================
# RESPONSE SCHEMAS (Salidas)


class AthleteBasicInfo(BaseSchema):
    """Info básica de atleta para listas de representantes."""

    id: int
    full_name: str
    dni: str
    is_active: bool


class RepresentativeResponse(BaseSchema):
    """Respuesta básica de representante para listados."""

    id: int
    full_name: str
    dni: str
    phone: Optional[str] = None
    email: Optional[str] = None
    relationship_type: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    direction: Optional[str] = None
    is_active: bool
    athletes_count: int = 0
    athletes: list[AthleteBasicInfo] = []
    created_at: Optional[str] = None


class RepresentativeDetailResponse(BaseSchema):
    """Respuesta detallada de representante con datos del MS."""

    id: int
    external_person_id: str
    full_name: str
    dni: str
    phone: Optional[str] = None
    email: Optional[str] = None
    relationship_type: str
    is_active: bool
    created_at: str
    updated_at: Optional[str] = None
    # Campos del MS de personas
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    direction: Optional[str] = None
    type_identification: Optional[str] = None
    type_stament: Optional[str] = None


class RepresentativeInscriptionResponseDTO(BaseSchema):
    """Respuesta al registrar un representante."""

    representative_id: int
    full_name: str
    dni: str
    relationship_type: str


class RepresentativeBasicInfo(BaseSchema):
    """Info básica del representante para respuestas combinadas."""

    id: int
    full_name: str
    dni: str
    relationship_type: str
